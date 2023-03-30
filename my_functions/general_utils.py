import socket
import data_and_settings as settings
from datetime import datetime

# Get the IP address of the current computer
def get_ip():
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Try to connect to 10.254.254.254 (doesn't have to be reachable)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        # If connection fails, set the IP address to 127.0.0.1 (localhost)
        ip = '127.0.0.1'
    finally:
        # Close the socket
        s.close()
    # Return the IP address
    return ip

def calculate_time_dif(loaded_time):
    now = datetime.now()
    # calculate time difference between now and last measurement
    difference = (now - loaded_time)
    # calculate time difference in seconds
    duration_in_s = difference.total_seconds()
    # calculate time difference in days, hours, minutes and seconds
    days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
    hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
    minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
    seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
    # if last measurement is older than SLEEPTIME_s + 10 seconds, show "not running"
    if duration_in_s > (settings.SETTINGS["SLEEPTIME_s"] * 2):
        settings.IS_RUNNING = False
        settings.SENSOR_VALUES["isSeeing"] = False
    # else show "running"
    else:
        settings.IS_RUNNING = True
    settings.LAST_TRANSMISSION = loaded_time.strftime("%d %b %Y %H:%M:%S")
    settings.MINUTES_AGO = "%d days, %d hours, %d minutes and %d seconds ago" % (
        days[0], hours[0], minutes[0], seconds[0])
