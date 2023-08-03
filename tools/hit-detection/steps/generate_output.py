import sys

sys.path.append('../../../')

import __constants, os.path, subprocess, json, math, platform, re
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from utils.utils__general import show_error
from utils.utils__aois import prepare_aois_df

def generate_output(participant_id, measurement_moment, task_id, aois_file, batch_id, progress, task):
    progress.print("[bold yellow]We are starting generating output")

    input_file_name = '{}/{}/{}/{}/entries_exits.json'.format(__constants.output_folder, participant_id, measurement_moment, task_id)
    if not os.path.isfile(input_file_name):
        show_error('Input file for step 5 is not found. Run step 4 first. {}'.format(input_file_name), progress)

    input_file_name_gps_x_aois = '{}/{}/{}/{}/df_gps_x_aois.csv'.format(__constants.output_folder, participant_id, measurement_moment, task_id)
    if not os.path.isfile(input_file_name):
        show_error('Input file for step 5 is not found. Run step 3 first.', progress)

    # Fetch all entries and exits
    a_file = open(input_file_name, "r")
    entries_and_exits = json.loads(a_file.read())

    # Prepare AOI's
    df_aois = pd.read_csv('{}/input-aoi/{}'.format(__constants.data_folder, aois_file))
    df_aois = prepare_aois_df(df_aois)

    # Set up the basics of the output file
    df = pd.DataFrame(columns = [
        'object_id',
        'first_appearance_time',
        'last_appearance_time',
        'total_appearance_duration',
        'is_hit',
        'absolute_entry_time',
        'entry_time',
        'amount_entries_exits',
        'total_dwell_duration',
        'total_diversion_duration',
    ])

    # Fill object ID
    df['object_id'] = (df_aois['Object ID'].unique().reshape(1, -1)[0])
    df = df.sort_values(['object_id'])
    df = df.reset_index()

    # First appearance time
    df_temp = df_aois.copy()
    df_temp = df_temp.drop_duplicates(['Object ID'], keep='first')
    df_temp = df_temp.sort_values(['Object ID'])
    df_temp = df_temp.reset_index(drop=True)
    df['first_appearance_time'] = df_temp['actual_time']

    # Last appearance time
    df_temp = df_aois.copy()
    df_temp = df_temp.drop_duplicates(['Object ID'], keep='last')
    df_temp = df_temp.sort_values(['Object ID'])
    df_temp = df_temp.reset_index(drop=True)
    df['last_appearance_time'] = df_temp['actual_time'] + 1/__constants.frame_rate # add 1 frame to account for the last frame on which it is shown

    # Total appearance duration
    df['total_appearance_duration'] = df['last_appearance_time'] - df['first_appearance_time']
    df = df.round({'total_appearance_duration': 2})

    # First entry time
    for index, row in df.iterrows():
        ee = entries_and_exits[row['object_id']]
        if(len(ee) > 0):
            absolute_entry_time = ee[0]
            df.iloc[index, df.columns.get_loc('absolute_entry_time')] = absolute_entry_time

    # Set some 0's; we'll fill it later
    df['total_diversion_duration'] = 0
    df['total_dwell_duration'] = 0
    df['amount_entries_exits'] = 0
    df['is_hit'] = 0

    # First, set up all columns needed for entries and exist (and dwell time)
    longest_key = None
    longest_length = 0

    progress.advance(task)

    # Decide how many entry(#n), exit(#n), dwell_time(#n) columns we need to generate
    for aoi, timestamps in entries_and_exits.items():
        if(longest_length < len(timestamps)):
            longest_key = aoi
            longest_length = len(timestamps)

    progress.advance(task)

    # We need to add this many:
    sets_to_add = int(longest_length / 2)

    # Add the place holder columns (set to None for now)
    for i in range(sets_to_add):
        df['entry({})'.format(i + 1)] = None
        df['exit({})'.format(i + 1)] = None
        df['dwell_time({})'.format(i + 1)] = None

    progress.advance(task)

    # Populate all the entry(n) exit(n) and dwell_time(n) columns
    for aoi, timestamps in entries_and_exits.items():

        for i in range(len(timestamps)):
            
            if i % 2 != 0:

                index = df.index[df['object_id'] == aoi]

                n = str(math.ceil(i/2))
                entry_n = previous_timestamp = timestamps[i - 1]
                exit_n = current_timestamp = timestamps[i]
                dwell_time_n = exit_n - entry_n

                if(dwell_time_n > 0):
                    # check if is higher than 0 for it may occur that
                    # entry and exit timestamps are the same (in this case only 1 HIT has been detected)
                    # for that particular AOI
                    # only check if is higher than 0 when we 2 timestamps. if we have more, always add the timestamps
                    df.loc[index, 'entry({})'.format(n)] = entry_n
                    df.loc[index, 'exit({})'.format(n)] = exit_n
                    df.loc[index, 'dwell_time({})'.format(n)] = dwell_time_n           

    progress.advance(task)

    # Remove short durations between exits and entries
    i = 0
    while i < sets_to_add: 
        # for each set entry, exit, dwell
        n = i + 1
        if n > 1:
            for index, row in df.iterrows():
                # dur = duration_between_entry_and_previous_exit
                if 'entry({})'.format(n) in df and 'exit({})'.format(n-1) in df and 'exit({})'.format(n-1) in df and row['entry({})'.format(n)] != None and row['exit({})'.format(n-1)] != None:
                    dur = row['entry({})'.format(n)] - row['exit({})'.format(n-1)]
                    
                    if(dur < __constants.minimal_threshold_entry_exit):
                        progress.print('found a duration of {} so we\'re merging this entry&exit pair with the previous one'.format(dur))

                        # replace the exit(n-1) with the exit(n)
                        df.at[index, 'exit({})'.format(n - 1)] = row['exit({})'.format(n)]
                        # take the sum of dwell(n-1) and dwell(n)
                        df.at[index, 'dwell_time({})'.format(n - 1)] = row['dwell_time({})'.format(n - 1)] + row['dwell_time({})'.format(n)]
                        df.at[index, 'entry({})'.format(n)] = None
                        df.at[index, 'exit({})'.format(n)] = None
                        df.at[index, 'dwell_time({})'.format(n)] = None

                        # After removing a short interval between exit(n-1) and entry(n):
                        # Reset the counter
                        i = 0
        i = i + 1

    progress.advance(task)

    # Entry time
    df['entry_time'] = df['absolute_entry_time'] - df['first_appearance_time']

    # After that, filter short dwell_time(n)
    for i in range(sets_to_add):
        # for each set entry, exit, dwell
        n = i + 1
        if n > 1:
            for index, row in df.iterrows():
                if row['dwell_time({})'.format(n)] != None and row['dwell_time({})'.format(n)] < __constants.minimal_threshold_dwell:
                    df.at[index, 'entry({})'.format(n)] = None
                    df.at[index, 'exit({})'.format(n)] = None
                    df.at[index, 'dwell_time({})'.format(n)] = None

    progress.advance(task)

    # output_temp_file_name = '{}/{}/{}/{}/{}_output_temp'.format(
    #     __constants.output_folder, participant_id, measurement_moment, task_id, participant_id)
    # df.to_csv(output_temp_file_name)

    # Now, delete empty columns
    df.dropna(how='all', axis=1, inplace=True)

    progress.advance(task)

    # Calculate dwell duration by getting the sum of dwell_duration
    df['total_dwell_duration'] = df.filter(regex='dwell_time\([\d]*\)',axis=1).sum(axis=1)

    # Calculate percentage dwell_duration/total_appearance
    ratio_dwell_duration_total_appereance = df['total_dwell_duration']/df['total_appearance_duration']*100
    df.insert(6, 'ratio_dwell_duration_total_appereance', ratio_dwell_duration_total_appereance)

    # Total diversion duration
    df['total_diversion_duration'] = df['total_appearance_duration'] - df['total_dwell_duration']

    # Calcualte the amount of entries and exits
    last_column_name = df.columns[-1]
    last_column_regex = re.search("dwell_time\((\d*)\)", last_column_name)
    last_column = int(last_column_regex.group(1))

    for index, row in df.iterrows():
        amount_entries_exits_for_row = 0

        for i in range(last_column):
            if 'dwell_time({})'.format(i + 1) in df:
                value_of_dwell_for_row = df.iloc[index, df.columns.get_loc('dwell_time({})'.format(i + 1))]

                if(value_of_dwell_for_row != None and not math.isnan(value_of_dwell_for_row)):
                    amount_entries_exits_for_row = amount_entries_exits_for_row + 1

        df.iloc[index, df.columns.get_loc('amount_entries_exits')] = amount_entries_exits_for_row
        progress.print("row {} has {} entries & exits".format(row['object_id'], amount_entries_exits_for_row))

    # Fill column
    df['total_diversion_duration'] = df['total_appearance_duration'] - df['total_dwell_duration']

    # Compute is hit or not
    df['is_hit'] = df['total_dwell_duration'] > 0
    df['is_hit'] = df['is_hit'].astype(int)

    # If is not a hit, all cells in the same row after is_hit are meaningless, void them
    df.loc[df['is_hit'] == 0, 'entry_time'] = None
    df.loc[df['is_hit'] == 0, 'absolute_entry_time'] = None

    progress.advance(task)

    # Write to csv
    d = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    output_file_name = '{}/{}/{}/{}/{}_{}_{}_output_{}_id_{}'.format(
        __constants.output_folder, participant_id, measurement_moment, task_id, participant_id, measurement_moment, task_id, d, batch_id)

    # When is_hit = 0, all columns to the right of is_hit are not informative
    # To avoid miscommunication, we remove those columns
    df.loc[(df['is_hit'] == 0), 'ratio_dwell_duration_total_appereance'] = math.nan
    df.loc[(df['is_hit'] == 0), 'amount_entries_exits'] = math.nan
    df.loc[(df['is_hit'] == 0), 'total_dwell_duration'] = math.nan
    df.loc[(df['is_hit'] == 0), 'total_diversion_duration'] = math.nan
    
    # Remove empty cells
    df = pd.read_csv(StringIO(re.sub(',+',',',df.to_csv())))

    # Drop empty columns 
    df = df.dropna(axis='columns', how='all')

    df.to_csv('{}.csv'.format(output_file_name), float_format='%.2f')

    # Save the constants/thresholds used to a file with similar 
    # name so we can trace our assumptions later
    text_file = '{}.txt'.format(output_file_name)
    with open(text_file,"w+") as f:
        f.write('minimal_threshold_entry_exit = {} \n'.format(__constants.minimal_threshold_entry_exit)),
        f.write('minimal_threshold_dwell = {} \n'.format(__constants.minimal_threshold_dwell)),
        f.write('minimal_angle_of_aoi = {} \n'.format(__constants.minimal_angle_of_aoi)),
        f.write('confidence_threshold = {} \n'.format(__constants.confidence_threshold)),
        f.write('error_angle = {} \n'.format(__constants.angle_a)),
        f.write('minimal_angle_of_aoi = {} \n'.format(__constants.angle_b)),

    progress.print("[green bold]Saved output to {}.csv".format(output_file_name))

    # if not platform.system() == 'Windows':
    #     subprocess.call(['open', "{}.csv".format(output_file_name)])
    
    progress.advance(task)
