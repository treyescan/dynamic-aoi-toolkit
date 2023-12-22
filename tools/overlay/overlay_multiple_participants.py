import argparse, cv2, sys, math, glob, re
import pandas as pd
import numpy as np
import os.path

sys.path.append('../../')
import __constants
from utils.utils__aois import prepare_aois_df
from utils.utils__margin_calculator import correct_aoi
from utils.utils__resize_with_aspect_ratio import ResizeWithAspectRatio

def eigsorted(cov):
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    return vals[order], vecs[:,order]

# BGR colors
colors = [
    #color alphabet
    (255, 163, 240),
    (220, 117, 0),
    (242, 241, 94),
    (5, 164, 255),
    (72, 206, 43),
    (0, 255, 255),
    (5, 80, 255),
    (143, 153, 0),
    (136, 0, 194),
    (102, 255, 224),
    (153, 204, 255),    
    (49, 92, 0),    
    (255, 10, 116),
    (181, 255, 148),
    (0, 204, 157),
    (187, 168, 255),
    (0, 102, 66),
    (16, 0, 255),
    (0, 0, 153),
    (128, 255, 255),
    (128, 51, 0),   
    (0, 124, 143),
    (0, 63, 153),
    (128, 128, 128),
    (92, 0, 76),   
    (25, 25, 25)
]

# Set window dimensions
FRAME_WIDTH = int(__constants.total_surface_width * 0.2)

# parse the arguments used to call this script
parser = argparse.ArgumentParser()
parser.add_argument('--video', help='path of video file', type=str)
parser.add_argument('--aois', help='path of the AOI csv file', type=str)
parser.add_argument('--m', help='of which measurement moment do we need to plot gaze positions', type=str)
parser.add_argument('--t', help='of which task do we need to plot gaze positions', type=str)
parser.add_argument('--start_frame', help='start playing at frame (0 = start)', type=int, default=0)
parser.add_argument('--ellipse', help='ellipse yes/no', action='store_true')
parser.add_argument('--groupcolors', help='group color by glaucoma yes/no', action='store_true')

args = parser.parse_args()
video_path = args.video
data_path = args.aois
measurement_moment = args.m 
task = args.t
start_frame = args.start_frame
ellips = args.ellipse
groupcolors = args.groupcolors

if(ellips and not groupcolors):
    raise Exception("Ellipses can't be plotted when grouping by colors is not enabled. Either remove --ellips or add --groupcolors as param.")

# Open all gaze position files (gp.csv in {task} folder of all participants)
dfs_gp = {}
dfs_gp_information = {}

pattern = "{}/*/{}/{}/gp.csv".format(__constants.input_folder, measurement_moment, task)
gaze_position_files = glob.glob(pattern)

# Prepare output file
output_file_name = 'gp_overlay_{}_{}.mp4'.format(measurement_moment, task)

for gp_file in gaze_position_files:
    regex = re.findall("(P-[0-9]..)\/(T[0-9])\/([a-zA-Z0-9]*)", gp_file)

    # Get participant ID
    participant_id = regex[0][0] 

    # Read GP csv
    df_gp = pd.read_csv(gp_file)

    # Add participant ID and GP's
    dfs_gp[gp_file] = df_gp
    dfs_gp_information[gp_file] = participant_id

# Read data file
df = pd.read_csv(data_path, header=0)

# Prepare data
df = prepare_aois_df(df)

