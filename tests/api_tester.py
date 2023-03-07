import requests
import json


def post_data():
    sensorErrors = ['Error1', 'Error2', 'Error3']  # sample sensor errors
    raining = 1  # sample sensor value
    luminosity = 100  # sample sensor value
    seeing = 80  # sample sensor value
    nelm = 6  # sample sensor value
    concentration = 50  # sample sensor value
    objectt = 22  # sample sensor value
    ambient = 20  # sample sensor value
    lux = 500  # sample sensor value
    lightning_distanceToStorm = 10  # sample sensor value
    SEEING_ENABLED = 0  # sample sensor value

    # create a dictionary with sensor values
    data = {
        "raining": raining,
        "luminosity": luminosity,
        "seeing": seeing,
        "nelm": nelm,
        "concentration": concentration,
        "object": objectt,
        "ambient": ambient,
        "lux": lux,
        "lightning_distanceToStorm": lightning_distanceToStorm,
        "errors": ", ".join(sensorErrors),
        "isSeeing": SEEING_ENABLED
    }

    # convert the dictionary to JSON string
    json_data = json.dumps(data)


    # send POST request to the server
    headers = {'Content-type': 'application/json'}
    response = requests.post("http://127.0.0.1:5000/SQM", data=json_data, headers=headers)

    # Return true if the post request is successful
    return response.status_code == 200

post_data()