"""
Script to combine all accuracy files from hit-detection outputs to one file, which can be imported into your statistics software
"""

import sys
sys.path.append('../../')

import argparse
import __constants, glob, os, platform, subprocess
import pandas as pd
import re

parser = argparse.ArgumentParser()
parser.add_argument('--id', help='Batch ID to include in output file names')

args = parser.parse_args()
batch_id = args.id

# fetch all json files
json_to_combine = glob.glob("{}/*/*/*/number_of_filtered_rows_{}.json".format(__constants.output_folder, batch_id))

# show error if non found
if(len(json_to_combine) == 0):
    raise Exception('No files to merge found'.format(id))

# empty df
df = pd.DataFrame()
for file in json_to_combine:
    # convert json to row and add to df to export
    dict = pd.DataFrame([pd.read_json(file, typ='series').to_dict()])
    df = pd.concat([df, dict], ignore_index=True)

# export df
output_file_name = '{}/merged_accuracy_{}.csv'.format(__constants.output_folder, batch_id)
df.to_csv(output_file_name)

print("Done! {} files combined to merged_accuracy_{}.csv".format(len(json_to_combine), batch_id))

# empty wide df
df_wide = pd.DataFrame()

# get all unique participants in the original df
participants = df['participant_id'].unique()
for participant_id in participants:
    # for all participants
    df_original_participant = df[df['participant_id'] == participant_id]
    df_participant = pd.DataFrame()
    df_participant['participant_id'] = participant_id

    # Get task1 and task2 info
    task1 = df_original_participant[df_original_participant['task_id'] == 'task1']
    task2 = df_original_participant[df_original_participant['task_id'] == 'task2']

    # we don't need these columns
    task1 = task1.drop(['task_id', 'measurement_moment'], axis=1)
    task2 = task2.drop(['task_id', 'measurement_moment'], axis=1)

    # rename everything to include _taskN, except for particpant ID
    task1 = task1.rename(columns={c: c+'_task1' for c in df.columns if c not in ['participant_id']})
    task2 = task2.rename(columns={c: c+'_task2' for c in df.columns if c not in ['participant_id']})

    # combine the two rows (based on particpant id)
    df_participant = pd.merge(task1, task2, on='participant_id', how='outer')

    # shift particpant_id column to front
    first_column = df_participant.pop('participant_id')
    df_participant.insert(0, 'participant_id', first_column)

    # add to df to export
    df_wide = pd.concat([df_wide, df_participant], ignore_index=True)

# export df wide
output_file_name = '{}/merged_accuracy_wide_{}.csv'.format(__constants.output_folder, batch_id)
df_wide.to_csv(output_file_name)

print("Done! {} participants combined to merged_accuracy_wide_{}.csv".format(len(participants), batch_id))