# Read video
cap = cv2.VideoCapture(video_path)
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Write video
out = cv2.VideoWriter(
    output_file_name,
    cv2.VideoWriter_fourcc(*'XVID'),
    cap.get(cv2.CAP_PROP_FPS),
    (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
)

# Try to open video
if (cap.isOpened()== False):  
    print("Error opening video file") 
else:
    print("Press Q to quit, P to pause\n") 
    print("RED BOX: must be seen, BLUE BOX: may be seen") 

    if(groupcolors):
        print("RED DOT/ELLIPS = Glaucoma, BLUE DOT/ELLIPS = Control")

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
            overlays = df[df['Frame'] == (frame_nr)]
        
            # Draw first GPs
            gp_index = 0

            g_x = []
            g_y = []
            c_x = []
            c_y = []

            for key, df_gp in dfs_gp.items():
                if('frame' in df_gp.columns):
                    gaze_position_overlays = df_gp[df_gp['frame'] == frame_nr]
                    # print('found {} gaze positions around frame {}'.format(len(gaze_position_overlays), frame_nr))

                    # set color
                    color = colors[gp_index % len(colors)]

                    # if --groupcolors, check 
                    # if G or C file exists in participant folder
                    # change the colors accordlingly 
                    if groupcolors:
                        # default case
                        isGlaucomaGP = False
                        color = (255, 90, 90)

                        participant_id = dfs_gp_information[key]

                        if os.path.isfile(f'{__constants.input_folder}/{participant_id}/glaucoma'):
                            isGlaucomaGP = True
                            # print('Glaucoma patient')
                            color = (90, 90, 255)

                    # flag to see if we have printed the label, we should do this once per frame per colored circle
                    printed_label = False 

                    for index, gaze_position in gaze_position_overlays.iterrows():
                        if not math.isnan(gaze_position['x']) and not math.isnan(gaze_position['y']):
                            x = gaze_position['x'] + __constants.total_surface_width/2
                            y = __constants.total_surface_height - (gaze_position['y'] + __constants.total_surface_height/2)

                            cv2.circle(frame, (int(x), int(y)), 20, color, -1)

                            if not printed_label:
                                cv2.putText(frame, participant_id, (int(x), int(y)+50), \
                                    cv2.FONT_HERSHEY_SIMPLEX, .8, color, 2, cv2.LINE_AA);
                                printed_label = True

                            if groupcolors:
                                if isGlaucomaGP:
                                    g_x.append(int(x))
                                    g_y.append(int(y))
                                else:
                                    c_x.append(int(x))
                                    c_y.append(int(y))
                            
                    gp_index = gp_index + 1

            if ellips:
                # Draw ellipses
                # print(g_x, g_y)
                # print(c_x, c_y)
                nstd = 1

                # Draw ellipse around control data
                if(len(c_x) > 0 and len(c_y) > 0):
                    c_cov = np.cov(c_x, c_y)
                    c_vals, c_vecs = eigsorted(c_cov)
                    c_theta = np.degrees(np.arctan2(*c_vecs[:,0][::-1]))
                    # c_w, c_h = 2 * nstd * np.sqrt(c_vals)
                    c_w = nstd * np.std(c_x)
                    c_h = nstd * np.std(c_y)
                    c_center = (int(np.mean(c_x)), int(np.mean(c_y)))
                    c_axesLength = (int(c_w), int(c_h))
                    cv2.ellipse(frame, c_center, c_axesLength, c_theta, 0, 360, (255, 0, 0), 20)

                # Draw ellipse around glaucoma data
                if(len(g_x) > 0 and len(g_y) > 0):
                    g_cov = np.cov(g_x, g_y)
                    g_vals, g_vecs = eigsorted(g_cov)
                    g_theta = np.degrees(np.arctan2(*g_vecs[:,0][::-1]))
                    # g_w, g_h = 2 * nstd * np.sqrt(g_vals)
                    g_w = nstd * np.std(g_x)
                    g_h = nstd * np.std(g_y)
                    g_center = (int(np.mean(g_x)), int(np.mean(g_y)))
                    g_axesLength = (int(g_w), int(g_h))
                    cv2.ellipse(frame, g_center, g_axesLength, g_theta, 0, 360, (0, 0, 255), 20)

            # Draw frame nr on frame
            cv2.rectangle(frame, (0, 0), (400, 80), (255, 255, 255), -1, 1)
            cv2.putText(frame, "Frame: {}".format(frame_nr), (0, 50), \
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2, cv2.LINE_AA);

            # Draw overlays on frame
            for index, overlay in overlays.iterrows():

                # Since we have "prepared" the aois into the new coordinates calculate this back
                y1 = overlay['y1'] + __constants.total_surface_height/2
                y2 = overlay['y2'] + __constants.total_surface_height/2
                x1 = overlay['x1'] + __constants.total_surface_width/2
                x2 = overlay['x2'] + __constants.total_surface_width/2
                y1 = __constants.total_surface_height-y1 # Inverse the y coordinates to match with "old" coordinate system
                y2 = __constants.total_surface_height-y2 

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
                cv2.rectangle(frame, p1, p2, color, 5, 1)

                cv2.putText(frame, "{}".format(overlay['Object ID']), (p1[0], p1[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA);

                # Corrected points
                new_x1, new_x2, new_y1, new_y2 = correct_aoi(x1, x2, y1, y2, overlay['angle'])

                new_p1 = (int(new_x1), int(new_y1))
                new_p2 = (int(new_x2), int(new_y2))

                cv2.rectangle(frame, new_p1, new_p2, color2, 5, 1)

            # Display the resulting frame
            frameToDisplay = ResizeWithAspectRatio(frame, width=FRAME_WIDTH) 

            # comment  this for faster export            
            cv2.imshow('Frame', frameToDisplay) 
            cv2.moveWindow('Frame', 20, 20)

            # Writing the resulting frame
            # print('saving frame {}/{}'.format(frame_nr, total_frames))
            out.write(frame)

            # time.sleep(.5)

            # Increase the frame number to go to the next frame
            frame_nr = frame_nr + 1
    
        # Break the loop 
        else:  
            break

cap.release()
out.release()