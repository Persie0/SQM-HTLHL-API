import json
import data_and_settings as settings
from datetime import datetime, timedelta
# calculate cloud state from IR temperature sensor
def get_cloud_state():
    # calculate the difference between the object and ambient temperature
    temp_diff = float(settings.SENSOR_VALUES["ambient"]) - float(settings.SENSOR_VALUES["object"])
    # calculate the cloud state
    if temp_diff > settings.SETTINGS["setpoint1"]:
        settings.SKYSTATE = "Clear"
    elif (temp_diff > settings.SETTINGS["setpoint2"]) and (temp_diff < settings.SETTINGS["setpoint1"]):
        settings.SKYSTATE = "Partly cloudy"
    elif temp_diff < settings.SETTINGS["setpoint2"]:
        settings.SKYSTATE = "Cloudy"
    else:
        settings.SKYSTATE = "Unknown"


# calculates the magnitude limit, for calibration of the SQM-sensor
def calculate_mag_limit(loaded_time: datetime, actual_sqm: float):
    # look that the calibration SQM-value is ok and not older than 15min
    if loaded_time > (datetime.now() - timedelta(
            minutes=15)) and settings.SENSOR_VALUES["luminosity"] != "-333":
        # calculate the magnitude limit

        # calculated_mag_limit = set_sqm_limit - actual_sqm + professionally_measured_sqm
        settings.SETTINGS["calculated_mag_limit"] = round(
            (settings.SETTINGS["set_sqm_limit"] - float(settings.SENSOR_VALUES["luminosity"]) + actual_sqm), 2)
        #set magnitude limit to the calculated value
        settings.SETTINGS["set_sqm_limit"] = settings.SETTINGS["calculated_mag_limit"]
        # save settings
        with open(settings.SETTINGSPATH, 'w') as f3:
            json.dump(settings.SETTINGS, f3)
        return True
    else:
        return False
