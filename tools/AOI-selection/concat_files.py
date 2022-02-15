import os, sys, glob, argparse
import pandas as pd

sys.path.append('../../')
import __constants

# Make sure we can accept arguments
parser = argparse.ArgumentParser()
parser.add_argument('--folder', help='name of folder with csv files to concatenate (without trailing slash)', type=str)
args = parser.parse_args()

# Get the folder from the arguments
folder = args.folder

# To prevent mistakes, check if the output file already exists
# And quit if that is the case
csv_location = "combined_data/dataset.csv"
if os.path.isfile(csv_location): 
    print('\033[1;31m' + 'Output file ({}) already exists.'.format(csv_location))
    print('Aborted the script. Please check if we can overwrite the file.' + '\033[0m')
    sys.exit(0)

# Get all files from the folder
files = [i for i in glob.glob('{}/*.csv'.format(folder))]
for file in files:
    print("Found file: {}".format(file))

# Combine into one csv and make sure we sort it by frame
combined_csv = pd.concat([pd.read_csv(f) for f in files]).sort_values(by=['Frame'])

combined_csv.loc[combined_csv['x1'] < 0, 'x1'] = 0
combined_csv.loc[combined_csv['y1'] < 0, 'y1'] = 0
combined_csv.loc[combined_csv['x2'] > __constants.total_surface_width, 'x2'] = __constants.total_surface_width
combined_csv.loc[combined_csv['y2'] > __constants.total_surface_height, 'y2'] = __constants.total_surface_height

# Save the csv and print the location
combined_csv.to_csv(csv_location, index=False, encoding='utf-8-sig')
print('\033[0;32m' + 'We saved the file to {}'.format(csv_location) + '\033[0m')