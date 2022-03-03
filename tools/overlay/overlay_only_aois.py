import argparse, cv2, sys
import pandas as pd

sys.path.append('../../')
from utils.utils__resize_with_aspect_ratio import ResizeWithAspectRatio

# parse the arguments used to call this script
parser = argparse.ArgumentParser()
parser.add_argument('--video', help='path of video file', type=str)
parser.add_argument('--aois', help='path of the aois file', type=str)
parser.add_argument('--start_frame', help='start playing at frame', type=int, default=0)

args = parser.parse_args()
video_path = args.video
data_path = args.aois
start_frame = args.start_frame

# Read data file
df = pd.read_csv(data_path, header=0)

# Read video
cap = cv2.VideoCapture(video_path)
cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Write video
out = cv2.VideoWriter(
    'video_with_labels.mp4',
    cv2.VideoWriter_fourcc(*'XVID'),
    cap.get(cv2.CAP_PROP_FPS),
    (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
)

# Try to open video
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
            overlays = df[df['Frame'] == frame_nr]

            # Draw frame nr on frame
            cv2.rectangle(frame, (0, 0), (400, 80), (255, 255, 255), -1, 1)
            cv2.putText(frame, "Frame: {}".format(frame_nr), (0, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2, cv2.LINE_AA);

            # Draw overlays on frame
            for index, overlay in overlays.iterrows():
                p1 = (int(overlay['x1']), int(overlay['y1']))
                p2 = (int(overlay['x2']), int(overlay['y2']))

                color = (0, 0, 255)
                if 'type' in overlay and overlay['type'] == 'may':
                    color = (255, 0, 0)

                cv2.rectangle(frame, (p1[0], p1[1] - 40), (p2[0], p1[1]), color, -1, 1)
                cv2.rectangle(frame, p1, p2, color, 5, 1)

                cv2.putText(frame, "{}".format(overlay['Object ID']), (p1[0], p1[1] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA);

            # Display the resulting frame
            frameToDisplay = ResizeWithAspectRatio(frame, width=1280) 
            cv2.imshow('Frame', frameToDisplay) 
            cv2.moveWindow('Frame', 20, 20)

            # Writing the resulting frame
            print('saving frame {}/{}'.format(frame_nr, total_frames))
            out.write(frame)

            # time.sleep(.5)

            # Increase the frame number to go to the next frame
            frame_nr = frame_nr + 1
    
        # Break the loop 
        else:  
            break

cap.release()
out.release()