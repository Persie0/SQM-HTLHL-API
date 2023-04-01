from datetime import date

# time diagramm
BAR = None

# directory for the data files
SPECIFIC_DIRECTORY = ""
SETTINGSPATH = ""
FILEPATH = ""

# running variables
LAST_TRANSMISSION = "No data yet"
MINUTES_AGO = "Never"
SKYSTATE = "Unknown"
IS_RUNNING = False
LOCAL_IP = "error"

# set the default values for the settings
SETTINGS = {
    "seeing_thr": 3,
    "SLEEPTIME_s": 180,
    "DISPLAY_TIMEOUT_s": 200,
    "DISPLAY_ON": 1,
    "PATH": "",
    "last_SQM_time": date(1, 1, 1).strftime("%d-%b-%Y (%H:%M:%S.%f)"),
    "calculated_mag_limit": -333,
    "set_sqm_limit": 21.83,

    "max_lux": 50.0,
    "setpoint1": 22.0,
    "setpoint2": 2.0,

    # Abbriviations
    "raining": "RQ",
    "luminosity": "SQ",
    "seeing": "SE",
    "nelm": "NE",
    "concentration": "SA",
    "object": "HT",
    "ambient": "TQ",
    "lux": "HL",
    "lightning_distanceToStorm": "BD",

    # sensor enabled
    "en_seeing": 1,
    "en_raining": 1,
    "en_luminosity": 1,
    "en_nelm": 1,
    "en_concentration": 1,
    "en_object": 1,
    "en_ambient": 1,
    "en_lux": 1,
    "en_lightning_distanceToStorm": 1,
}

# whole names of the sensors
FULL_NAMES={
    "raining": "Raining",
    "ambient": "Ambient temperature",
    "object": "Object temperature",
    "lux": "Lux",
    "luminosity": "SQM",
    "seeing": "Seeing",
    "lightning_distanceToStorm": "Lightning distance",
    "nelm": "NELM",
    "concentration": "Air particle concentration",
}

# -333 if no data
SENSOR_VALUES = {
    "raining": "-333",
    "ambient": "-333",
    "object": "-333",
    "lux": "-333",
    "luminosity": "-333",
    "seeing": "-333",
    "lightning_distanceToStorm": "-333",
    "nelm": "-333",
    "concentration": "-333",
    "errors": "-333",
    "isSeeing": "0"
}