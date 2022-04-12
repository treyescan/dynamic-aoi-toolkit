import __constants
import pandas as pd
import numpy as np

def prepare_aois_df(df):
    df['actual_time'] = df['Frame']/__constants.frame_rate # Add timestamp to the AOI data
    df['frame'] = df['Frame'].astype(int)
    df = df.round({'actual_time': 2})

    df['y1'] = 1200-df['y1'] # Inverse the y coordinates to match with pupil labs data
    df['y2'] = 1200-df['y2'] 

    df['width'] = df['x2'] - df['x1']

    # Omrekenen naar 'nieuwe' coordinatensysteem (0,0 tussen ogen)
    df['y1'] = df['y1'] - __constants.total_surface_height/2
    df['y2'] = df['y2'] - __constants.total_surface_height/2
    df['x1'] = df['x1'] - __constants.total_surface_width/2
    df['x2'] = df['x2'] - __constants.total_surface_width/2

    df['center_x'] = df['x1'] + (df['x2'] - df['x1']) / 2
    df['center_y'] = df['y2'] + (df['y1'] - df['y2']) / 2

    df['dot_product'] = df['x1'] * df['x2'] + df['center_y'] * df['center_y'] + __constants.z*__constants.z
    df['length_v1'] = (df['x1']**2 + df['center_y']**2 + __constants.z**2)**(1/2)
    df['length_v2'] = (df['x2']**2 + df['center_y']**2 + __constants.z**2)**(1/2)
    df['angle'] = np.degrees(np.arccos(df['dot_product'] / (df['length_v1'] * df['length_v2'])))

    return df