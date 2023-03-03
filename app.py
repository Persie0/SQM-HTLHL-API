import threading
import time
from datetime import datetime, timedelta, date
from pathlib import Path
import os
import json
import flask
from flask import Flask, request, redirect, url_for
from turbo_flask import Turbo
import socket
import webbrowser
import plotly
import plotly.graph_objs as go
import pandas as pd

# Create a Flask application instance
app = Flask(__name__)

# Initialize Turbo
turbo = Turbo(app)

# Initialize variables
last_transm = "No data yet"
min_ago = "Never"
skystate = "Unknown"
isRunning = False
localIP = "error"

# -333 if no data
sensor_values = {
    "raining": "-333",
    "ambient": "-333",
    "object": "-333",
    "lux": "-333",
    "luminosity": "-333",
    "seeing": "-333",
    "lightning_distanceToStorm": "-333",
    "nelm": "-333",
    "concentration": "-333",
    "errors": "-333",
    "isSeeing": "0"
}

# set the default values for the settings
settings = {
    "seeing_thr": 3,
    "SLEEPTIME_s": 180,
    "DISPLAY_TIMEOUT_s": 200,
    "DISPLAY_ON": 1,
    "PATH": "",
    "actual_SQM": -333,
    "actual_SQM_time": date(1, 1, 1).strftime("%d-%b-%Y (%H:%M:%S.%f)"),
    "calculated_mag_limit": -333,
    "set_sqm_limit": 21.83,

    "max_lux": 50.0,
    "setpoint1": 22.0,
    "setpoint2": 2.0,

    # Abbriviations
    "raining": "RQ",
    "luminosity": "SQ",
    "seeing": "SE",
    "nelm": "NE",
    "concentration": "SA",
    "object": "HT",
    "ambient": "TQ",
    "lux": "HL",
    "lightning_distanceToStorm": "BD",

    # sensor enabled
    "en_seeing": 1,
    "en_raining": 1,
    "en_luminosity": 1,
    "en_nelm": 1,
    "en_concentration": 1,
    "en_object": 1,
    "en_ambient": 1,
    "en_lux": 1,
    "en_lightning_distanceToStorm": 1,
}

# whole names of the sensors
vis={
    "raining": "Raining",
    "ambient": "Ambient temperature",
    "object": "Object temperature",
    "lux": "Lux",
    "luminosity": "SQM",
    "seeing": "Seeing",
    "lightning_distanceToStorm": "Lightning distance",
    "nelm": "NELM",
    "concentration": "Air particle concentration",
}

# time diagramm
bar = None
# if the files should be saved in a specified directory (eg "C:/Users")
SPECIFIC_DIRECTORY = Path(settings["PATH"])

# Get all abbreviations from the settings dictionary
def get_all_abriviations():
    # Initialize empty dictionary to store abbreviations
    abriviations = {}

    # Iterate over the items in the settings dictionary
    for key, value in settings.items():
        # If value is a string and 2 characters long, add to abbreviations dictionary
        if isinstance(value, str) and len(value) == 2:
            abriviations[value] = key

    # Return the abbreviations dictionary
    return abriviations

# Get the long name for an abbreviation
def get_long_name(abriviation):
    # Iterate over the items in the settings dictionary
    for key, value in settings.items():
        # If value matches the abbreviation, return the capitalized key
        if value == abriviation:
            return key.capitalize()
    # Return None if abbreviation not found
    return None

