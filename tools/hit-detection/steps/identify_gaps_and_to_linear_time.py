import sys
sys.path.append('../../../')

import __constants,  os.path, json
import pandas as pd
import numpy as np 
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt

from utils.utils__general import show_error

def identify_gaps_and_to_linear_time(participant_id, measurement_moment, task_id, progress, task):
    input_file_name = '{}/{}/{}/{}/merged_mf_gp.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)

    output_file_name = '{}/{}/{}/{}/gp.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)

    text_file = '{}/{}/{}/{}/number_of_filtered_rows.txt'.format(
        __constants.output_folder, participant_id, measurement_moment, task_id)
    
    # Check if our input file exists
    if not os.path.isfile(input_file_name):
        show_error('Input file for step 2 is not found. Run step 1 first.', progress)

    df = pd.read_csv(input_file_name)
    total_count = df.shape[0]

    # Rolling average on confidence
    df['confidence'] = df['confidence'].rolling(3, center=True).mean()
    df.iloc[0, df.columns.get_loc('confidence')] = df.iloc[0, df.columns.get_loc('confidence')]
    df.iloc[-1, df.columns.get_loc('confidence')] = df.iloc[-1, df.columns.get_loc('confidence')]

    # Save the size of the original data set
    with open(text_file,"w+") as f:
        f.write('Total amount of rows: {} \n\n'.format(total_count))
    
    # Save how many rows will be changed to NaN to a text file
    removed_NaN_count = df[df['confidence'] < __constants.confidence_threshold].shape[0]
    with open(text_file,"a+") as f:
        percentage = round(removed_NaN_count/total_count*100, 2)
        f.write('Set position of {} rows ({}%) to NaN due to confidence below {} \n'.format(
            removed_NaN_count, percentage, __constants.confidence_threshold))

    # Set X and Y to NaN when confidence < threshold
    df.loc[df['confidence'] < __constants.confidence_threshold, 'true_x_scaled'] = np.NaN
    df.loc[df['confidence'] < __constants.confidence_threshold, 'true_y_scaled'] = np.NaN

    # Save how many rows will be changed to on_screen == False
    removed_NaN_count = df[df['on_screen'] == False].shape[0]
    with open(text_file,"a+") as f:
        percentage = round(removed_NaN_count/total_count*100, 2)
        f.write('Set position of {} rows ({}%) to NaN due to on_screen == False \n'.format(
            removed_NaN_count, percentage))

    # Set X and Y to NaN when not looking on screen
    df.loc[df['on_screen'] == False, 'true_x_scaled'] = np.NaN
    df.loc[df['on_screen'] == False, 'true_y_scaled'] = np.NaN

    # For debugging purposes:
    # print(df[['confidence', 'on_screen', 'true_x_scaled', 'true_y_scaled']][df['on_screen'] == False].head())
    # print(df[['confidence', 'on_screen', 'true_x_scaled', 'true_y_scaled']][df['confidence'] < __constants.confidence_threshold].head())

    # Count NaN rows and save to file
    NaN_count = df[df['true_x_scaled'].isnull()].shape[0]
    with open(text_file,"a+") as f:
        percentage = round(NaN_count/total_count*100, 2)
        f.write('Set position to NaN of {} rows in total ({}% of the original dataset) \n\n'.format(
            NaN_count, percentage))
 
    progress.advance(task)

    # Interpolate x and y if the time gaps are < threshold (e.g. 60 ms)
    df = df.reset_index()
    currentlyAtGap = False
    currentGapStartedAtIndex = np.NaN
    durationOfCurrentGap = 0
    gap_timestamps_to_save = []

    for index, gp in df.iterrows():
        if(index % 2000 == 0 or index == 0):
            progress.print('[bold deep_pink4]Processed: {}/{}'.format(index, len(df)))

        # Open gap
        if(np.isnan(gp['true_x_scaled']) and np.isnan(gp['true_y_scaled']) and not currentlyAtGap):
            # progress.print('[blue]Opened a gap at index: {}'.format(index))
            currentGapStartedAtIndex = index
            currentlyAtGap = True
        
        # Decide on gap duration
        currentlyAtLastGazeP = (index == len(df) - 1)
        if(currentlyAtGap and not currentlyAtLastGazeP):
            durationOfCurrentGazeP = df.loc[index + 1, 'actual_time'] - gp['actual_time']
            durationOfCurrentGap = durationOfCurrentGap + durationOfCurrentGazeP

        # Close and interpolate gap
        if(
            (
                # if we find a row which has a x AND y again
                (not np.isnan(gp['true_x_scaled']) and not np.isnan(gp['true_y_scaled'])) 
                or
                # if we are at the last row
                currentlyAtLastGazeP
            )
            # and we are currenly keeping track of a gap
            and currentlyAtGap
        ):
            # THEN: close and interpolate the gap

            # For debugging purposes
            # progress.print('Closed a gap at index: {}, with duration: {}s'.format(index, durationOfCurrentGap))
            # progress.print('Should we interpolate between index {} and index {}?'.format(currentGapStartedAtIndex, index))

            # Save the gap start and end time
            if(durationOfCurrentGap > __constants.valid_gap_threshold):
                # We need to save the start and end time of the gap
                # since we need it in to_lin_time_scale_and_generate_tsv
                # to NaN the x,y after interpolating is done
                startTimestamp = df.iloc[(currentGapStartedAtIndex - 1)]['actual_time'] 
                if(currentGapStartedAtIndex == 0):
                    startTimestamp = 0
                endTimestamp = df.iloc[index]['actual_time']
                gap_timestamps_to_save.append([startTimestamp, endTimestamp])

            # Interpolate x
            df.loc[(currentGapStartedAtIndex - 1):index, 'true_x_scaled'] = df.loc[(currentGapStartedAtIndex - 1):index, 'true_x_scaled'].interpolate()
            # Interpolate y
            df.loc[(currentGapStartedAtIndex - 1):index, 'true_y_scaled'] = df.loc[(currentGapStartedAtIndex - 1):index, 'true_y_scaled'].interpolate()

            # For debugging purposes
            # print(df.loc[(currentGapStartedAtIndex - 1):index, ['confidence', 'on_screen', 'true_x_scaled', 'true_y_scaled']].head())

            # Reset
            currentlyAtGap = False
            durationOfCurrentGap = 0
            currentGapStartedAtIndex = np.NaN

    # Save gap indexes to file
    gap_timestamps_file = '{}/{}/{}/{}/gap_timestamps.json'.format(__constants.output_folder, participant_id, measurement_moment, task_id)

    file_handle = open(gap_timestamps_file, "w")
    json.dump(gap_timestamps_to_save, file_handle)
    file_handle.close()

    # Gaps at the very start of the dataset, could not have been interpolated (because we are interpolating forwards)
    # However, these values should be interpolated as well.
    # Thus, we "fill backwards" those NaN cells at the very start with the first known value
    # In most cases (when gaps are not very short) these values will be replaced by NaNs after interpolating
    if(pd.isna(df.iloc[0, df.columns.get_loc('true_x_scaled')])):
         for index, gp in df.iterrows():
             if(not pd.isna(df.iloc[index, df.columns.get_loc('true_x_scaled')])):
                 df.loc[0:index-1, ('true_x_scaled')] = np.repeat(df.iloc[index, df.columns.get_loc('true_x_scaled')], index)
                 df.loc[0:index-1, ('true_y_scaled')] = np.repeat(df.iloc[index, df.columns.get_loc('true_y_scaled')], index)
                 break

    # Interpolate to linear time scale
    gp = to_lin_time(progress, df, output_file_name, participant_id, task_id)
    
    # Gaps > 75ms +/- (__constants.add_gap_samples) seconds naar NaN
    # Now, check in the original dataframe where we have gaps (we saved this before)
    # NaN the x,y in rows where we know there is a gap with (__constants.add_gap_samples) seconds margin
    gap_timestamps_file = '{}/{}/{}/{}/gap_timestamps.json'.format(
        __constants.output_folder, participant_id, measurement_moment, task_id)
    a_file = open(gap_timestamps_file, "r")
    gap_timestamps = json.loads(a_file.read())

    gp_for_calculating_interpolated_rows = gp.copy()

    for timestamp in gap_timestamps:
        gp_for_calculating_interpolated_rows.loc[(gp_for_calculating_interpolated_rows['t'] > timestamp[0]) & \
            (gp_for_calculating_interpolated_rows['t'] < timestamp[1]), 'x'] = np.NaN
        gp_for_calculating_interpolated_rows.loc[(gp_for_calculating_interpolated_rows['t'] > timestamp[0]) & \
            (gp_for_calculating_interpolated_rows['t'] < timestamp[1]), 'y'] = np.NaN

        gp.loc[(gp['t'] > timestamp[0] - __constants.add_gap_samples) & \
             (gp['t'] < timestamp[1] + __constants.add_gap_samples), 'x'] = np.NaN
        gp.loc[(gp['t'] > timestamp[0] - __constants.add_gap_samples) & \
             (gp['t'] < timestamp[1] + __constants.add_gap_samples), 'y'] = np.NaN

    # the amount of rows left interpolated < valid_gap_threshold
    # count how many rows we interpolated in total, and subtract the amount of rows in gaps > valid_gap_threshold

    rows_to_NaN_without_extended_gap = gp_for_calculating_interpolated_rows[gp_for_calculating_interpolated_rows['x'].isnull()].shape[0]
    interpolated_rows_count = NaN_count - rows_to_NaN_without_extended_gap

    # Save some stats to the number_of_filtered_rows.txt
    NaN_count_with_extended_gaps = gp[gp['x'].isnull()].shape[0]
    with open(text_file,"a+") as f:

        f.write('After interpolation to linear time, set position of {} rows set to NaN\n'
            .format(rows_to_NaN_without_extended_gap))

        f.write('{} interpolated rows are left in the dataset (these where < threshold of {} seconds)\n'
            .format(interpolated_rows_count, __constants.valid_gap_threshold))

        percentage = round(NaN_count_with_extended_gaps/total_count*100, 2)
        f.write('Set position of {} rows ({}% of the original dataset) to NaN (after extending the gaps)\n'
            .format(NaN_count_with_extended_gaps, percentage))

    # Save the GP to a file
    gp.to_csv(output_file_name)

    progress.print("Done! We will start outputting the dataframe to a csv file. This will take a second.")
    progress.print('[bold green]We are done! The new csv is outputted to {} and contains {} rows.'.format(output_file_name, len(gp)))

