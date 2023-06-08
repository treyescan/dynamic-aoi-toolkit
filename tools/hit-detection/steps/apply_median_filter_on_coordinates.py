import sys
sys.path.append('../../../')

import __constants
import pandas as pd

def apply_median_filter_on_coordinates(participant_id, measurement_moment, task_id, progress, task):
    progress.print("[blue]Applying median filter on true_x_scaled and true_y_scaled")

    input_file_name = '{}/{}/{}/{}/merged_raw_gp.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)

    output_file_name = '{}/{}/{}/{}/merged_mf_gp.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)

    df = pd.read_csv(input_file_name)

    # Apply median filter on true_x_scaled and true_y_scaled
    df['true_x_scaled_srm'] = df['true_x_scaled'].rolling(3, center=True).median()
    df['true_y_scaled_srm'] = df['true_y_scaled'].rolling(3, center=True).median()
    
    # Set first and last true_x_scaled and true_y_scaled
    df.iloc[0, df.columns.get_loc('true_x_scaled_srm')] = df.iloc[0, df.columns.get_loc('true_x_scaled')]
    df.iloc[-1, df.columns.get_loc('true_x_scaled_srm')] = df.iloc[-1, df.columns.get_loc('true_x_scaled')]
    df.iloc[0, df.columns.get_loc('true_y_scaled_srm')] = df.iloc[0, df.columns.get_loc('true_y_scaled')]
    df.iloc[-1, df.columns.get_loc('true_y_scaled_srm')] = df.iloc[-1, df.columns.get_loc('true_y_scaled')]

    # Remove old true_x_scaled and true_y_scaled and rename true_x_scaled_srm and true_y_scaled_srm
    df = df.drop(columns=['true_x_scaled', 'true_y_scaled'])
    df = df.rename(columns={"true_x_scaled_srm": "true_x_scaled", "true_y_scaled_srm": "true_y_scaled"})

    progress.advance(task)

    # Write to csv
    progress.print('[bold green]Done! We saved to {} with {} rows'.format(output_file_name, len(df)))
    df.to_csv(output_file_name)