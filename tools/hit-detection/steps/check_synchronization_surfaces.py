import sys
sys.path.append('../../../')

import __constants, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def check_synchronization_surfaces(participant_id, measurement_moment, task_id, synchronization_file, console):

    # Open synchronization surface data file
    synchronization_surface_name = '{}/{}/{}/{}/gaze_positions_on_surface_ijksurface.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)
    synchronization_surface = pd.read_csv(synchronization_surface_name)

    # Open the dummy surface gaze positon data
    surface_5_name = '{}/{}/{}/{}/gaze_positions_on_surface_Surface5WB.csv'.format(
        __constants.input_folder, participant_id, measurement_moment, task_id)
    surface_5 = pd.read_csv(surface_5_name)

    # Correct the timestamps in synchronization_surface
    # Get the first timestamp of surface 5
    first_gaze_timestamp = surface_5.iloc[0]['gaze_timestamp']
    synchronization_surface['gaze_timestamp'] = synchronization_surface['gaze_timestamp'] - first_gaze_timestamp
    synchronization_surface['frame'] = synchronization_surface['gaze_timestamp'] * __constants.frame_rate

    # Fetch expected frame numbers of the synchronization surfaces
    input_file_name = '{}/videos/start_end_frames/synchronization/{}'.format(__constants.data_folder, synchronization_file)

    # Fetch all start and end frames of synchronization surfaces
    a_file = open(input_file_name, "r")
    synchronization_frames = json.loads(a_file.read())
    gps_in_scene = []

    for i in range(len(synchronization_frames)-1):
        # per scene, we want to know how many synchronization detections we find
        current = synchronization_frames[i]
        next = synchronization_frames[i+1]

        # find the amount of GP's between frame CURRENT.end and NEXT.start
        n = len(synchronization_surface[(synchronization_surface['frame'] > current['end']) & (synchronization_surface['frame'] < next['start'])])

        gps_in_scene.append(n)

    console.print('[purple]Found gps in scenes: {}'.format(gps_in_scene))
    scenes = list(range(1, len(gps_in_scene) + 1))

    # linear regression across points
    df = pd.DataFrame(data={'gps_in_scene': gps_in_scene, 'scenes': scenes })
    x = df.scenes
    y = df.gps_in_scene
    model = np.polyfit(x, y, 1)
    predict = np.poly1d(model)
    
    # show graph
    plt.scatter(x,y)
    x_lin_reg = range(1, len(gps_in_scene) + 1)
    y_lin_reg = predict(x_lin_reg)
    model = np.polyfit(x, y, 1)
    plt.plot(x_lin_reg, y_lin_reg, c = 'r')

    plt.xticks(np.arange(min(x), max(x)+1, 1.0))
    plt.xlabel('Scene')
    plt.ylabel('Frames found with ijksurfaces')
    # plt.show()
    # sys.exit()

    filename = '{}/{}/{}/{}/frames_with_ijksurfaces_found_in_scenes.png'.format(__constants.output_folder, participant_id, measurement_moment, task_id)
    plt.savefig(filename)

    # regression: ax + b = y
    a = model[0]
    b = model[1]

    console.print('[purple]Found linear regression fit across previous array, with coefficient: {}'.format(a))
    console.print('[purple]Saved file to {}'.format(filename))
    
    # plt.show()