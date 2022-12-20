import threading
import time
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import flask
from flask import Flask, request, redirect, url_for
from turbo_flask import Turbo
import socket
import webbrowser

app = Flask(__name__)
turbo = Turbo(app)

last_transm = "No data yet"
min_ago = "Never"
skystate = "Unknown"
isRunning = False
localIP = "error"

# -1 if no data
sensor_values = {
    "raining": "-1",
    "ambient": "-1",
    "object": "-1",
    "lux": "-1",
    "luminosity": "-1",
    "seeing": "-1",
    "lightning_distanceToStorm": "-1",
    "nelm": "-1",
    "concentration": "-1",
    "errors": "-1",
    "isSeeing": "0"
}

settings = {
    "seeing_thr": 3,
    "SLEEPTIME_s": 180,
    "DISPLAY_TIMEOUT_s": 200,
    "DISPLAY_ON": 1,
    "PATH": "",
    "actual_SQM": -1,
    "actual_SQM_time": date(1, 1, 1).strftime("%d-%b-%Y (%H:%M:%S.%f)"),
    "calculated_mag_limit": -1,
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
}

# if the files should be saved in a specified directory (eg "C:/Users")
SPECIFIC_DIRECTORY = Path(settings["PATH"])


# get this PCs IP-Adress
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# calculate cloud state from IR temperature sensor
def get_cloud_state():
    global settings, skystate
    temp_diff = float(sensor_values["ambient"]) - float(sensor_values["object"])
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
            minutes=15) and sensor_values["luminosity"] != "-1":
        settings["calculated_mag_limit"] = round(
            (settings["set_sqm_limit"] - float(sensor_values["luminosity"]) + settings[
                "actual_SQM"]), 2)
        # save settings
        with open("SQM_Settings.json", 'w') as f3:
            json.dump(settings, f3)


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
            # write the current datetime as last measurement datetime
            if not SPECIFIC_DIRECTORY.is_dir():
                SPECIFIC_DIRECTORY.mkdir()
            with open(SPECIFIC_DIRECTORY / "last_measurement.txt", 'w') as f1:
                f1.write(timestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                f1.close()
            # loop through sensor values
            print(jsonfile)
            for key in jsonfile.keys():
                # "-1" means no data
                global sensor_values
                sensor_values[key] = jsonfile[key]
                # don't write values if sensor error (-1) and don't write the errors & if Seeing is on
                if jsonfile[key] == "-1" or key == "errors" or key == "isSeeing":
                    continue
                else:
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
    return flask.render_template('index.html')


# ESP32 settings page
@app.route('/settings', methods=["GET", "POST"])
def settingspage():
    # if sending/saving settings
    if request.method == "POST":
        global settings, SPECIFIC_DIRECTORY
        # getting the input from the html form
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
        actual_SQM = request.form.get("actual_SQM", type=float)
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
                    loaded_time = datetime.strptime(f4.read(), "%d-%b-%Y (%H:%M:%S.%f)")
                    now = datetime.now()
                    difference = (now - loaded_time)
                    duration_in_s = difference.total_seconds()
                    days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
                    hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
                    minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
                    seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
                    global last_transm, min_ago, isRunning
                    if duration_in_s > (settings["SLEEPTIME_s"] + 10):
                        isRunning = False
                    else:
                        isRunning = True
                    last_transm = loaded_time.strftime("%d %b %Y %H:%M:%S")
                    min_ago = "%d days, %d hours, %d minutes and %d seconds ago" % (
                        days[0], hours[0], minutes[0], seconds[0])
            turbo.push(turbo.replace(flask.render_template('replace_content.html'), 'load'))
            time.sleep(5)


# inject settings/sensor values into the website
@app.context_processor
def inject_load():
    global last_transm, min_ago, isRunning
    return {'last_transm': last_transm,
            'min_ago': min_ago,
            "isRunning": isRunning,
            "isSeeing": sensor_values["isSeeing"],
            "raining": sensor_values["raining"],
            "ambient": sensor_values["ambient"],
            "object": sensor_values["object"],
            "lux": sensor_values["lux"],
            "luminosity": sensor_values["luminosity"],
            "seeing": sensor_values["seeing"],
            "lightning_distanceToStorm": sensor_values["lightning_distanceToStorm"],
            "nelm": sensor_values["nelm"],
            "concentration": sensor_values["concentration"],

            "errors": sensor_values["errors"],

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
            }


# send settings to ESP32 as json response
@app.route('/getsettings')
def sendsettings():
    return settings


if __name__ == '__main__':
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
