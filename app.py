import threading
import time
from datetime import datetime
from pathlib import Path
import json
import flask
from flask import Flask, url_for, render_template, redirect
from turbo_flask import Turbo
import webbrowser
import data_and_settings as settings
from my_functions import general_utils
from my_routes.routes_visualize import vis_bp
from my_routes.routes_esp32 import esp32_bp
from my_routes.routes_settings import set_bp

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = b'key_blabla'
# register blueprints (routes)
app.register_blueprint(vis_bp)
app.register_blueprint(esp32_bp)
app.register_blueprint(set_bp)

# Initialize Turbo-Flask with the Flask app instance
turbo = Turbo(app)

# if the files should be saved in a specified directory (eg "C:/Users")
settings.SPECIFIC_DIRECTORY = Path(settings.SETTINGS["PATH"])

# Homepage with status and current settings
@app.route('/', methods=["GET"])
def statuspage():
    return render_template('index.html', stats=url_for('static', filename='statistics.svg'))

#error screen with info
@app.route('/error/<er>')
def error(er):
    return render_template('error.html', error_message=er)

#redirect to error screen
@app.errorhandler(404)
def page_not_found(error):
    return redirect("/error/url not found")
    

# turbo-flask, update website every 5 sec
def update_load():
    with app.app_context():
        while True:
            # if a measurement exists, read time and date and calculate the time difference to now, show if (not) running
            if (settings.SPECIFIC_DIRECTORY / "last_measurement.txt").is_file():
                with open(settings.SPECIFIC_DIRECTORY / "last_measurement.txt", 'r') as f4:
                    # read last measurement time
                    loaded_time = datetime.strptime(f4.read(), "%d-%b-%Y (%H:%M:%S.%f)")
                    general_utils.calculate_time_dif(loaded_time)
            turbo.push(turbo.replace(render_template('replace_content.html', stats="static/statistics.svg"), 'load'))
            time.sleep(5)


# inject settings/sensor values into the website
@app.context_processor
def inject_load():
    return {'last_transm': settings.LAST_TRANSMISSION,
            'min_ago': settings.MINUTES_AGO,
            "isRunning": settings.IS_RUNNING,
            "isSeeing": int(settings.SENSOR_VALUES["isSeeing"]),
            "raining": int(settings.SENSOR_VALUES["raining"]),
            "ambient": float(settings.SENSOR_VALUES["ambient"]),
            "object": float(settings.SENSOR_VALUES["object"]),
            "lux": float(settings.SENSOR_VALUES["lux"]),
            "luminosity": float(settings.SENSOR_VALUES["luminosity"]),
            "seeing": float(settings.SENSOR_VALUES["seeing"]),
            "lightning_distanceToStorm": int(settings.SENSOR_VALUES["lightning_distanceToStorm"]),
            "nelm": float(settings.SENSOR_VALUES["nelm"]),
            "concentration": int(settings.SENSOR_VALUES["concentration"]),

            "errors": settings.SENSOR_VALUES["errors"].strip()[:-1],

            "SLEEPTIME_s": settings.SETTINGS["SLEEPTIME_s"],
            "DISPLAY_TIMEOUT_s": settings.SETTINGS["DISPLAY_TIMEOUT_s"],
            "DISPLAY_ON": settings.SETTINGS["DISPLAY_ON"],
            "PATH": settings.SETTINGS["PATH"],
            "skystate": settings.SKYSTATE,
            "localIP": settings.LOCAL_IP,
            "calculated_mag_limit": settings.SETTINGS["calculated_mag_limit"],
            "set_sqm_limit": settings.SETTINGS["set_sqm_limit"],
            "seeing_thr": settings.SETTINGS["seeing_thr"],

            "max_lux": settings.SETTINGS["max_lux"],
            "setpoint1": settings.SETTINGS["setpoint1"],
            "setpoint2": settings.SETTINGS["setpoint2"],

            "abr_seeing": settings.SETTINGS["seeing"],
            "abr_raining": settings.SETTINGS["raining"],
            "abr_luminosity": settings.SETTINGS["luminosity"],
            "abr_nelm": settings.SETTINGS["nelm"],
            "abr_concentration": settings.SETTINGS["concentration"],
            "abr_object": settings.SETTINGS["object"],
            "abr_ambient": settings.SETTINGS["ambient"],
            "abr_lux": settings.SETTINGS["lux"],
            "abr_lightning_distanceToStorm": settings.SETTINGS["lightning_distanceToStorm"],

            "en_seeing": settings.SETTINGS["en_seeing"],
            "en_raining": settings.SETTINGS["en_raining"],
            "en_luminosity": settings.SETTINGS["en_luminosity"],
            "en_nelm": settings.SETTINGS["en_nelm"],
            "en_concentration": settings.SETTINGS["en_concentration"],
            "en_object": settings.SETTINGS["en_object"],
            "en_ambient": settings.SETTINGS["en_ambient"],
            "en_lux": settings.SETTINGS["en_lux"],
            "en_lightning_distanceToStorm": settings.SETTINGS["en_lightning_distanceToStorm"],

            "plot": settings.BAR,
            }


if __name__ == '__main__':
    # start thread to update website with  current values, runs parallel to Flask app
    threading.Thread(target=update_load).start()
    # create / read settings file
    if not Path("SQM_settings.json").is_file():
        with open("SQM_settings.json", 'w') as f:
            json.dump(settings.SETTINGS, f)
    else:
        with open("SQM_settings.json", 'r') as file:
            settings.SETTINGS = json.load(file)
            settings.SPECIFIC_DIRECTORY = Path(settings.SETTINGS["PATH"])
    # get ip of this server/PC
    settings.LOCAL_IP = general_utils.get_ip()
    # open IP in browser
    webbrowser.open("http://" + str(settings.LOCAL_IP) + ":5000")
    # run Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)