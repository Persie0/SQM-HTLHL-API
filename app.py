import threading
import time
from datetime import datetime
from pathlib import Path
import json
import flask
from flask import Flask, request, redirect, url_for
from turbo_flask import Turbo

app = Flask(__name__)
turbo = Turbo(app)


running = ""
last_transm = ""
min_ago = ""
skystate = "Unknown"
isRunning = False
sensor_values = {
    "raining": -1,
    "ambient": -1,
    "object": -1,
    "lux": -1,
    "SQMreading": -1,
    "irradiance": -1,
    "lightning_distanceToStorm": -1,
    "nelm": -1,
    "concentration": -1,
}
settings = {
    "SLEEPTIME_s": 180,
    "DISPLAY_TIMEOUT_s": 200,
    "DISPLAY_ON": 1,
    "PATH": "",
}

# if the files should be saved in a specified directory (eg "C:/Users")
# else leave it as "" - and it saves it in the same as the script gets run
SPECIFIC_DIRECTORY = Path(settings["PATH"])

def get_cloud_state():
    global skystate
    temp_diff = sensor_values["ambient"] - sensor_values["object"]
    if temp_diff > 22:
        skystate = "Clear"
    elif (temp_diff > 2) and (temp_diff < 22):
        skystate = "Partly cloudy"
    elif temp_diff < 2:
        skystate = "Cloudy"
    else:
        skystate = "Unknown"


