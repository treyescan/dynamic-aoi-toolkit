"""
Script to combine all individual participant hit detection outputs to one file, which can be imported into your statistics software
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

csv_to_combine = glob.glob("{}/*/*/*/*_{}.csv".format(__constants.output_folder, batch_id))

if(len(csv_to_combine) == 0):
    raise Exception('No files to merge found'.format(id))

dfs = []

for file in csv_to_combine:
    path = file.replace(__constants.output_folder, "")

    regex = re.findall("(P-[0-9]..)\/(T[0-9])\/([a-zA-Z0-9]*)", path)

    participant_id = regex[0][0]
    measurement_moment = regex[0][1]
    task_id = regex[0][2]

    objects = pd.read_csv(file)
    
    objects.insert(2, 'participant_id', participant_id)
    objects.insert(3, 'measurement_moment', measurement_moment)
    objects.insert(4, 'task_id', task_id)

    dfs.append(objects)

big_frame = pd.concat(dfs, ignore_index=True)
big_frame = big_frame.drop(columns=['Unnamed: 0', 'index'])

output_file_name = '{}/merged_outputs_{}.csv'.format(__constants.output_folder, batch_id)
big_frame.to_csv(output_file_name)

print("Done! {} files combined to merged_outputs_{}.csv".format(len(csv_to_combine), batch_id))