import cv2, os, sys
import argparse
from csv import writer
import glob
import time

# Original video dimensions
VIDEO_WIDTH = 5760
VIDEO_HEIGHT = 1200

# Set window dimensions
FRAME_WIDTH = int(2880 * 0.4)
FRAME_HEIGHT = int(600 * 0.4)

def main():
    # parse the arguments used to call this script
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, help='name of video file', type=str)
    # parser.add_argument('--label', required=True, help='label of tracked object', type=str)
    parser.add_argument('--step', help='How many frames to skip in between', type=float, default=40)
    parser.add_argument('--start-frame', help='Starting frame (first = 0)', type=float, default=1)
    parser.add_argument('--max-frames', help='Maximum number of frames processed', type=int, default=10000)
    parser.add_argument('--output_file', help='Filename', type=str, default="output.csv")

    args = parser.parse_args()
    start_frame = args.start_frame
    max_frames = args.max_frames
    # given_label = args.label
    video_name = args.name
    step = args.step

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

    # How many CBR MUST 
    CBR_MUST = input('How many CBR MUST ? ')
    if(CBR_MUST == ''):    
        print('invalid input')
        sys.exit()

    # How many CBR MAY
    CBR_MAY = input('How many CBR MAY? ')
    if(CBR_MAY == ''): 
        print('invalid input')
        sys.exit()

    # How many drivers MUST 
    drivers_MUST = input('How many drivers MUST ? ')
    if(drivers_MUST == ''):    
        print('invalid input')
        sys.exit()

    # How many drivers MAY
    drivers_MAY = input('How many drivers MAY? ')
    if(drivers_MAY == ''): 
        print('invalid input')
        sys.exit()

    # Prepare output file name, we'll show it multiple times for convenience
    output_file_name = generate_file_name(given_label)

    # Get all ROI's on specific frames (store those in a dictionary)
    selected_rois = roi_selection(video_name, start_frame, step, max_frames)

    # At least 2 ROI's must have been selected
    if len(selected_rois) < 2:
        print('Not computed! Select at least 2 regions of interests')
        return

    # Compute the "in between" rois
    computed_rois = compute_transition_rois(selected_rois)

    # Save the computed rois to a csv
    save_to_csv(output_file_name, computed_rois, start_frame, must_or_may, CBR_MUST, CBR_MAY, drivers_MUST, drivers_MAY, category)

    # Playback the rois for a visual check
    playback_rois(video_name, selected_rois, computed_rois, output_file_name, start_frame)

    # Do we really want to save the video?
    save_video_confirmation(output_file_name)

