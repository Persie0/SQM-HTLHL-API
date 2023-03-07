import plotly
import plotly.graph_objs as go
import pandas as pd
from pathlib import Path
import json

# convert a .dat file to a pandas dataframe
def dat_to_df(dat_file_full_path):
    # read the .dat file and convert it to a pandas dataframe
    df = pd.read_csv(dat_file_full_path, sep='\t', header=None, names=['time', 'value'])
    # use file name as date
    # get file name from path with pathlib
    f_date = Path(dat_file_full_path).stem[2:8]   # 2:8 because of the "SQ" in the file name
    # convert all dataframes to datetime, date is the f_date and time is the time column
    #year = int(f_date[:1]), month = int(f_date[2:3]), day = int(f_date[4:]
    #replace the date with the date from the file name
    df['time'].replace('0000', regex=True).replace("20"+f_date[:1], regex=True)
    # sort the data by time
    df.sort_values(by=['time'], inplace=True)

    # convert the values to float
    df['value'] = df['value'].astype(float)
    return df

# Create a plotly plot from a dataframe
def create_plot(df):
    # Create a scatter plot with the time and value columns from the dataframe
    scatter_plot = go.Scatter(
        x=df['time'],
        y=df['value'],
        mode='lines+markers',
        line=dict(
            width=1
        ),
        marker=dict(
            size=7,
            symbol='circle',
        ),
        connectgaps=False,
    )

    # Package the plot data as a list of dictionaries
    data = [scatter_plot]

    # Return the serialized plot data
    return json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
