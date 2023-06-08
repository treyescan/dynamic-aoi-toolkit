import sys
sys.path.append('../../../')

import __constants, os.path, json
import pandas as pd

from utils.utils__aois import prepare_aois_df
from utils.utils__general import show_error

def identify_entries_and_exits(participant_id, measurement_moment, task_id, aois_file, progress, task):
    progress.print("[bold yellow]We are starting identifying entries and exits")

    input_file_name = '{}/{}/{}/{}/gp_x_aoi.csv'.format(__constants.output_folder, participant_id, measurement_moment, task_id)
    if not os.path.isfile(input_file_name):
        show_error('Input file for step 4 is not found. Run step 3 first.', progress)

    # Prepare AOI's
    df_aois = pd.read_csv('{}/input-aoi/{}'.format(__constants.data_folder, aois_file))
    df_aois = prepare_aois_df(df_aois)

    entries_and_exits = {}

    aois = df_aois['Object ID'].unique() # get all objects

    for aoi in aois:
        entries_and_exits[aoi] = [] # make a placeholder in entries_and_exits

    # Loop over all gps(x)aois
    df_gps_x_aois = pd.read_csv(input_file_name)

    progress.update(task, total=(len(df_gps_x_aois)-1))
    progress.print('[bold yellow]Starting iterating all rows in df_gps_x_aois to identify entries and exits')

    counter = 0
    for i, hit_row in df_gps_x_aois.iterrows():
        # Some nice progress output
        if(counter % 2000 == 0 or counter == 0):
            progress.print('[bold deep_pink4]Processed: {}/{}'.format(counter, len(df_gps_x_aois)))
        counter = counter + 1

        progress.advance(task)

        # Loop over all aois to check if we have seen a one

        for aoi in aois:

            if(hit_row[aoi] == 1 and len(entries_and_exits[aoi]) % 2 == 0):
                # We're looping and finding a 1 AND the previous found mark was an exit
                # so mark this moment as an entry
                entries_and_exits[aoi].append(hit_row['t'])

            if(hit_row[aoi] == 0 and len(entries_and_exits[aoi]) % 2 != 0):
                # If we are finding a 0 and we may register an exit, do it
                # The timestamp needed is not the current one (first 0 after gap, where 1 = non-hit)
                # But the previous one (last 1 of a hap, where 1 = hit)
                timestamp = df_gps_x_aois.iloc[i - 1, df_gps_x_aois.columns.get_loc('t')]
                entries_and_exits[aoi].append(timestamp)
    
    progress.advance(task)

    entries_exits_file = '{}/{}/{}/{}/entries_exits.json'.format(__constants.output_folder, participant_id, measurement_moment, task_id)

    file_handle = open(entries_exits_file, "w")
    json.dump(entries_and_exits, file_handle)
    file_handle.close()

    progress.print('[bold green]Done! We found and saved all entries and exits')
