# Download .exe
no console: (runs in background):

https://github.com/Persie0/SQM-HTLHL-API/raw/master/dist/app.exe


# create .exe
`pip install pyinstaller`

without console Windows

`pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" --clean app.py `


Linux (NOT TESTED):

`pyinstaller -w -F --add-data "templates:templates" --add-data "static:static" app.py`
