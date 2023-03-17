from flask import Blueprint, request, redirect, url_for, render_template
from datetime import datetime
import os
from pathlib import Path
import data_and_settings as settings
from my_functions.data_handling import dat_to_df, create_plot
from my_functions.abriviation import get_all_abbreviations

vis_bp = Blueprint('visualize', __name__)

# visualize the selected date
@vis_bp.route('/shortvisual/<sensor>')
def shortvisual(sensor):
    # get the selected date from the html page
    selected_date = request.args.get('date')
    # format the date to the correct format (the date is in the format dd.mm.yyyy + ".dat")
    formatted_date = sensor + selected_date[2:4] + selected_date[5:7] + selected_date[8:10] + ".dat"
    # redirect to the visualdate function (/visual/<sensor>/<datum>)
    return redirect(url_for('visualdate', sensor=sensor, datum=formatted_date))

# visualize the data
@vis_bp.route('/visual/<sensor>/<datum>')
def visualdate(sensor, datum):
    # format the date to the correct format
    formatted_datum= datum[6:8] + "." + datum[4:6] + "." + "20" + datum[2:4]
    # get all dat files in the directory
    temp_path = str(Path(settings.SETTINGS["PATH"]))+"/"+sensor+"/"+datetime.now().strftime("%Y")[2:4]
    if not os.path.exists(temp_path):
        return "No data available"
    dat_files = os.listdir(temp_path)
    # sort them by date
    dat_files.sort(key=lambda x: os.path.getmtime(temp_path + "/" + x), reverse=True)
    # check if date was passed
    if datum == "newest":
        # if not, redirect to the newest datebug fix
        return redirect('/visual/'+sensor+'/'+dat_files[0])
    else:
        # if yes, check if the date is in the list of dates
        if datum in dat_files:
            selected_file = datum
        else:
            return "Date not found"
    # convert the file to a pandas dataframe
    df = dat_to_df(str(Path(settings.SETTINGS["PATH"]))+"/"+sensor+"/"+datetime.now().strftime("%Y")[2:4]+"/"+selected_file)
    # create the plot
    settings.BAR = create_plot(df)
    #get earliest and latest date
    #earliest = dat_files[0]
    #latest = dat_files[-1]
    #convert to html date format
    #earliest = datetime.strptime(earliest[2:8], "%y%m%d").strftime("%Y-%m-%d")
    #latest = datetime.strptime(latest[2:8], "%y%m%d").strftime("%Y-%m-%d")
    # get all dates in html date format
    dates = []
    for i in dat_files:
        dates.append(datetime.strptime(i[2:8], "%y%m%d").strftime("%Y-%m-%d"))
    return render_template('visual.html', sens=settings.FULL_NAMES[get_all_abbreviations()[sensor]],
                                 plot=settings.BAR, dat_files=dat_files, abr=sensor, formatted_date=formatted_datum)
