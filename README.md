# Download .exe
no console:
https://github.com/Persie0/SQM-HTLHL-API/raw/master/SQM_API.exe

console:
https://github.com/Persie0/SQM-HTLHL-API/raw/master/SQM_API_CL.exe

# create .exe
`pip install pyinstaller`

without console

`pyinstaller -w -F --add-data "templates;templates" --onefile .\app.py`

with console

`pyinstaller --add-data "templates;templates" --onefile .\app.py`

or

 nuitka --onefile .\app.py