@app.route('/SQM', methods=['POST'])
def process():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        # is content in json format?
        if content_type == 'application/json':
            # get current datetime
            timestamp = datetime.now()
            jsonfile = request.json
            # write the current datetime as alst measurement datetime
            with open(SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt", 'w') as f1:
                f1.write(timestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                f1.close()
            for key in jsonfile.keys():
                # -1 means no data
                global sensor_values
                sensor_values[key] = jsonfile[key]
                if jsonfile[key] == "-1":
                    continue
                else:
                    # create a directory for each sensor and write append the values to the current file
                    measurement_path = SPECIFIC_DIRECTORY / "SQM" / key
                    if not measurement_path.is_dir():
                        measurement_path.mkdir()
                    temp_val = (timestamp.strftime('%H:%M') + "\t" + jsonfile[key] + "\n").encode('ascii')
                    with open(measurement_path / (key[0:2].upper() +
                                                  timestamp.strftime('%Y')[2:4] +
                                                  timestamp.strftime('%m%d') + ".dat"), 'ab') as f1:
                        f1.write(temp_val)
            f1.close()
            get_cloud_state()
            return ""


#Homepage with status and current settings
@app.route('/', methods=["GET", "POST"])
def statuspage():
    # show when the last measurement was as a website
    if request.method == "POST":
        return redirect(url_for('settingspage'))
    if (SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt").is_file():
        with open(SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt", 'r') as f2:
            loaded_time = datetime.strptime(f2.read(), "%d-%b-%Y (%H:%M:%S.%f)")
            now = datetime.now()
            difference = (now - loaded_time)
            duration_in_s = difference.total_seconds()
            days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
            hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
            minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
            seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
            global running, last_transm, min_ago, isRunning
            if duration_in_s > (settings["SLEEPTIME_s"] + 10):
                isRunning = False
                running = "SQM NOT running"
            else:
                isRunning = True
                running = "SQM Running"
            last_transm = loaded_time.strftime("%d %b %Y %H:%M:%S")
            min_ago = "%d days, %d hours, %d minutes and %d seconds ago" % (
                days[0], hours[0], minutes[0], seconds[0])
            return flask.render_template('index.html', running=running, last_transm=last_transm, min_ago=min_ago)
    return flask.render_template('index.html', running="SQM files not available", last_transm="", min_ago="")

#settings page
@app.route('/settings', methods=["GET", "POST"])
def settingspage():
    if request.method == "POST":
        global settings, SPECIFIC_DIRECTORY
        # getting inputs from html form
        disp = request.form.get("DISPLAY", type=int)
        if disp is not None:
            settings["DISPLAY_ON"] = disp
        disp_to = request.form.get("DISPLAY_TIMEOUT_s", type=int)
        if disp_to is not None:
            settings["DISPLAY_TIMEOUT_s"] = disp_to
        sleep_t = request.form.get("SLEEPTIME_s", type=int)
        if sleep_t is not None:
            settings["SLEEPTIME_s"] = sleep_t
        path = request.form.get("PATH", type=str)
        if path is not None:
            settings["PATH"] = path
            SPECIFIC_DIRECTORY = Path(settings["PATH"])
        if not (SPECIFIC_DIRECTORY / "SQM").is_dir():
            (SPECIFIC_DIRECTORY / "SQM").mkdir()
        with open(SPECIFIC_DIRECTORY / "SQM" / "settings.json", 'w') as f3:
            json.dump(settings, f3)
        return redirect(url_for('statuspage'))
    return flask.render_template('settings.html')

# turbo-flask update status website every 5 sec
def update_load():
    with app.app_context():
        while True:
            time.sleep(5)
            if (SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt").is_file():
                with open(SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt", 'r') as f4:
                    loaded_time = datetime.strptime(f4.read(), "%d-%b-%Y (%H:%M:%S.%f)")
                    now = datetime.now()
                    difference = (now - loaded_time)
                    duration_in_s = difference.total_seconds()
                    days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
                    hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
                    minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
                    seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
                    global running, last_transm, min_ago, isRunning
                    if duration_in_s > (settings["SLEEPTIME_s"] + 10):
                        running = "SQM NOT running"
                        isRunning = False
                    else:
                        running = "SQM Running"
                        isRunning = True
                    last_transm = loaded_time.strftime("%d %b %Y %H:%M:%S")
                    min_ago = "%d days, %d hours, %d minutes and %d seconds ago" % (
                        days[0], hours[0], minutes[0], seconds[0])
            turbo.push(turbo.replace(flask.render_template('index.html'), 'load'))


@app.before_first_request
def before_first_request():
    threading.Thread(target=update_load).start()


#inject settings/sensor values in website
@app.context_processor
def inject_load():
    global running, last_transm, min_ago, isRunning
    return {'running': running, 'last_transm': last_transm, 'min_ago': min_ago, "isRunning": isRunning,
            "raining": sensor_values["raining"],
            "ambient": sensor_values["ambient"],
            "object": sensor_values["object"],
            "lux": sensor_values["lux"],
            "SQMreading": sensor_values["SQMreading"],
            "irradiance": sensor_values["irradiance"],
            "lightning_distanceToStorm": sensor_values["lightning_distanceToStorm"],
            "nelm": sensor_values["nelm"],
            "concentration": sensor_values["concentration"],

            "SLEEPTIME_s": settings["SLEEPTIME_s"],
            "DISPLAY_TIMEOUT_s": settings["DISPLAY_TIMEOUT_s"],
            "DISPLAY_ON": settings["DISPLAY_ON"],
            "PATH": settings["PATH"],
            "skystate": skystate,
            }

#send settings to ESP32 as json
@app.route('/getsettings')
def sendsettings():
    with open(SPECIFIC_DIRECTORY / "SQM" / "settings.json", 'r') as f5:
        global settings
        settings = json.load(f5)
        return settings


if __name__ == '__main__':
    if not (SPECIFIC_DIRECTORY / "SQM").is_dir():
        (SPECIFIC_DIRECTORY / "SQM").mkdir()
    if not (SPECIFIC_DIRECTORY / "SQM" / "settings.json").is_file():
        with open(SPECIFIC_DIRECTORY / "SQM" / "settings.json", 'w') as f:
            json.dump(settings, f)
    else:
        with open(SPECIFIC_DIRECTORY / "SQM" / "settings.json", 'r') as file:
            settings = json.load(file)
    app.run(host='0.0.0.0', port=5000, threaded=True)
