import glob, sys, re, os
import pandas as pd
sys.path.append('../../')
import __constants
from datetime import datetime
# per participant moeten we een output krijgen

# input:
# Centrale graden:
# 10 graden -> 2669	  3091
# 20 graden -> 2454	  3306
# 30 graden -> 2232	  3528
# 40 graden -> 2000	  3760
# 50 graden -> 1753	  4007
# 60 graden -> 1485	  4275
# 70 graden -> 1188   4572
# 80 graden -> 852	  4908
# 90 graden -> 463	  5297
# 100 graden -> 0	  5760

# links ->      0     2880
# rechts ->     2880  5760

# optie om evt. meer toe te voegen...

# neem gp.csv
# hoeveel van de tijd binnen die area gekeken wordt

# label                   x1        x2       y1     y2      total_dwell_duration (s)          ratio_dwell_duration
# centrale 10 graden      500       1000     0      0       5.34                              50%
# ...

def compute_deg_times(df, session_time, label, x1, x2, y1, y2):
    # count rows within deg field
    deg100 = df.loc[(df['x'] >= x1) & (df['x'] <= x2) & (df['y'] >= y1) & (df['y'] <= y2)]
    total_dwell_duration = len(deg100) * 1/__constants.sample_rate_ET

    return {
        'label': label,
        'x1': x1,
        'x2': x2,
        'y1': y1,
        'y2': y2,
        'total_dwell_duration': total_dwell_duration,
        'ratio_dwell_duration': total_dwell_duration / session_time
    }

# Loop over all gp.csv and compute

gps = glob.glob("{}/*/*/*/gp.csv".format(__constants.input_folder))
columns = ['label', 'x1', 'x2', 'y1', 'y2', 'total_dwell_duration', 'ratio_dwell_duration']

big_frame = pd.DataFrame({}, columns=columns + ['participant_id', 'measurement_moment', 'task_id'])

for file_name in gps:
    regex = re.findall("(P-[0-9]..)\/(T[0-9])\/([a-zA-Z0-9]*)", file_name)

    participant_id = regex[0][0]
    measurement_moment = regex[0][1]
    task_id = regex[0][2]

    print('Analysing file {} {} {}'.format(participant_id, measurement_moment, task_id))
    
    # read csv
    df = pd.read_csv(file_name)
    session_time = len(df) * 1/__constants.sample_rate_ET
    
    # generate output
    output = pd.DataFrame([], columns=columns)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_10', -211, 211, -211, 211)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_20', -426, 426, -426, 426)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_30', -648, 648, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_40', -880, 880, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_50', -1127, 1127, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_60', -1395, 1395, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_70', -1692, 1692, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_80', -2028, 2028, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_90', -2417, 2417, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'deg_100', -2880, 2880, -600, 600)

    output.loc[len(output), :] = compute_deg_times(df, session_time, 'left', -2880, 0, -600, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'right', 0, 2880, -600, 600)

    output.loc[len(output), :] = compute_deg_times(df, session_time, 'top', -2880, 2880, 0, 600)
    output.loc[len(output), :] = compute_deg_times(df, session_time, 'bottom', -2880, 2880, -600, 0)

    # make output folder
    screens_output_folder = '{}/{}/{}/{}/screens'.format(__constants.output_folder, participant_id, measurement_moment, task_id)
    if not os.path.exists(screens_output_folder):
        os.makedirs(screens_output_folder)

    # construct file name
    d = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    output_file_name = '{}/{}/{}/{}/screens/{}_{}_{}_screens_{}.csv'.format(
        __constants.output_folder, participant_id, measurement_moment, task_id, participant_id, measurement_moment, task_id, d)
    output.to_csv(output_file_name)

    output['participant_id'] = participant_id
    output['measurement_moment'] = measurement_moment
    output['task_id'] = task_id

    big_frame = pd.concat([big_frame, output])

output_file_name = '{}/merged_screen_outputs.csv'.format(__constants.output_folder)
big_frame.to_csv(output_file_name)

print('Done, saved the file to {}'.format(output_file_name))