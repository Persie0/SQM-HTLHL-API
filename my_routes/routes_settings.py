from flask import Blueprint, request, redirect, url_for, render_template, flash
from pathlib import Path
import data_and_settings as settings
import json
from datetime import datetime
import my_functions.sensor_specific as sensor_specific

set_bp = Blueprint('settings', __name__)

# ESP32 settings page
@set_bp.route('/settings', methods=["GET", "POST"])
def settingspage():
    if request.method == "POST":
        # Define a dictionary of setting names and their corresponding types
        setting_types = {
        "seeing_thr": int,
        "DISPLAY": bool,
        "setpoint1": float,
        "setpoint2": float,
        "max_lux": float,
        "DISPLAY_TIMEOUT_s": int,
        "SLEEPTIME_s": int,
        "PATH": str,
        "set_sqm_limit": float
        }
        # Iterate over the settings and update the SETTINGS dictionary
        for setting_name, setting_type in setting_types.items():
            setting_value = request.form.get(setting_name, type=setting_type)
            if setting_value is not None:
                settings.SETTINGS[setting_name] = setting_value
        # Update the SPECIFIC_DIRECTORY if the PATH setting has changed
        if "PATH" in settings.SETTINGS and settings.SETTINGS["PATH"] != "":
            settings.SPECIFIC_DIRECTORY = Path(settings.SETTINGS["PATH"])
        # save settings.SETTINGS
        with open(settings.SETTINGSPATH, 'w') as f3:
            json.dump(settings.SETTINGS, f3)
        flash('Settings saved')
        # route to status page
        return redirect(url_for('statuspage'))
    # if GET show settings page
    return render_template('settings.html')


# abbreviation settings page
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
        with open(settings.SETTINGSPATH, 'w') as f3:
            json.dump(settings.SETTINGS, f3)
        # route to status page
        flash('Settings saved')
        return redirect(url_for('statuspage'))
    # else show settings page
    return render_template('abriv_settings.html')

@set_bp.route('/onoff', methods=["POST"])
def onoffpage():
    # Update SETTINGS based on request.json data0
    for key in request.json.keys():
        if key in settings.SETTINGS.keys():
            settings.SETTINGS[key] = request.json[key]
    # Save updated SETTINGS to file
    with open(settings.SETTINGSPATH, 'w') as f3:
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
            if (settings.SPECIFIC_DIRECTORY / "last_measurement.txt").is_file():
                with open(settings.SPECIFIC_DIRECTORY / "last_measurement.txt", 'r') as f4:
                    # read last measurement time
                    loaded_time = datetime.strptime(f4.read(), "%d-%b-%Y (%H:%M:%S.%f)")
            else:
                return redirect(url_for('error', er="No SQM values available"))
            successful= sensor_specific.calculate_mag_limit(loaded_time, actual_SQM)
            if not successful:
                return redirect(url_for('error', er="SQM value older than 15 min or no value for this session"))
        else:
            #redirect to page showing error
            return redirect(url_for('error', er="No value entered"))
        flash('Calibrated successfully')
        # route to status page
        return redirect(url_for('statuspage'))