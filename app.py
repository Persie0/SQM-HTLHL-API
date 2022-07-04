from flask import Flask, request
from datetime import datetime

app = Flask(__name__)


@app.route('/SQM', methods=['POST'])
def process():
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')
        if content_type == 'application/json':
            json = request.json
            for key in json.keys():
                if json[key] == "-1":
                    continue
                else:
                    temp_val = (datetime.now().strftime('%H:%M') + "\t" + json[key] + "\n").encode('ascii')
                    print(temp_val)
                    with open(key[0:2].upper() + datetime.now().strftime('%Y')[2:4]+ datetime.now().strftime('%m%d')+".dat", 'ab') as f:
                        f.write(temp_val)
            f.close()
            return ""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
