# Search-AOI-Pass
Program to search Satellite Pass for AOI with limited Off-Nadir

# Usage
```python Search-AOI-Pass.py```

# Requirements
```pip install -r requirements.txt```

You may need "Build Tools for Visual Studio 2017" to install pyorbital in requirements.txt.  
See https://visualstudio.microsoft.com/downloads/

# Input files
- input/AOI.txt
  - list of AOI (latitude, longitude, name)
- input/SATELLITE.json
  - json file of target satellite
      - ["satellites"]: list of target satellite
      - ["satellite_map"]: mapping from formal name of satellite to its abbreviation
      - ["orbitoffset_map"]: offset of orbit number from pyorbital's orbit number
- input/AOI-Pass-Template.html
  - template of output html file (don't have to change)

# Output file
- output/AOI-Pass.html
  - output satellite passes for AOIs
  - formatted and made searchable by jquery plugins:
    - datatables: https://datatables.net/
      - pre-installed at folder "output/DataTables"
    - yadcf: https://github.com/vedmack/yadcf
      - pre-installed at folder "output/yadcf"

# Options
<pre>
usage: Search-AOI-Pass.py [-h] [--tleset-url TLESET_URL]
                          [--tleset-file TLESET_FILE]
                          [--tleset-update-interval TLESET_UPDATE_INTERVAL]
                          [--aoi-file AOI_FILE]
                          [--satellite-json SATELLITE_JSON]
                          [--max-offnadir MAX_OFFNADIR]
                          [--start-date START_DATE] [--days DAYS]
                          [--template-html TEMPLATE_HTML]
                          [--placeholder-string PLACEHOLDER_STRING]
                          [--output-html OUTPUT_HTML]

Search Pass for AOI

optional arguments:
  -h, --help            show this help message and exit
  --tleset-url TLESET_URL
                        URL of TLE set
  --tleset-file TLESET_FILE
                        Filename of TLE set
  --tleset-update-interval TLESET_UPDATE_INTERVAL
                        Update interval (hours) of TLE set
  --aoi-file AOI_FILE   
                        Name of file including AOIs
  --satellite-json SATELLITE_JSON
                        JSON file of target satellite
  --max-offnadir MAX_OFFNADIR
                        Max Off-Nadir of satellite for AOI
  --start-date START_DATE
                        Start day to search pass
  --days DAYS           
                        Days (period) to Search pass
  --template-html TEMPLATE_HTML
                        Template html file
  --placeholder-string PLACEHOLDER_STRING
                        Placeholder string in template html file
  --output-html OUTPUT_HTML
                        Output html file
</pre>