def to_lin_time(progress, gp, output_file_name, participant_id, task_id):
    first_timestamp = gp.actual_time.iloc[0]  
    last_timestamp = gp.actual_time.iloc[-1] 

    progress.print('First timestamp: {}'.format(first_timestamp))
    progress.print('Last timestamp: {}'.format(last_timestamp))
    
    progress.print('Average sample rate in data set: {}'.format(len(gp)/last_timestamp))

    # we find the new index
    timeIX = np.linspace(
        int(np.floor(first_timestamp)), 
        int(np.ceil(last_timestamp)), 
        int(np.ceil(last_timestamp - first_timestamp) * __constants.sample_rate_ET + 1)
    )
 
    def interp(x, y):
        f = PchipInterpolator(x, y, extrapolate=True)
        return f(timeIX)

    gazeInt = pd.DataFrame()
    gazeInt.loc[:, 't'] = timeIX

    gazeInt.loc[:, 'x'] = interp(gp.actual_time, gp.true_x_scaled)
    gazeInt.loc[:, 'y'] = interp(gp.actual_time, gp.true_y_scaled)

    # Add frame numbers
    gazeInt['frame'] = np.ceil((gazeInt['t'] * __constants.frame_rate) + 0.00001) - 1
    gazeInt['frame'] = gazeInt['frame'].astype(int)

    return gazeInt