from flask import Flask, request
from datetime import datetime
import flask
from pathlib import Path

app = Flask(__name__)

# if the files should be saved in a specified directory (eg "C:/Users")
# else leave it as "" - and it saves it in the same as the script gets run
SPECIFIC_DIRECTORY = Path('C:/Users/Persie/Pictures')


@app.route('/SQM', methods=['POST'])
def process():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            json = request.json
            with open(SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt", 'w') as file:
                file.write(datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
                file.close()
            for key in json.keys():
                if json[key] == "-1":
                    continue
                else:
                    measurement_path = SPECIFIC_DIRECTORY / "SQM" / key
                    if not measurement_path.is_dir():
                        measurement_path.mkdir()
                    temp_val = (datetime.now().strftime('%H:%M') + "\t" + json[key] + "\n").encode('ascii')
                    with open(measurement_path / (key[0:2].upper() +
                                                  datetime.now().strftime('%Y')[2:4] +
                                                  datetime.now().strftime('%m%d') + ".dat"), 'ab') as f:
                        f.write(temp_val)
            f.close()
            return ""


@app.route('/')
def show_if_online():
    if (SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt").is_file():
        with open(SPECIFIC_DIRECTORY / "SQM" / "last_measurement.txt", 'r') as file:
            loaded_time = datetime.strptime(file.read(), "%d-%b-%Y (%H:%M:%S.%f)")
            now = datetime.now()
            difference = (now - loaded_time)
            duration_in_s = difference.total_seconds()
            days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
            hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
            minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
            seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds

            if minutes[0] > 6:
                running = "SQM NOT running"
            else:
                running = "SQM Running"
            last_transm = loaded_time.strftime("%d %b %Y %H:%M:%S") + " - last transmission"
            min_ago = "%d days, %d hours, %d minutes and %d seconds ago" % (
                days[0], hours[0], minutes[0], seconds[0])
            return flask.render_template('index.html', running=running, last_transm=last_transm, min_ago=min_ago)
    return flask.render_template('index.html', running="SQM files not available", last_transm="", min_ago="")


if __name__ == '__main__':
    if not (SPECIFIC_DIRECTORY / "SQM").is_dir():
        (SPECIFIC_DIRECTORY / "SQM").mkdir()
    app.run(host='0.0.0.0', port=5000, threaded=True)