# Get the IP address of the current computer
def get_ip():
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Try to connect to 10.254.254.254 (doesn't have to be reachable)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        # If connection fails, set the IP address to 127.0.0.1 (localhost)
        ip = '127.0.0.1'
    finally:
        # Close the socket
        s.close()
    # Return the IP address
    return ip

def dat_to_df(dat_file_full_path):
    # read the .dat file and convert it to a pandas dataframe
    df = pd.read_csv(dat_file_full_path, sep='\t', header=None, names=['time', 'value'])
    # use file name as date
    # get file name from path with pathlib
    f_date = Path(dat_file_full_path).stem[2:8]   # 2:8 because of the "SQ" in the file name
    print(f_date)
    # convert all dataframes to datetime, date is the f_date and time is the time column
    #year = int(f_date[:1]), month = int(f_date[2:3]), day = int(f_date[4:]
    #replace the date with the date from the file name
    df['time'].replace('0000', regex=True).replace("20"+f_date[:1], regex=True)
    # sort the data by time
    df.sort_values(by=['time'], inplace=True)

    # convert the values to float
    df['value'] = df['value'].astype(float)
    return df

# Create a plotly plot from a dataframe
def create_plot(df):
    # Create a scatter plot with the time and value columns from the dataframe
    scatter_plot = go.Scatter(
        x=df['time'],
        y=df['value'],
        mode='lines+markers',
        line=dict(
            width=1
        ),
        marker=dict(
            size=7,
            symbol='circle',
        ),
        connectgaps=False,
    )

    # Package the plot data as a list of dictionaries
    data = [scatter_plot]

    # Serialize the plot data to JSON using the PlotlyJSONEncoder
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    # Return the serialized plot data
    return graphJSON

# calculate cloud state from IR temperature sensor
def get_cloud_state():
    global settings, skystate
    # calculate the difference between the object and ambient temperature
    temp_diff = float(sensor_values["ambient"]) - float(sensor_values["object"])
    # calculate the cloud state
    if temp_diff > settings["setpoint1"]:
        skystate = "Clear"
    elif (temp_diff > settings["setpoint2"]) and (temp_diff < settings["setpoint1"]):
        skystate = "Partly cloudy"
    elif temp_diff < settings["setpoint2"]:
        skystate = "Cloudy"
    else:
        skystate = "Unknown"


# calculates the magnitude limit, for calibration of the SQM-sensor
def calculate_mag_limit():
    global settings
    # look that the calibration SQM-value is ok and not older than 15min
    if datetime.strptime(settings["actual_SQM_time"], "%d-%b-%Y (%H:%M:%S.%f)") > datetime.now() - timedelta(
            minutes=15) and sensor_values["luminosity"] != "-333":
        # calculate the magnitude limit
        settings["calculated_mag_limit"] = round(
            (settings["set_sqm_limit"] - float(sensor_values["luminosity"]) + settings[
                "actual_SQM"]), 2)
        # save settings
        with open("SQM_Settings.json", 'w') as f3:
            json.dump(settings, f3)

# visualize the selected date
@app.route('/shortvisual/<sensor>')
def shortvisual(sensor):
    # get the selected date from the html page
    selected_date = request.args.get('date')
    # format the date to the correct format (the date is in the format dd.mm.yyyy + ".dat")
    formatted_date = sensor + selected_date[2:4] + selected_date[5:7] + selected_date[8:10] + ".dat"
    # redirect to the visualdate function (/visual/<sensor>/<datum>)
    return redirect(url_for('visualdate', sensor=sensor, datum=formatted_date))

# visualize the data 
@app.route('/visual/<sensor>/<datum>')
def visualdate(sensor, datum):
    # format the date to the correct format
    formatted_datum= datum[6:8] + "." + datum[4:6] + "." + "20" + datum[2:4]
    # get all dat files in the directory
    temp_path = str(SPECIFIC_DIRECTORY)+"/"+sensor
    dat_files = os.listdir(temp_path)
    # sort them by date
    dat_files.sort(key=lambda x: os.path.getmtime(temp_path + "/" + x), reverse=True)
    # check if date was passed
    if datum == "newest":
        # if not, redirect to the newest date
        return redirect('/visual/'+sensor+'/'+dat_files[0])
    else:
        # if yes, check if the date is in the list of dates
        if datum in dat_files:
            selected_file = datum
        else:
            return "Date not found"
    # convert the file to a pandas dataframe
    df = dat_to_df(str(SPECIFIC_DIRECTORY)+"/"+sensor+"/"+selected_file)
    # create the plot
    global bar
    bar = create_plot(df)
    #get earliest and latest date
    earliest = dat_files[0]
    latest = dat_files[-1]
    #convert to html date format
    earliest = datetime.strptime(earliest[2:8], "%y%m%d").strftime("%Y-%m-%d")
    latest = datetime.strptime(latest[2:8], "%y%m%d").strftime("%Y-%m-%d")
    # get all dates in html date format
    dates = []
    for i in dat_files:
        dates.append(datetime.strptime(i[2:8], "%y%m%d").strftime("%Y-%m-%d"))
    return flask.render_template('visual.html', sens=vis[get_all_abriviations()[sensor]],
                                 plot=bar, dat_files=dat_files, abr=sensor, min_date=earliest,
                                 max_date=latest, formatted_date=formatted_datum)



# get & process ESP32 sensor data
@app.route('/SQM', methods=['POST'])
def process():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        # is content in json format?
        if content_type == 'application/json':
            # get current datetime
            timestamp = datetime.now()
            jsonfile = request.json
            print(jsonfile)
            # write the current datetime as last measurement datetime
            if not SPECIFIC_DIRECTORY.is_dir():
                SPECIFIC_DIRECTORY.mkdir()
            with open(SPECIFIC_DIRECTORY / "last_measurement.txt", 'w') as f1:
                f1.write(timestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                f1.close()
            # loop through sensor values
            for key in jsonfile.keys():
                # "-333" means no data
                global sensor_values
                if jsonfile[key] == "":
                    continue
                else:
                    sensor_values[key] = jsonfile[key]
                # don't write values if sensor error (-333) and don't write the errors & if Seeing is on
                if key == "errors" or key == "isSeeing":
                    continue
                if float(jsonfile[key]) < -100:
                    continue
                # write the values to the sensor file if enabled
                elif settings["en_"+key] == 1:
                    # create a directory for each sensor and append the values to the sensor file
                    measurement_path = SPECIFIC_DIRECTORY / settings[key]
                    if not measurement_path.is_dir():
                        measurement_path.mkdir()
                    # ASCII encode timestamp + value
                    temp_val = (timestamp.strftime('%H:%M') + "\t" + jsonfile[key] + "\n").encode('ascii')
                    # write to .dat file
                    with open(measurement_path / (settings[key].upper() +
                                                  timestamp.strftime('%Y')[2:4] +
                                                  timestamp.strftime('%m%d') + ".dat"), 'ab') as f1:
                        f1.write(temp_val)
                        f1.close()
            get_cloud_state()
            calculate_mag_limit()
            return ""


# Homepage with status and current settings
@app.route('/', methods=["GET"])
def statuspage():
    return flask.render_template('index.html', stats=url_for('static', filename='statistics.svg'))

#ESP32 turn the sensors on/off
@app.route('/onoff', methods=["POST"])
def onoffpage():
    # sensors even enabled?, get the transmitted data from the index.html
    # get JSON.stringify({ en_seeing: status });
    if "en_seeing" in request.json and request.json["en_seeing"] is not None:
        settings["en_seeing"] = request.json["en_seeing"]

    if "en_lux" in request.json and request.json["en_lux"] is not None:
        settings["en_lux"] = request.json["en_lux"]

    if "en_luminosity" in request.json and request.json["en_luminosity"] is not None:
        settings["en_luminosity"] = request.json["en_luminosity"]

    if "en_lux" in request.json and request.json["en_lux"] is not None:
        settings["en_lux"] = request.json["en_lux"]

    if "en_nelm" in request.json and request.json["en_nelm"] is not None:
        settings["en_nelm"] = request.json["en_nelm"]

    if "en_concentration" in request.json and request.json["en_concentration"] is not None:
        settings["en_concentration"] = request.json["en_concentration"]

    if "en_ambient" in request.json and request.json["en_ambient"] is not None:
        settings["en_ambient"] = request.json["en_ambient"]

    if "en_object" in request.json and request.json["en_object"] is not None:
        settings["en_object"] = request.json["en_object"]

    if "en_lightning_distanceToStorm" in request.json and request.json["en_lightning_distanceToStorm"] is not None:
        settings["en_lightning_distanceToStorm"] = request.json["en_lightning_distanceToStorm"]

    if "en_raining" in request.json and request.json["en_raining"] is not None:
        settings["en_raining"] = request.json["en_raining"]

    # save settings
    with open("SQM_Settings.json", 'w') as f3:
        json.dump(settings, f3)

    return ""

# ESP32 settings page
@app.route('/settings', methods=["GET", "POST"])
def settingspage():
    # if sending/saving settings
    if request.method == "POST":
        global settings, SPECIFIC_DIRECTORY

        # getting the input from the settings page
        # check if value x was entered
        seeing_thr = request.form.get("seeing_thr", type=int)
        if seeing_thr is not None:
            settings["seeing_thr"] = seeing_thr
        if request.form.get("DISPLAY") is not None:
            settings["DISPLAY_ON"] = 1
        else:
            settings["DISPLAY_ON"] = 0
        setpoint1 = request.form.get("setpoint1", type=float)
        if setpoint1 is not None:
            settings["setpoint1"] = setpoint1
        setpoint2 = request.form.get("setpoint2", type=float)
        if setpoint2 is not None:
            settings["setpoint2"] = setpoint2
        max_lux = request.form.get("max_lux", type=float)
        if max_lux is not None:
            settings["max_lux"] = max_lux
        dto = request.form.get("DISPLAY_TIMEOUT_s", type=int)
        if dto is not None:
            settings["DISPLAY_TIMEOUT_s"] = dto
        sleep_t = request.form.get("SLEEPTIME_s", type=int)
        if sleep_t is not None:
            settings["SLEEPTIME_s"] = sleep_t
        path = request.form.get("PATH", type=str)
        if path is not None:
            settings["PATH"] = path
            SPECIFIC_DIRECTORY = Path(settings["PATH"])
        set_sqm_limit = request.form.get("set_sqm_limit", type=float)
        if set_sqm_limit is not None:
            settings["set_sqm_limit"] = set_sqm_limit

        # save settings
        with open("SQM_Settings.json", 'w') as f3:
            json.dump(settings, f3)
        # route to status page
        return redirect(url_for('statuspage'))
    # else show settings page
    return flask.render_template('settings.html')


# abbreviation settings page
@app.route('/abriv', methods=["GET", "POST"])
def abrivpage():
    # if sending/saving settings
    if request.method == "POST":
        global settings, SPECIFIC_DIRECTORY
        # getting the input from the html forms
        abr_dictionary = request.form.to_dict()
        # loop through input fields
        for abr_key in abr_dictionary.keys():
            abr_value = abr_dictionary[abr_key]
            # if form field is not empty
            if abr_value != "":
                settings[abr_key.replace("abr_", "")] = abr_value
        # save settings
        with open("SQM_Settings.json", 'w') as f3:
            json.dump(settings, f3)
        # route to status page
        return redirect(url_for('statuspage'))
    # else show settings page
    return flask.render_template('abriv_settings.html')


# SQM-sensor calibration
@app.route('/calibrate', methods=["POST"])
def calibrate():
    if request.method == "POST":
        global settings
        # getting the input from the html forms
        actual_SQM = request.form.get("actual_SQM", type=float)
        # if form field is not empty
        if actual_SQM is not None:
            settings["actual_SQM"] = actual_SQM
            settings["actual_SQM_time"] = datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
            calculate_mag_limit()
        return redirect(url_for('statuspage'))


# turbo-flask, update website every 5 sec
def update_load():
    with app.app_context():
        while True:
            # if a measurement exists, read time and date and calculate the time difference to now, show if (not) running
            if (SPECIFIC_DIRECTORY / "last_measurement.txt").is_file():
                with open(SPECIFIC_DIRECTORY / "last_measurement.txt", 'r') as f4:
                    # read last measurement time
                    loaded_time = datetime.strptime(f4.read(), "%d-%b-%Y (%H:%M:%S.%f)")
                    now = datetime.now()
                    # calculate time difference between now and last measurement
                    difference = (now - loaded_time)
                    # calculate time difference in seconds
                    duration_in_s = difference.total_seconds()
                    # calculate time difference in days, hours, minutes and seconds
                    days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
                    hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
                    minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
                    seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
                    global last_transm, min_ago, isRunning
                    # if last measurement is older than SLEEPTIME_s + 10 seconds, show "not running"
                    if duration_in_s > (settings["SLEEPTIME_s"] + 10):
                        isRunning = False
                        sensor_values["isSeeing"] = False
                    # else show "running"
                    else:
                        isRunning = True
                    last_transm = loaded_time.strftime("%d %b %Y %H:%M:%S")
                    min_ago = "%d days, %d hours, %d minutes and %d seconds ago" % (
                        days[0], hours[0], minutes[0], seconds[0])
            turbo.push(turbo.replace(flask.render_template('replace_content.html', stats="static/statistics.svg"), 'load'))
            time.sleep(5)


# inject settings/sensor values into the website
@app.context_processor
def inject_load():
    global last_transm, min_ago, isRunning
    return {'last_transm': last_transm,
            'min_ago': min_ago,
            "isRunning": isRunning,
            "isSeeing": int(sensor_values["isSeeing"]),
            "raining": int(sensor_values["raining"]),
            "ambient": float(sensor_values["ambient"]),
            "object": float(sensor_values["object"]),
            "lux": float(sensor_values["lux"]),
            "luminosity": float(sensor_values["luminosity"]),
            "seeing": float(sensor_values["seeing"]),
            "lightning_distanceToStorm": int(sensor_values["lightning_distanceToStorm"]),
            "nelm": float(sensor_values["nelm"]),
            "concentration": int(sensor_values["concentration"]),

            "errors": sensor_values["errors"].strip()[:-1],

            "SLEEPTIME_s": settings["SLEEPTIME_s"],
            "DISPLAY_TIMEOUT_s": settings["DISPLAY_TIMEOUT_s"],
            "DISPLAY_ON": settings["DISPLAY_ON"],
            "PATH": settings["PATH"],
            "skystate": skystate,
            "localIP": localIP,
            "calculated_mag_limit": settings["calculated_mag_limit"],
            "set_sqm_limit": settings["set_sqm_limit"],
            "seeing_thr": settings["seeing_thr"],

            "max_lux": settings["max_lux"],
            "setpoint1": settings["setpoint1"],
            "setpoint2": settings["setpoint2"],

            "abr_seeing": settings["seeing"],
            "abr_raining": settings["raining"],
            "abr_luminosity": settings["luminosity"],
            "abr_nelm": settings["nelm"],
            "abr_concentration": settings["concentration"],
            "abr_object": settings["object"],
            "abr_ambient": settings["ambient"],
            "abr_lux": settings["lux"],
            "abr_lightning_distanceToStorm": settings["lightning_distanceToStorm"],

            "en_seeing": settings["en_seeing"],
            "en_raining": settings["en_raining"],
            "en_luminosity": settings["en_luminosity"],
            "en_nelm": settings["en_nelm"],
            "en_concentration": settings["en_concentration"],
            "en_object": settings["en_object"],
            "en_ambient": settings["en_ambient"],
            "en_lux": settings["en_lux"],
            "en_lightning_distanceToStorm": settings["en_lightning_distanceToStorm"],

            "plot": bar,
            }


# send settings to ESP32 as json response
@app.route('/getsettings')
def sendsettings():
    return settings


if __name__ == '__main__':
    # start thread to update website with  current values, runs parallel to Flask app
    threading.Thread(target=update_load).start()
    # create / read settings file
    if not Path("SQM_Settings.json").is_file():
        with open("SQM_Settings.json", 'w') as f:
            json.dump(settings, f)
    else:
        with open("SQM_Settings.json", 'r') as file:
            settings = json.load(file)
            SPECIFIC_DIRECTORY = Path(settings["PATH"])
    # get ip of this server/PC
    localIP = get_ip()
    # open IP in browser
    webbrowser.open("http://" + str(localIP) + ":5000")
    # run Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)