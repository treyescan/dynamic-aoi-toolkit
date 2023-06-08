import sys
sys.path.append('../../../')

import __constants
import pandas as pd

def merge_gaze_positions(participant_id, measurement_moment, task_id, progress, task):
    ## Variables
    surfaces_base_name = '{}/{}/{}/{}/gaze_positions_on_surface_Surface{:d}WB.csv'
    dummy_surface_base_name = '{}/{}/{}/{}/gaze_positions_on_surface_dummysurface.csv'
    synchronization_surface_base_name = '{}/{}/{}/{}/gaze_positions_on_surface_ijksurface.csv'

    output_file_name = '{}/{}/{}/{}/merged_raw_gp.csv'.format(__constants.input_folder, participant_id, measurement_moment, task_id)
    surfaces = __constants.surfaces # surface meta data

    dfs = {} # a list of all pandas dataframes from all surfaces

    progress.print('[bold yellow]We are preparing data from each surface.')

    for n in range(1, __constants.n_surfaces + 1):
        dfs[n] = pd.read_csv(surfaces_base_name.format(__constants.input_folder, participant_id, measurement_moment, task_id, n))
        progress.print('Found {} rows in CSV #{}'.format(len(dfs[n]), n))

        # Remove onsurf = False, participant did not look in this surface so no usable x and y coordinates to transform.
        progress.print('- Removing onsurf = False from data frame #{}'.format(n))
        dfs[n] = dfs[n].loc[dfs[n]['on_surf'] == True]

        # The screen is divided in 9 surfaces. Each surface has a x-norm value of 0 to 1.
        progress.print('- Adding pix_x_norm to data frame #{}'.format(n))
        dfs[n]['pix_x_norm'] = dfs[n]['x_norm'] * (surfaces[n]['right_border'] - surfaces[n]['left_border']) 

        # Correcting values of pix_x_norm.
        progress.print('- Correcting pix_x_norm values in data frame #{}'.format(n))
        dfs[n]['true_x_scaled'] = dfs[n]['pix_x_norm'] + surfaces[n]['left_border']

        # Correcting values of pix_y_norm.
        progress.print('- Creating true_y_scaled from y_norm in data frame #{}'.format(n))
        dfs[n]['true_y_scaled'] = dfs[n]['y_norm'] * __constants.total_surface_height

        # New column with surface number.
        progress.print('- Adding surface number to data frame #{}'.format(n))
        dfs[n]['surface_no'] = n

        progress.advance(task)

    # Merging into one dataframe
    progress.print('[bold yellow]Perparing data is done. Start merging frames into one frame.')
    merged_df = pd.concat(dfs)
    merged_df = merged_df.sort_values(by=['gaze_timestamp'], kind='mergesort')

    # The surfaces overlap in order to always have data of each part of the screen. 
    # Hence, duplicate rows can exist if a participant looks in the overlap region. We decide to keep the data of the most central surface.
    # We have to be smart on making the algorithm that decides which row to keep
    # If we iterate over all the rows, it will get rather slow. Instead we do this:
    # 1. we create a new dataframe containing all duplicates (duplicate_df) from the original dataframe
    # 2. we remove the duplicates from the original dataframe
    # 3. in the duplicate_df we create a new column called keep_condition: keep_condition = absolute(surface_no - 5)
    #      examples:
    #        surface no: 2 --> keep_condition = |2 - 5| = 3
    #        surface no: 3 --> keep_condition = |3 - 5| = 2
    #        surface no: 5 --> keep_condition = |5 - 5| = 0
    #        surface no: 8 --> keep_condition = |8 - 5| = 3
    #        surface no: 9 --> keep_condition = |9 - 5| = 4
    #     as you can see, the closer the keep_condition is to 0, the closer the surface is to surface 5
    # 4. now we will sort the duplicate_df on keep_condition (ascending order)
    # 5. now we will remove all duplicates in duplicate_df BUT we keep the FIRST record
    #     we know that the first occurence in the dataframe must be the one closest to surface 5
    # 6. we remove the keep_condition column
    # 7. we merge the duplicate_df with the original dataframe (merged_df) into final_df
    # 8. we sort the final_df on gaze_timestamp 

    ## 1. Create duplicate_df
    duplicate_df = merged_df[merged_df.duplicated('gaze_timestamp', keep=False)]
    # print(duplicate_df[['world_timestamp', 'gaze_timestamp', 'true_x_scaled', 'surface_no']])
    progress.print("Based on gaze_timestamp, we have found {} duplicate rows. We will now filter them.".format(len(duplicate_df)))
    progress.advance(task)

    ## 2. Remove all duplicates from the original dataframe
    merged_df = merged_df.drop_duplicates(subset=['gaze_timestamp'], keep=False)
    # check = merged_df[merged_df.duplicated('gaze_timestamp', keep=False)]
    # print(check[['world_timestamp', 'gaze_timestamp', 'true_x_scaled', 'surface_no']])
    progress.advance(task)

    ## 3. create keep_condition
    duplicate_df['keep_condition'] = abs(duplicate_df['surface_no'] - 5)
    # print(duplicate_df[['world_timestamp', 'gaze_timestamp', 'surface_no', 'keep_condition']])
    progress.advance(task)

    ## 4. sort duplicate_df on keep_condition
    duplicate_df = duplicate_df.sort_values(by=['keep_condition'], kind='mergesort')
    # print(duplicate_df[['world_timestamp', 'gaze_timestamp', 'surface_no', 'keep_condition']])
    progress.advance(task)

    ## 5. remove duplicates (on gaze_timestamp) from duplicate_df, but keep first
    duplicate_df = duplicate_df.drop_duplicates(subset=['gaze_timestamp'], keep='first')
    # check = duplicate_df[duplicate_df.duplicated('gaze_timestamp', keep=False)]
    # print(check[['world_timestamp', 'gaze_timestamp', 'true_x_scaled', 'surface_no']])
    progress.advance(task)

    ## 6. remove the keep_condition column
    duplicate_df = duplicate_df.drop(columns=['keep_condition'])
    # print(duplicate_df[['world_timestamp', 'gaze_timestamp', 'surface_no']])
    progress.advance(task)

    ## 7. Merge duplicate_df and merged_df into final_df
    final_df = pd.concat([merged_df, duplicate_df])
    # print(final_df[['world_timestamp', 'gaze_timestamp', 'surface_no']])
    check = final_df[final_df.duplicated('gaze_timestamp', keep=False)]
    # print(check[['world_timestamp', 'gaze_timestamp', 'true_x_scaled', 'surface_no']])
    progress.print("We have filtered all duplicates. Based on gaze_timestamp, the final dataframe now contains {} duplicate rows.".format(len(check)))
    progress.advance(task)

    ## 8. sort final_df
    final_df = final_df.sort_values(by=['gaze_timestamp'], kind='mergesort')
    progress.advance(task)

    ## 9a. Correct the offset by finding the first gaze_timestamp from the dummy surface and remove everything 
    # before it from the final dataset.

    # NB: Commented this section due to unreliable dummy QR codes. We export from pupil labs from the right start.
     
    # dummy_df = pd.read_csv(dummy_surface_base_name.format(__constants.input_folder, participant_id, task_id))
    # first_gaze_timestamp = dummy_df.iloc[0]['gaze_timestamp']
    # final_df = final_df[final_df['gaze_timestamp'] >= first_gaze_timestamp]
    # progress.print("We are now fetching the first known gaze timestamp from the dummy surfaces, and removing everything before it")

    ## 9b. Correct the ending of the dataset, by removing everything after the 
    # last gaze_timestamp from the ijk surface dataframe.
    synchronization_df = pd.read_csv(synchronization_surface_base_name.format(__constants.input_folder, participant_id, measurement_moment, task_id))
    last_gaze_timestamp = synchronization_df.iloc[-1]['gaze_timestamp']
    final_df = final_df[final_df['gaze_timestamp'] <= last_gaze_timestamp]
    progress.print("We are now fetching the last known gaze timestamp from the ijk surfaces, and removing everything after it")
    progress.advance(task)

    ## 10. Add offsets to true_x_scaled and true_y_scaled so the center of the screen is (0, 0)
    final_df['true_x_scaled'] = final_df['true_x_scaled'] - __constants.total_surface_width/2
    final_df['true_y_scaled'] = final_df['true_y_scaled'] - __constants.total_surface_height/2
    progress.advance(task)

    ## In this script we are filling up the gaps that were created be removing on_surf = false (in gaze_timestamps) 
    ## by including rows for which on_surf = false
    ## this position data is not useful, but we want to create a complete database and may later use the confidence

    final_df['on_screen'] = True

    # Fetch surface 5 (center)
    center_surface_df = pd.read_csv(surfaces_base_name.format(
        __constants.input_folder, participant_id, measurement_moment, task_id, 5))
    # Everything we add may have an on_screen = False
    center_surface_df['on_screen'] = False

    # Only surfaces with on_surf False should be considered (the other surfaces already exist in merged_surfaces)
    to_insert_potentially_df = center_surface_df[center_surface_df['on_surf'] == False]

    # Filter everything out of the df before the first gaze timestamp from the dummy surface (See step 9 above)
    # to_insert_potentially_df = to_insert_potentially_df[to_insert_potentially_df['gaze_timestamp'] >= first_gaze_timestamp]

    # Compute correct coordinates (see first steps above and step 10)
    to_insert_potentially_df['pix_x_norm'] = to_insert_potentially_df['x_norm'] * (surfaces[5]['right_border'] - surfaces[5]['left_border']) 

    to_insert_potentially_df['true_x_scaled'] = to_insert_potentially_df['x_norm'] + surfaces[5]['left_border']
    to_insert_potentially_df['true_y_scaled'] = to_insert_potentially_df['y_norm'] * __constants.total_surface_height

    to_insert_potentially_df['true_x_scaled'] = to_insert_potentially_df['true_x_scaled'] - __constants.total_surface_width/2
    to_insert_potentially_df['true_y_scaled'] = to_insert_potentially_df['true_y_scaled'] - __constants.total_surface_height/2

    # Merge the merged_surfaces with everything from center (which passes conditions above)
    new_df = pd.concat([final_df, to_insert_potentially_df]).drop_duplicates(keep='first', subset=['gaze_timestamp'])
    progress.advance(task)

    # Order the df on gaze_timestamp
    new_df = new_df.sort_values(by=['gaze_timestamp'], kind='mergesort')

    # Normalize timestamps to actual time (in seconds)
    new_df = new_df.reset_index()

    if new_df['gaze_timestamp'][0] < 0:
        new_df['actual_time'] = new_df['gaze_timestamp'] + abs(new_df.loc[0, 'gaze_timestamp'])
    else:
        new_df['actual_time'] = new_df['gaze_timestamp'] - abs(new_df.loc[0, 'gaze_timestamp'])

    # Write the csv
    progress.print("We will start outputting the dataframe to a csv file. This will take a second.")
    new_df.to_csv(output_file_name, index=False)
    progress.print('[green bold]We are done! The new csv is outputted to {} and contains {} rows.'.format(output_file_name, len(new_df)))