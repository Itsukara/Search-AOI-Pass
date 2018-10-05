import ephem
from pyorbital import orbital
import datetime
from math import asin, cos

# Program to search Satellite Pass for AOI with limited Off-Nadir

# Parameters
R = 6378.1  # Earth Radius

# Utility functions


def deg(radians):
    return radians / ephem.degree


def jday2datetime(jday):
    (year, month, day, hour, minute, second) = ephem.Date(jday).tuple()
    sec = int(second)
    micro = int((second - sec) * 1e6 + 0.5)
    return datetime.datetime(year, month, day, hour, minute, sec, micro)


def jday2dateStr(jday):
    (year, month, day, _, _, _) = ephem.Date(jday).tuple()
    return "%04d-%02d-%02d" % (year, month, day)


def jday2timeStr(jday):
    (_, _, _, hour, minute, second) = ephem.Date(jday).tuple()
    return "%02d:%02d:%04.1f" % (hour, minute, second)

# Class for AOI


class AOI(ephem.Observer):
    def __init__(self, lat, lon, name):
        self.name = name
        self.lat = str(ephem.degrees(lat))
        self.lon = str(ephem.degrees(lon))
        self.elevation = 0
        self.horizon = "00:00:00"

    def __str__(self):
        s = self
        line = "[AOI] name=%s, lat=%.6f (%s), lon=%.6f (%s)" % (
            s.name, deg(s.lat), s.lat, deg(s.lon), s.lon)
        return line

# Class for sat Information


class SatInfo:
    def __init__(self, tle, orbitOffset):
        self.tle = tle
        self.orbitOffset = orbitOffset
        (name, line1, line2) = tle.split("\n")[0:3]
        name = name.strip()
        line1 = line1.strip()
        line2 = line2.strip()
        self.name = name
        self.line1 = line1
        self.line2 = line2
        yyyy = "20" + line1[18:20]
        yday = line1[20:32]
        self.epoch = ephem.Date(ephem.Date(yyyy + "/1/1") + float(yday) - 1.0)
        # ephem satellite
        self.sat = ephem.readtle(name, line1, line2)
        # pyorbital satellite (to get orbit number)
        self.osat = orbital.Orbital(name, line1=line1, line2=line2)

    def __str__(self):
        s = self
        line = "[TLE] name=%s, epoch=%s, orbitOffset=%s" % (
            s.name, s.epoch, s.orbitOffset)
        return line

# Class for Pass


class Pass:
    def __init__(self, sat, aoi, orbit, offNadir):
        self.satName = sat.name
        self.aoiName = aoi.name
        self.orbit = orbit
        self.date = jday2dateStr(aoi.date)
        self.time = jday2timeStr(aoi.date)
        self.lat = sat.sublat
        self.lon = sat.sublong
        self.height = sat.elevation / 1000
        self.az = deg(sat.az)
        self.alt = deg(sat.alt)
        self.distance = sat.range / 1000
        self.offNadir = deg(offNadir)

    def csv(self):
        s = self
        r = "'%s','%s','%d','%s','%s','%s(+N)','%s(+E)','%.1f[Km]','%.1f[deg]','%.1f[deg]','%.1f[Km]','%.1f[deg]'" % \
            (s.satName, s.aoiName, s.orbit, s.date, s.time, s.lat, s.lon,
             s.height, s.az, s.alt, s.distance, s.offNadir)
        return r

# Set Observer of sat


def searchPass(aoi, satInfo, startdate, enddate, maxOffNadir):
    sat = satInfo.sat
    osat = satInfo.osat
    orbitOffset = satInfo.orbitOffset

    aoi.date = startdate
    sat.compute(aoi)
    passes = []
    i = 0
    while True:
        (_, _, mat, _, st, _) = aoi.next_pass(sat)
        if mat > enddate:
            break

        # Move sat to Max Alt Time
        aoi.date = mat
        sat.compute(aoi)

        # Compute off-nadir angle
        alt = sat.alt
        h = sat.elevation / 1000
        offNadir = ephem.degrees(asin(R/(R+h) * cos(alt)))
        eclipsed = sat.eclipsed
        if offNadir < maxOffNadir and not eclipsed:
            i = i + 1
            orbit = osat.get_orbit_number(jday2datetime(mat)) + orbitOffset
            apass = Pass(sat, aoi, orbit, offNadir)
            passes.append(apass)

        # Move sat to end of pass + 1 sec.
        aoi.date = st + ephem.second
        sat.compute(aoi)

    return passes


