import sys
sys.path.append('../../../')

import __constants, os.path
import pandas as pd
import numpy as np

from utils.utils__aois import prepare_aois_df
from utils.utils__margin_calculator import correct_aoi
from utils.utils__general import show_error

def identify_hits(participant_id, measurement_moment, task_id, aois_file, progress, task):
    progress.print("[bold yellow]We are starting identifying hits")

    # Prepare AOI's
    df_aois = pd.read_csv('{}/input-aoi/{}'.format(__constants.data_folder, aois_file))
    df_aois = prepare_aois_df(df_aois)

    # Check if our input file exists
    input_file_name = '{}/{}/{}/{}/gp.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)
    if not os.path.isfile(input_file_name):
        show_error('Input file for step 3 is not found. Run step 2 first.', progress)

    # Prepare merged surfaces with gaps
    df_gps = pd.read_csv(input_file_name)
    progress.print('found {} gaze position records'.format(len(df_gps)))

    # Create a df x gps
    df_gps_x_aois = pd.DataFrame(columns = ['t', 'frame', 'x', 'y',
        # more columns to come: all aoi's
    ])

    df_gps_x_aois['t'] = df_gps['t']
    df_gps_x_aois['frame'] = df_gps['frame']
    df_gps_x_aois['x'] = df_gps['x']
    df_gps_x_aois['y'] = df_gps['y']
    #0,0 point for original gp data is the left down corner and for aoi data the left up corner
    df_gps_x_aois['y_for_hit_calculation'] = __constants.total_surface_height - df_gps['y'] 

    new_cols = df_aois['Object ID'].unique().reshape(1, -1)[0]

    zeros = np.zeros(shape=(len(df_gps_x_aois),len(new_cols)))
    df_gps_x_aois[new_cols] = pd.DataFrame(zeros, columns=new_cols)

    df_gps_x_aois.to_csv('{}/{}/{}/{}/gp_x_aoi.csv'.format(__constants.output_folder, participant_id, measurement_moment, task_id))

    progress.print('We saved a preliminary df_gps_x_aois (with all hits to 0)')
    progress.update(task, total=(len(df_gps_x_aois)-1))
    progress.print('[bold yellow]Starting iterating all rows in df_gps_x_aois to identify hits')

    counter = 0
    for i, gp in df_gps_x_aois.iterrows():
        # Some nice progress output
        if(counter % 2000 == 0 or counter == 0):
            progress.print('[bold deep_pink4]Processed: {}/{}'.format(counter, len(df_gps_x_aois)))
        counter = counter + 1
        
        progress.advance(task)

        # Fetch AOIS on the same frame as the GP, 
        # if no aois are found, go to the next gaze position
        aois_to_consider = df_aois[df_aois['frame'] == gp['frame']]

        if(len(aois_to_consider) == 0):
            continue

        # We found aois to consider, let's do that now:
        for j, aoi_to_consider in aois_to_consider.iterrows():
            
            is_hit = False

            # So here we're doing something worth commenting:
            # Instead of passing x1, x2, y1, y2 to correct_aoi directly
            # we need to "translate" this (again) to the coordinates system in which 0,0 is top left
            # The correct_aoi script expects that coordinate system
            # Because the hit calculation expects the coordinate system in which 0,0 is the center
            # we translate this back again after it has been passed through correct_aoi

            x1 = aoi_to_consider['x1'] + __constants.total_surface_width / 2
            x2 = aoi_to_consider['x2'] + __constants.total_surface_width / 2
            y2 = (__constants.total_surface_height - aoi_to_consider['y2']) + __constants.total_surface_height / 2 
            y1 = (__constants.total_surface_height - aoi_to_consider['y1']) + __constants.total_surface_height / 2
            angle = aoi_to_consider['angle']

            x1, x2, y1, y2 = correct_aoi(x1, x2, y1, y2, angle)

            x1 = x1 - __constants.total_surface_width / 2
            x2 = x2 - __constants.total_surface_width / 2
            y2 = y2 - __constants.total_surface_height / 2 
            y1 = y1 - __constants.total_surface_height / 2 

            # Simple is "hit"
            is_hit = ((x1 < gp['x'] < x2) and (y1 < gp['y_for_hit_calculation'] < y2))

            if(is_hit):
                # Change the zero to one if needed                
                df_gps_x_aois.at[i, aoi_to_consider['Object ID']] = 1

    progress.print('Done with iterating over all rows, now saving the file')
    progress.print('[bold green]Done! We saved df_gps_x_aois.csv with {} rows'.format(len(df_gps_x_aois)))
    df_gps_x_aois.to_csv('{}/{}/{}/{}/gp_x_aoi.csv'.format(__constants.output_folder, participant_id, measurement_moment, task_id))

    progress.advance(task)