# Start the selection process
def roi_selection(file, start_frame, step, max_frames):
    cap = cv2.VideoCapture(file)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    ok, frame = cap.read()

    selected_rois = {}

    frames = 0
    while ok and frames <= max_frames:
        # Resize frame and position the window
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Without waiting at least 1ms for a key press, the image would not be shown
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        # When hitting S, the video will pause and we may select a ROI for that frame
        if key == ord("s") or frames == 1:
            cv2.putText(frame, "Selecting ROI on frame {} and/or hit [space] to continue.".format(frames - 1), (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);
            
            roiBB = cv2.selectROI('frame', frame, fromCenter=False) 

            if not (roiBB[2] == 0 or roiBB[3] == 0): # if no width or height
                selected_rois[frames - 1] = roiBB;
        else:
            cv2.putText(frame, "Hit [s] to select another ROI or hit [q] to compute & quit.", (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);

        # Show the frame
        cv2.imshow('frame', frame)

        # Go to next frame
        time.sleep(.2)
        ok, frame = cap.read();
        frames += 1

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    return selected_rois

# Compute the ROI's in between our selected ROI's
def compute_transition_rois(selected_rois):
    frame_of_first_roi = list(selected_rois.keys())[0]
    frame_of_last_roi = list(selected_rois.keys())[-1]
    frame_range = range(frame_of_first_roi, frame_of_last_roi + 1)

    # print('frame of first roi: {}'.format(frame_of_first_roi))
    # print('frame of last roi: {}'.format(frame_of_last_roi))

    # a dict to store all rois
    computed_rois = {}

    # the first 'previous' roi is the first roi
    previous_selected_frame = frame_of_first_roi
    next_selected_frame = find_next_frame_with_roi(frame_of_first_roi, selected_rois)

    for frame in frame_range:
        if frame in selected_rois:
            # we selected in manually
            computed_rois[frame] = selected_rois[frame]

            # for all upcoming ROI's, this ROI is the previous one
            previous_selected_frame = frame
            next_selected_frame = find_next_frame_with_roi(previous_selected_frame, selected_rois)
        else:
            # use next and previous selected roi

            if(next_selected_frame is not None):
                # print('van {} -> {}'.format(previous_selected_frame, next_selected_frame))

                prev_frame = previous_selected_frame
                next_frame = next_selected_frame
                prev_roi = selected_rois[prev_frame]
                next_roi = selected_rois[next_frame]
                total_frames_between_rois = next_frame - prev_frame + 1
                
                # ROI: x,y,w,h
                computed_rois[frame] = (
                    calc_transition_values(0, prev_roi, next_roi, prev_frame, frame, total_frames_between_rois),
                    calc_transition_values(1, prev_roi, next_roi, prev_frame, frame, total_frames_between_rois),
                    calc_transition_values(2, prev_roi, next_roi, prev_frame, frame, total_frames_between_rois),
                    calc_transition_values(3, prev_roi, next_roi, prev_frame, frame, total_frames_between_rois),
                )

    # Display the computed ROI's to the console
    for fnr in computed_rois:
        if fnr in selected_rois:
            print('{}: {} <- manually selected'.format(fnr, computed_rois[fnr]))
        else:
            print('{}: {}'.format(fnr, computed_rois[fnr]))

    return computed_rois

# find the next selected ROI and return it
def find_next_frame_with_roi(previous_key, selected_rois):
    temp = list(selected_rois) 
    try: 
        res = temp[temp.index(previous_key) + 1] 
    except (ValueError, IndexError): 
        res = None
    return res

# calculate transition bb values
def calc_transition_values(key, prev_roi, next_roi, prev_frame, frame, total_frames_between_rois):
    return int(round((next_roi[key] - prev_roi[key])*((frame - prev_frame)/total_frames_between_rois)+prev_roi[key]))

# to check if we had done it right, show the computed rois over the video
def playback_rois(file, selected_rois, computed_rois, output_file_name, start_frame):
    cap = cv2.VideoCapture(file)

    frame_of_first_roi = list(selected_rois.keys())[0]
    frame_of_last_roi = list(selected_rois.keys())[-1]

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_of_first_roi + start_frame)

    ok, frame = cap.read()

    frames = frame_of_first_roi
    while ok and frames <= (frame_of_last_roi):

        # Resize frame and position the window
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Without waiting at least 1ms for a key press, the image would not be shown
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            sys.exit()

        # Draw over the frame
        # this is for drawing the box on the screen
        roiBB = computed_rois[frames]
        print("Recapping computed rois for frame {}".format(frames))

        p1 = (int(roiBB[0]), int(roiBB[1]))
        p2 = (int(roiBB[0] + roiBB[2]), int(roiBB[1] + roiBB[3]))

        if(frames in selected_rois):
            color = (0, 0, 255)
            cv2.putText(frame, "Selected BB for frame {}: {} (coordinates are scaled to video)".format(frames, roiBB), (30, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA);
        else:
            color = (255,0,0)
            cv2.putText(frame, "Computed BB for frame {}: {} (coordinates are scaled to video)".format(frames, roiBB), (30, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);

        cv2.rectangle(frame, p1, p2, color, 2, 1)

        # Show the output file location
        cv2.putText(frame, "Results already saved to {}. Hit [q] to exit.".format(output_file_name), (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);

        # Show the frame
        cv2.imshow('frame', frame)

        # Go to next frame
        time.sleep(.1)
        ok, frame = cap.read();
        frames += 1

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

# Generate a filename, based on the files in output/
def generate_file_name(given_label):
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

    unique_label = given_label + '_' + str(unique_id)
    return 'output/' + unique_label + '.csv'

# Save the csv
def save_to_csv(output_file_name, computed_rois, start_frame, must_or_may, CBR_MUST, CBR_MAY, drivers_MUST, drivers_MAY, category):
    label = output_file_name.replace('output/', '').replace('.csv', '')
    csv_file = output_file_name

    with open(csv_file, 'w', newline='') as write_obj:
        csv_writer = writer(write_obj)
        csv_writer.writerow(['Frame','Object ID', 'category', 'x1','x2','y1','y2', 'type', 'CBR_MUST', 'CBR_MAY', 'drivers_MUST', 'drivers_MAY'])

        for fnr in computed_rois:
            roi = computed_rois[fnr]

            # Save the csv values, scaled to the original video
            x1 = int(round(roi[0]/FRAME_WIDTH * VIDEO_WIDTH))
            y1 = int(round(roi[1]/FRAME_WIDTH * VIDEO_WIDTH))
            x2 = int(round(x1 + roi[2]/FRAME_WIDTH * VIDEO_WIDTH))
            y2 = int(round(y1 + roi[3]/FRAME_WIDTH * VIDEO_WIDTH))

            csv_writer.writerow([
                (fnr + start_frame + 1), 
                label, category, x1, x2, y1, y2,
                ('must' if must_or_may == 1 else 'may'),
                CBR_MUST, CBR_MAY, drivers_MUST, drivers_MAY
            ])
    
    print('\033[0;32m' + '----------------------------')
    print('saving results to ' + output_file_name)
    print('----------------------------' + '\033[0m')

# Remove the csv file if we do not want to save it
def save_video_confirmation(output_file_name):
    print("\n");
    may_save = input("Do you want to save a csv? The default is (Y)es, type n to remove. [Y/n]\n");

    if(may_save.lower() == 'n'):
        print("Okay, we are removing the file")
        os.remove(output_file_name);
    else:
        print("Okay, done!")

if __name__ == "__main__":
    main()