if __name__ == "__main__":
    import os
    import re
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Search Pass for AOI')
    parser.add_argument("--tleset-url",
                        default="https://www.celestrak.com/NORAD/elements/resource.txt",
                        help="URL of TLE set")
    parser.add_argument("--tleset-file",
                        default="input/resource.txt",
                        help="Filename of TLE set")
    parser.add_argument("--tleset-update-interval", type=int,
                        default=12,
                        help="Update interval (hours) of TLE set")
    parser.add_argument("--aoi-file",
                        default="input/AOI.txt",
                        help="Name of file including AOIs")
    parser.add_argument("--satellite-json",
                        default="input/SATELLITE.json",
                        help="JSON file of target satellite")
    parser.add_argument("--max-offnadir",
                        default="45.0",
                        help="Max Off-Nadir of satellite for AOI")
    parser.add_argument("--start-date",
                        default="",
                        help="Start day to search pass")
    parser.add_argument("--days", type=int,
                        default=7,
                        help="Days (period) to Search pass")
    parser.add_argument("--template-html",
                        default="input/AOI-Pass-Template.html",
                        help="Template html file")
    parser.add_argument("--placeholder-string",
                        default="{{ AOI_PASS_DATA }}",
                        help="Placeholder string in template html file")
    parser.add_argument("--output-html",
                        default="output/AOI-Pass.html",
                        help="Output html file")

    args = parser.parse_args()

    # Prepare TLEset
    TLEsetURL = args.tleset_url
    TLEsetFile = args.tleset_file
    UpdateInterval = args.tleset_update_interval

    needUpdate = False
    if not os.path.exists(TLEsetFile):
        needUpdate = True
    else:
        mtime = datetime.datetime.fromtimestamp(os.stat(TLEsetFile).st_mtime)
        if datetime.datetime.now() - mtime > datetime.timedelta(hours=UpdateInterval):
            needUpdate = True
    if needUpdate:
        import urllib.request
        urllib.request.urlretrieve(TLEsetURL, TLEsetFile)

    # Prepare TLEandOffNadirs
    with open(args.satellite_json, "r") as f:
        satellite_dict = json.loads(f.read())
        SATELLITES = satellite_dict["satellites"]
        SATELLITE_MAP = satellite_dict["satellite_map"]
        ORBITOFFSET_MAP = satellite_dict["orbitoffset_map"]

    with open(TLEsetFile) as f:
        TLEsetStr = f.read()
        TLEset = TLEsetStr.split("\n")
    TLEandOffset = []
    for (i, line) in enumerate(TLEset):
        for satellite in SATELLITES:
            if satellite in line:
                name = SATELLITE_MAP[satellite]
                line1 = TLEset[i+1].strip()
                line2 = TLEset[i+2].strip()
                tle = name + "\n" + line1 + "\n" + line2
                offset = ORBITOFFSET_MAP[name]
                TLEandOffset.append({"tle": tle, "offset": offset})

    # Prepare AOIs
    AOIFile = args.aoi_file
    if not os.path.exists(AOIFile):
        print("[ERROR] AOI file not found: %s" % (AOIFile))
        exit()
    with open(AOIFile) as f:
        AOIsStr = f.read()
        AOIsLines = AOIsStr.split("\n")
    AOIs = []
    error_occured = False
    for line in AOIsLines:
        line = line.strip()
        if line == "":
            continue
        aoi = re.split("\s*,\s*", line)
        try:
            lat = float(aoi[0])
            lon = float(aoi[1])
            if len(aoi) < 3 or lat < -90 or lat > 90 or lon < -180 or lon > 180:
                print("[ERROR] Invalid lat,lon: %s" % (line))
                error_occured = True
        except:
            print("[ERROR] Invalid lat,lon: %s" % (line))
            error_occured = True
        AOIs.append(aoi)
    if error_occured:
        print("[ERROR] Exit by Error in AOI file: %s" % (AOIFile))
        exit()

    # Search Passes
    MaxOffNadir = args.max_offnadir  # Upper Limit of off-nadir angle
    maxOffNadir = ephem.degrees(MaxOffNadir)
    MaxDays = args.days

    if args.start_date:
        start = ephem.Date(args.start_date)
    else:
        start = ephem.now()
    (yyyy, mm, dd, _, _, _) = start.tuple()
    startdate = ephem.Date("%04d-%02d-%02d 00:00:00" % (yyyy, mm, dd))
    end = startdate + (MaxDays - 1)
    (yyyy, mm, dd, _, _, _) = ephem.Date(end).tuple()
    enddate = ephem.Date("%04d-%02d-%02d 23:59:59" % (yyyy, mm, dd))

    allPasses = []
    for tleandoffset in TLEandOffset:
        satInfo = SatInfo(tleandoffset["tle"], tleandoffset["offset"])
        for (lat, lon, name) in AOIs:
            aoi = AOI(lat, lon, name)
            passes = searchPass(aoi, satInfo, startdate, enddate, maxOffNadir)
            allPasses += passes

    # output
#    sortedPasses = sorted(allPasses, key=lambda p: [p.satName, p.date])
    sortedPasses = sorted(allPasses, key=lambda p: [p.date, p.time])
    passesList = []
    for apass in sortedPasses:
        passesList.append("[" + apass.csv() + "]")
    aoi_pass_data = ",\n".join(passesList)

    TemplateFileName = args.template_html
    PlaceholderStr = args.placeholder_string
    OutputFileName = args.output_html
    with open(TemplateFileName, "r") as f_in:
        with open(OutputFileName, "w") as f_out:
            html_in = f_in.read()
            html_out = html_in.replace(PlaceholderStr, aoi_pass_data)
            f_out.write(html_out)
