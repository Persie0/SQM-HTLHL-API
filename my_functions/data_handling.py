import plotly
import plotly.graph_objs as go
import pandas as pd
import json

# convert a .dat file to a pandas dataframe
def dat_to_df(dat_file_full_path):
    # read the .dat file and convert it to a pandas dataframe
    df = pd.read_csv(dat_file_full_path, sep='\t', header=None, names=['time', 'value'])
    # sort the data by time
    df.sort_values(by=['time'], inplace=True)
    # replace the , with a .
    df['value'] = df['value'].str.replace(',', '.')
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
