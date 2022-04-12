# adaptation of Video_bbox by sachinruk
# @see: https://github.com/sachinruk/Video_bbox

import cv2, os, sys, argparse, glob
from csv import writer

sys.path.append('../../')
import __constants

# Original video dimensions
VIDEO_WIDTH = __constants.total_surface_width
VIDEO_HEIGHT = __constants.total_surface_height

# Set window dimensions
FRAME_WIDTH = int(__constants.total_surface_width * 0.2)
FRAME_HEIGHT = int(__constants.total_surface_height * 0.2)

# parse the arguments used to call this script
parser = argparse.ArgumentParser()
parser.add_argument('--video', help='name of video file', type=str)
parser.add_argument('--max_obj', help='Maximum number of objects followed', type=int, default=6)
parser.add_argument('--max_frames', help='Maximum number of frames processed', type=int, default=10000)
parser.add_argument('--thresh', help='Threshold for scene changes', type=float, default=2)
parser.add_argument('--start_frame', help='Starting frame (first = 0)', type=float, default=1)
parser.add_argument('--output_file', help='Filename', type=str, default="output.csv")

args = parser.parse_args()
max_obj = args.max_obj
max_frames = args.max_frames
thresh = args.thresh
start_frame = args.start_frame
may_play=True

# QUESTIONS
# Label?
given_label = input("What is the label of the tracked object? ")
if(given_label ==  ''):
    print('invalid input')
    sys.exit()

# What is the category?
category = input('What is the category? ')
if(category == ''): 
    print('invalid input')
    sys.exit()

# Must or may?
must_or_may = int(input("Before we start: are you tracking a must or may be seen object? \n 1: must-be-seen, 2: may-be-seen \n"))
if(must_or_may != 1 and must_or_may != 2):
    print('invalid input')
    sys.exit()

# generate correct file identifier

# step 1: check if files with same label already exist in output/
found_files = glob.glob("output/" + given_label + "_*.csv")
found_ids = []

for file in found_files:
    sanitized_string = file.replace('output/' + given_label + '_', '')
    sanitized_string = sanitized_string.replace('.csv', '')
    found_ids.append(int(sanitized_string))

# sort ascending
found_ids = sorted(found_ids)

if len(found_ids) == 0:
    # in this case, we didnt find any files
    unique_id = 1
else:
    # in this case, we did find files
    last_found_id = found_ids[-1]
    unique_id = last_found_id + 1

# Generate unique ID (incremented from last known ID) and create file name
unique_label = given_label + '_' + str(unique_id)
output_file_name = 'output/' + unique_label + '.csv'

fname =  os.path.basename(args.video)[:-4] #filename without extentsion
video = cv2.VideoCapture(args.video) # Read video

# Create csv with headers
csv_file = output_file_name
with open(csv_file, 'w', newline='') as write_obj:
    csv_writer = writer(write_obj)
    csv_writer.writerow(['Frame','Object ID', 'category', 'x1','x2','y1','y2', 'type'])

print('\033[0;32m' + '----------------------------')
print('saving results to ' + output_file_name)
print('----------------------------' + '\033[0m')

# Exit if video not opened
if not video.isOpened():
    print("Could not open video")
    may_play = False
 
# Set starting frame number from args
video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

# Read first frame
ok,frame = video.read()
if not ok:
    print("Cannot read video file")
    may_play = False

h = FRAME_HEIGHT
w = FRAME_WIDTH
initBB = None

frames = 0
prev_mean = 0

cv2.namedWindow("Frame")
cv2.startWindowThread()

# also, close before
if cv2.waitKey(1) & 0xFF == ord("q"):
    may_play = False

while ok and frames <= max_frames and may_play:
    frame_diff = abs(frame.mean() - prev_mean)
    prev_mean = frame.mean()

    frame = cv2.resize(frame, (w, h))
    name = fname + '_' + str(frames).zfill(4)
    origFrame = frame.copy()
    
    key = cv2.waitKey(1) & 0xFF

    # always close if the q is hit
    if key == ord("q"):
        may_play = False

    # if the 's' key is selected, we are going to "select" a bounding
    # box to track
    if key == ord("s") or frames == 0 or frame_diff > thresh:
        trackers = cv2.legacy.MultiTracker_create()
        for i in range(max_obj):
            # select the bounding box of the object we want to track (make
            # sure you press ENTER or SPACE after selecting the AOI)
            initBB = cv2.selectAOI("Frame", frame, fromCenter=False) 
            # create a new object tracker for the bounding box and add it
            # to our multi-object tracker
            if initBB[2] == 0 or initBB[3] == 0: # if no width or height
                break
            # # start OpenCV object tracker using the supplied bounding box
            tracker = cv2.legacy.TrackerCSRT_create()
            trackers.add(tracker, frame, initBB)

    if initBB is not None:
        (tracking_ok, boxes) = trackers.update(frame)

        # save image and bounding box
        if tracking_ok:
            if len(boxes) > 0: # if there is a box that is being tracked
                with open(csv_file, 'a+', newline='') as write_obj:
                    for index, bbox in enumerate(boxes):

                        # get the relative x and y of the points
                        #(x, y, w, h) = bbox;
                        p1 = (int(bbox[0]), int(bbox[1]))
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))

                        x1rel = (p1[0]/w)
                        x2rel = (p2[0]/w)
                        y1rel = (p1[1]/h)
                        y2rel = (p2[1]/h)

                        # this is for drawing the box on the screen
                        screen_bbox_p1 = (int(x1rel*FRAME_WIDTH), int(y1rel*FRAME_HEIGHT))
                        screen_bbox_p2 = (int(x2rel*FRAME_WIDTH), int(y2rel*FRAME_HEIGHT))
                        cv2.rectangle(frame, screen_bbox_p1, screen_bbox_p2, (255,0,0), 2, 1)

                        # this is for us, making a csv
                        x1 = (x1rel*VIDEO_WIDTH)
                        x2 = (x2rel*VIDEO_WIDTH)
                        y1 = (y1rel*VIDEO_HEIGHT)
                        y2 = (y2rel*VIDEO_HEIGHT)
 
                        csv_writer = writer(write_obj)
                        csv_writer.writerow([                   
                            (frames + start_frame),         
                            unique_label, category,
                            x1, x2, y1, y2, ('must' if must_or_may == 1 else 'may')
                        ])

        else:
            initBB = None

    cv2.imshow("Frame", frame)

    ok,frame = video.read()
    frames += 1

# Close all
video.release()
cv2.destroyWindow("Frame")
cv2.waitKey(1)

print("\n");
may_save = input("Do you want to save a csv? The default is (Y)es, type n to remove. [Y/n]\n");

if(may_save.lower() == 'n'):
    print("Okay, we are removing the file")
    os.remove(output_file_name);
else:
    print("Okay, done!")
