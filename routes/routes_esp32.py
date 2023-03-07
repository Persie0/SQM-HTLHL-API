from flask import Blueprint
#import the settings from functions/data_and_settings.py
import data_and_settings as settings
from datetime import datetime
from flask import request
import functions.sensor_specific as sensor_specific

esp32_bp = Blueprint('esp32', __name__)
# send settings.SETTINGS to ESP32 as json response
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
            with open(settings.SPECIFIC_DIRECTORY / "last_measurement.txt", 'w') as f1:
                f1.write(timestamp.strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                f1.close()
            # loop through sensor values
            for key in jsonfile.keys():
                # "-333" means no data
                if jsonfile[key] == "":
                    continue
                else:
                    settings.SENSOR_VALUES[key] = jsonfile[key]
                # don't write values if sensor error (-333) and don't write the errors & if Seeing is on
                if key == "errors" or key == "isSeeing":
                    continue
                if float(jsonfile[key]) < -100:
                    continue
                # write the values to the sensor file if enabled
                elif settings.SETTINGS["en_"+key] == 1:
                    # create a directory for each sensor and append the values to the sensor file
                    # year only has 2 digits
                    measurement_path = settings.SPECIFIC_DIRECTORY / settings.SETTINGS[key] / timestamp.strftime('%Y')[2:4]
                    #create the directories if they don't exist
                    if not measurement_path.is_dir():
                        measurement_path.mkdir(parents=True)
                    # ASCII encode timestamp + value
                    temp_val = (timestamp.strftime('%H:%M') + "\t" + str(jsonfile[key]).replace(".",",") + "\r\n").encode('ascii')
                    # write to .dat file
                    with open(measurement_path / (settings.SETTINGS[key].upper() +
                                                  timestamp.strftime('%Y')[2:4] +
                                                  timestamp.strftime('%m%d') + ".dat"), 'ab') as f1:
                        f1.write(temp_val)
                        f1.close()
            sensor_specific.get_cloud_state()
            return ""
