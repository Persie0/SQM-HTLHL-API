# Download .exe
no console: (runs in background):

https://github.com/Persie0/SQM-HTLHL-API/raw/master/SQM_API.exe

v2:

https://github.com/Persie0/SQM-HTLHL-API/raw/master/release_v2.exe
# create .exe
`pip install pyinstaller`

without console Windows

`pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" app.py`


Linux (NOT TESTED):

`pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" app.py`
