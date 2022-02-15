import argparse
import pandas as pd
import cv2, os, sys
import time, math
import numpy as np

sys.path.append('../4_gaze_roi_analysis')
import __constants
from utils__aois import prepare_aois_df
from utils__margin_calculator import correct_aoi

# Set window dimensions
FRAME_WIDTH = int(2880 * 0.4)

# parse the arguments used to call this script
parser = argparse.ArgumentParser()
parser.add_argument('--video', help='path of video file', type=str)
parser.add_argument('--data', help='path of the ROI csv file', type=str)
parser.add_argument('--participant', help='path of the participant data files', type=str)
parser.add_argument('--offset', help='offset of the frames in the data set', type=int, default=0)
parser.add_argument('--start_frame', help='start playing at frame', type=int, default=0)

args = parser.parse_args()
video_path = args.video
data_path = args.data # ROI data
participant_folder = args.participant
offset = args.offset
start_frame = args.start_frame - 1

gaze_data_path = '{}/gp.csv'.format(participant_folder)
annotations_data_path = '{}/annotations.csv'.format(participant_folder)

def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

# Read data file
df = pd.read_csv(data_path, header=0)
df_gp = pd.read_csv(gaze_data_path, header=0)
df_a = pd.read_csv(annotations_data_path, header=0)

# Prepare data
df = prepare_aois_df(df)

# NOTE: the timestamps of the merged gaze positions are normalized in merge_gaze_positions

if df_a['timestamp'][0] < 0:
    df_a['actual_time'] = df_a['timestamp'] + abs(df_gp.loc[0, 'gaze_timestamp'])
else:
    df_a['actual_time'] = df_a['timestamp'] - abs(df_gp.loc[0, 'gaze_timestamp'])

df_a['frame'] = df_a['actual_time']*25 + 0.00001
df_a['frame'] = df_a['frame'].astype(int)

# TODO: remove in january 2022
df_gp['frame'] = np.ceil(df_gp['frame'])
df_gp['frame'] = df_gp['frame'].astype(int)

# print(df_a.head())
# sys.exit()

# Read video
cap = cv2.VideoCapture(video_path)
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Write video
out = cv2.VideoWriter(
        'video_with_labels_and_gaze.mp4',
        cv2.VideoWriter_fourcc(*'XVID'),
        cap.get(cv2.CAP_PROP_FPS),
        (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    )

if (cap.isOpened()== False):  
    print("Error opening video file") 
else:
    print("Press Q to quit, P to pause\n") 
    print("Red: must be seen, Blue: may be seen") 

paused = False

# Read until video is completed 
frame_nr = start_frame

# Capture frame-by-frame 
while(cap.isOpened()): 
    key = cv2.waitKey(1) & 0xff

    # quit on Q
    if key == ord('q'):
        break

    # pause on P
    if key == ord('p'):
        paused = not paused

    if paused == False:
        ret, frame = cap.read()

        if ret == True:
            frame_nr = frame_nr + 1
            overlays = df[df['Frame'] == (frame_nr - offset)]
            
            # HIERZO: inladen GP voor tijd (ongeveer) rond hier
            actual_time  = frame_nr / 25
            # print('considering frame {} -> actual time: {}'.format(frame_nr, actual_time))

            # Draw if hazard button is pressed
            found_annotations = df_a[(df_a['frame'] >= frame_nr - 1) & (df_a['frame'] < frame_nr - 1 + 15)]
            print('--- found {} annotations on frame {}'.format(len(found_annotations), frame_nr - 1))

            if len(found_annotations) > 0:
                cv2.rectangle(frame, (450, 0), (1200, 80), (0, 0, 255), -1, 1)
                cv2.putText(frame, "HAZARD BUTTON PRESSED", (500, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4, cv2.LINE_AA);

            # Draw first GPs
            gaze_position_overlays = df_gp[df_gp['frame'] == frame_nr]
            print('found {} gaze positions around frame {}'.format(len(gaze_position_overlays), frame_nr))

            for index, gaze_position in gaze_position_overlays.iterrows():
                if not math.isnan(gaze_position['x']) and not math.isnan(gaze_position['y']):
                    x = gaze_position['x'] + __constants.total_surface_width/2
                    y = 1200 - (gaze_position['y'] + __constants.total_surface_height/2) # change back to "old" coordinate system

                    # print('x: {}, y: {}'.format(x,y))

                    cv2.circle(frame, (int(x), int(y)), 20, (161, 254, 141), -1)

            # print('considering frame {}'.format(frame_nr))
            # print('found {} overlay(s) in data frame'.format(len(overlays)))

            # Draw frame nr on frame
            cv2.rectangle(frame, (0, 0), (400, 80), (255, 255, 255), -1, 1)
            cv2.putText(frame, "Frame: {}".format(frame_nr), (0, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2, cv2.LINE_AA);

            # Draw overlays on frame
            for index, overlay in overlays.iterrows():

                # Since we have "prepared" the aois into the new coordinates
                # calculate this back
                y1 = overlay['y1'] + __constants.total_surface_height/2
                y2 = overlay['y2'] + __constants.total_surface_height/2
                x1 = overlay['x1'] + __constants.total_surface_width/2
                x2 = overlay['x2'] + __constants.total_surface_width/2
                y1 = 1200-y1 # Inverse the y coordinates to match with "old" coordinate system
                y2 = 1200-y2 

                if 'type' in overlay and overlay['type'] == 'may':
                    color = (254, 141, 141)
                    color2 = (254, 10, 10)
                else:
                    color = (141, 141, 254)
                    color2 = (10, 10, 254)

                # Original coordinates
                p1 = (int(x1), int(y1))
                p2 = (int(x2), int(y2))

                cv2.rectangle(frame, (p1[0], p1[1] - 40), (p2[0], p1[1]), color, -1, 1)
                cv2.rectangle(frame, p1, p2, color, 2, 1)

                cv2.putText(frame, "{}".format(overlay['Object ID']), (p1[0], p1[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA);

                # Corrected points
                new_x1, new_x2, new_y1, new_y2 = correct_aoi(x1, x2, y1, y2, overlay['angle'])

                new_p1 = (int(new_x1), int(new_y1))
                new_p2 = (int(new_x2), int(new_y2))

                cv2.rectangle(frame, new_p1, new_p2, color2, 2, 1)

            # Display the resulting frame
            frameToDisplay = ResizeWithAspectRatio(frame, width=FRAME_WIDTH) 


            # comment  this for faster export            
            cv2.imshow('Frame', frameToDisplay) 
            cv2.moveWindow('Frame', 20, 20)

            # Writing the resulting frame
            print('saving frame {}/{}'.format(frame_nr, total_frames))
            out.write(frame)

            # time.sleep(.5)
    
        # Break the loop 
        else:  
            break

cap.release()
out.release()