from flask import Blueprint
#import the settings from functions/data_and_settings.py
import data_and_settings as settings
from datetime import datetime
from flask import request
import my_functions.sensor_specific as sensor_specific

esp32_bp = Blueprint('esp32', __name__)
# send settings to ESP32 as json response
@esp32_bp.route('/getsettings')
def sendsettings():
    return settings.SETTINGS

# get & process ESP32 sensor data
@esp32_bp.route('/SQM', methods=['POST'])
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
            if not settings.SPECIFIC_DIRECTORY.is_dir():
                settings.SPECIFIC_DIRECTORY.mkdir()
            print(settings.SPECIFIC_DIRECTORY)
            with open(settings.SPECIFIC_DIRECTORY / "last_measurement.txt", 'w') as f1:
                f1.write(timestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                f1.close()
            # loop through sensor values
            for key, value in jsonfile.items():
                # if key is sensor errors or isSeeing
                if key == "errors" or key == "isSeeing":
                    settings.SENSOR_VALUES[key] = value
                # write the values to the ASCII file if enabled
                elif settings.SETTINGS.get("en_"+key, 0) == 1 and  float(value) > -100:
                    settings.SENSOR_VALUES[key] = value
                    # create a directory for each sensor and append the values to the sensor file
                    measurement_path = settings.SPECIFIC_DIRECTORY / settings.SETTINGS[key] / timestamp.strftime('%y')
                    measurement_path.mkdir(parents=True, exist_ok=True)
                    # ASCII encode timestamp + value
                    temp_val = f"{timestamp.strftime('%H:%M')}\t{str(value).replace('.', ',')}\r\n".encode('ascii')
                    # write to .dat file
                    with open(measurement_path / f"{settings.SETTINGS[key].upper()}{timestamp.strftime('%y%m%d')}.dat", 'ab') as f1:
                        f1.write(temp_val)
                    sensor_specific.get_cloud_state()
        return ""
