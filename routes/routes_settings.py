from flask import Blueprint, request, redirect, url_for, render_template
from pathlib import Path
#import the settings from functions/data_and_settings.py
import data_and_settings as settings
import json
from datetime import datetime
import functions.sensor_specific as sensor_specific

set_bp = Blueprint('settings', __name__)

# ESP32 settings page
@set_bp.route('/settings', methods=["GET", "POST"])
def settingspage():
    # if sending/saving settings.SETTINGS
    if request.method == "POST":
        # getting the input from the settings.SETTINGS page
        # check if value x was entered
        seeing_thr = request.form.get("seeing_thr", type=int)
        if seeing_thr is not None:
            settings.SETTINGS["seeing_thr"] = seeing_thr
        if request.form.get("DISPLAY") is not None:
            settings.SETTINGS["DISPLAY_ON"] = 1
        else:
            settings.SETTINGS["DISPLAY_ON"] = 0
        setpoint1 = request.form.get("setpoint1", type=float)
        if setpoint1 is not None:
            settings.SETTINGS["setpoint1"] = setpoint1
        setpoint2 = request.form.get("setpoint2", type=float)
        if setpoint2 is not None:
            settings.SETTINGS["setpoint2"] = setpoint2
        max_lux = request.form.get("max_lux", type=float)
        if max_lux is not None:
            settings.SETTINGS["max_lux"] = max_lux
        dto = request.form.get("DISPLAY_TIMEOUT_s", type=int)
        if dto is not None:
            settings.SETTINGS["DISPLAY_TIMEOUT_s"] = dto
        sleep_t = request.form.get("SLEEPTIME_s", type=int)
        if sleep_t is not None:
            settings.SETTINGS["SLEEPTIME_s"] = sleep_t
        path = request.form.get("PATH", type=str)
        if path is not None and path != "":
            settings.SETTINGS["PATH"] = path
            settings.SPECIFIC_DIRECTORY = Path(settings.SETTINGS["PATH"])
        set_sqm_limit = request.form.get("set_sqm_limit", type=float)
        if set_sqm_limit is not None:
            settings.SETTINGS["set_sqm_limit"] = set_sqm_limit

        # save settings.SETTINGS
        with open("SQM_settings.json", 'w') as f3:
            json.dump(settings.SETTINGS, f3)
        # route to status page
        return redirect(url_for('statuspage'))
    # else show settings.SETTINGS page
    return render_template('settings.html')


# abbreviation settings.SETTINGS page
@set_bp.route('/abriv', methods=["GET", "POST"])
def abrivpage():
    # if sending/saving settings.SETTINGS
    if request.method == "POST":
        # getting the input from the html forms
        abr_dictionary = request.form.to_dict()
        # loop through input fields
        for abr_key in abr_dictionary.keys():
            abr_value = abr_dictionary[abr_key]
            # if form field is not empty
            if abr_value != "":
                settings.SETTINGS[abr_key.replace("abr_", "")] = abr_value
        # save settings.SETTINGS
        with open("SQM_settings.json", 'w') as f3:
            json.dump(settings.SETTINGS, f3)
        # route to status page
        return redirect(url_for('statuspage'))
    # else show settings.SETTINGS page
    return render_template('abriv_settings.html')

#ESP32 turn the sensors on/off
@set_bp.route('/onoff', methods=["POST"])
def onoffpage():
    # sensors even enabled?, get the transmitted data from the index.html
    # get JSON.stringify({ en_seeing: status });
    if "en_seeing" in request.json and request.json["en_seeing"] is not None:
        settings.SETTINGS["en_seeing"] = request.json["en_seeing"]

    if "en_lux" in request.json and request.json["en_lux"] is not None:
        settings.SETTINGS["en_lux"] = request.json["en_lux"]

    if "en_luminosity" in request.json and request.json["en_luminosity"] is not None:
        settings.SETTINGS["en_luminosity"] = request.json["en_luminosity"]

    if "en_lux" in request.json and request.json["en_lux"] is not None:
        settings.SETTINGS["en_lux"] = request.json["en_lux"]

    if "en_nelm" in request.json and request.json["en_nelm"] is not None:
        settings.SETTINGS["en_nelm"] = request.json["en_nelm"]

    if "en_concentration" in request.json and request.json["en_concentration"] is not None:
        settings.SETTINGS["en_concentration"] = request.json["en_concentration"]

    if "en_ambient" in request.json and request.json["en_ambient"] is not None:
        settings.SETTINGS["en_ambient"] = request.json["en_ambient"]

    if "en_object" in request.json and request.json["en_object"] is not None:
        settings.SETTINGS["en_object"] = request.json["en_object"]

    if "en_lightning_distanceToStorm" in request.json and request.json["en_lightning_distanceToStorm"] is not None:
        settings.SETTINGS["en_lightning_distanceToStorm"] = request.json["en_lightning_distanceToStorm"]

    if "en_raining" in request.json and request.json["en_raining"] is not None:
        settings.SETTINGS["en_raining"] = request.json["en_raining"]

    # save settings.SETTINGS
    with open("SQM_settings.json", 'w') as f3:
        json.dump(settings.SETTINGS, f3)

    return ""

# SQM-sensor calibration
@set_bp.route('/calibrate', methods=["POST"])
def calibrate():
    if request.method == "POST":
        # getting the input from the html forms
        actual_SQM = request.form.get("actual_SQM", type=float)
        # if form field is not empty
        if actual_SQM is not None:
            settings.SETTINGS["actual_SQM"] = actual_SQM
            settings.SETTINGS["actual_SQM_time"] = datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
            successful= sensor_specific.calculate_mag_limit()
            if not successful:
                return redirect(url_for('error', er="SQM value older than 15 min"))
        else:
            #redirect to page showing error
            return redirect(url_for('error', er="No value entered"))
        return redirect(url_for('statuspage'))