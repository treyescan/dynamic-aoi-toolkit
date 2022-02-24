import __constants, sys, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rich.prompt import Confirm

sys.path.append('../../../')
from utils.utils__general import show_error

def check_calibration_surfaces(participant_id, video_id, calibration_file, console):

    # Open synchronization surface data file
    calibration_surface_name = '{}/{}/{}/gaze_positions_on_surface_ijksurface.csv'.format(
        __constants.input_folder, participant_id, video_id)
    calibration_surface = pd.read_csv(calibration_surface_name)

    # Open the dummy surface
    dummy_surface_name = '{}/{}/{}/gaze_positions_on_surface_dummysurface.csv'.format(
        __constants.input_folder, participant_id, video_id)
    dummy_surface = pd.read_csv(dummy_surface_name)

    # Correct the timestamps in calibration_surface
    first_gaze_timestamp = dummy_surface.iloc[0]['gaze_timestamp']
    calibration_surface['gaze_timestamp'] = calibration_surface['gaze_timestamp'] - first_gaze_timestamp
    calibration_surface['frame'] = calibration_surface['gaze_timestamp'] * 25

    # Fetch expected frame numbers of the calibration surfaces
    input_file_name = '../start_end_frames/synchronisation/{}'.format(calibration_file)

    # Fetch all entries and exits
    a_file = open(input_file_name, "r")
    calibration_frames = json.loads(a_file.read())
    gps_in_scene = []

    for i in range(len(calibration_frames) - 1):
        # per scene, we want to know how many calibration detections we find
        current = calibration_frames[i]
        next = calibration_frames[i+1]

        # find the amount of GP's between frame CURRENT.end and NEXT.start
        n = len(calibration_surface[(calibration_surface['frame'] > current['end']) & (calibration_surface['frame'] < next['start'])])

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

    plt.savefig('../outputs/{}/{}/frames_with_ijksurfaces_found_in_scenes.png'.format(participant_id, video_id))

    # regression: ax + b = y
    a = model[0]
    b = model[1]

    console.print('[purple]Found linear regression fit across previous array, with coefficient: {}'.format(a))
    
    plt.show()