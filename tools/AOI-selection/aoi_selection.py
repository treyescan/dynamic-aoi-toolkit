import cv2, os, sys, time, argparse, glob
from csv import writer

sys.path.append('../../')
import __constants

# Original video dimensions
VIDEO_WIDTH = __constants.total_surface_width
VIDEO_HEIGHT = __constants.total_surface_height

# Set window dimensions
FRAME_WIDTH = int(__constants.total_surface_width * 0.2)
FRAME_HEIGHT = int(__constants.total_surface_height * 0.2)

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    # parse the arguments used to call this script
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', required=True, help='name of video file', type=str)
    parser.add_argument('--step', help='How many frames to skip in between', type=float, default=40)
    parser.add_argument('--start_frame', help='Starting frame (first = 0)', type=float, default=1)
    parser.add_argument('--max_frames', help='Maximum number of frames processed', type=int, default=10000)
    parser.add_argument('--output_file', help='Filename', type=str, default="output.csv")
    parser.add_argument("--manual", type=str2bool, nargs='?', const=True, default=False, help="Do you want to select all frames manually?")

    args = parser.parse_args()
    start_frame = args.start_frame
    max_frames = args.max_frames
    video_name = args.video
    step = args.step
    manual = args.manual

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

    # Prepare output file name, we'll show it multiple times for convenience
    output_file_name = generate_file_name(given_label)

    # Get all AOI's on specific frames (store those in a dictionary)
    selected_aois = aoi_selection(video_name, start_frame, step, max_frames, manual)

    # At least 2 AOI's must have been selected
    if len(selected_aois) < 2:
        print('Not computed! Select at least 2 regions of interests')
        return

    # Compute the "in between" aois
    computed_aois = compute_transition_aois(selected_aois)

    # Save the computed aois to a csv
    save_to_csv(output_file_name, computed_aois, start_frame, must_or_may, category)

    # Playback the aois for a visual check
    playback_aois(video_name, selected_aois, computed_aois, output_file_name, start_frame)

    # Do we really want to save the video?
    save_video_confirmation(output_file_name)

# Start the selection process
def aoi_selection(file, start_frame, step, max_frames, manual):
    cap = cv2.VideoCapture(file)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    ok, frame = cap.read()

    selected_aois = {}

    frames = 0
    while ok and frames <= max_frames:
        # Resize frame and position the window
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Without waiting at least 1ms for a key press, the image would not be shown
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        # When hitting S, the video will pause and we may select a AOI for that frame
        if key == ord("s") or frames == 0 or manual:
            cv2.putText(frame, "Selecting AOI on frame {} and/or hit [space] to continue.".format(frames), (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);
            
            aoiBB = cv2.selectAOI('frame', frame, fromCenter=False) 

            if not (aoiBB[2] == 0 or aoiBB[3] == 0): # if no width or height
                selected_aois[frames] = aoiBB;
        else:
            cv2.putText(frame, "Hit [s] to select another AOI or hit [q] to compute & quit.", (30, 30), 
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

    return selected_aois

# Compute the AOI's in between our selected AOI's
def compute_transition_aois(selected_aois):
    frame_of_first_aoi = list(selected_aois.keys())[0]
    frame_of_last_aoi = list(selected_aois.keys())[-1]
    frame_range = range(frame_of_first_aoi, frame_of_last_aoi + 1)

    # a dict to store all aois
    computed_aois = {}

    # the first 'previous' aoi is the first aoi
    previous_selected_frame = frame_of_first_aoi
    next_selected_frame = find_next_frame_with_aoi(frame_of_first_aoi, selected_aois)

    for frame in frame_range:
        if frame in selected_aois:
            # we selected in manually
            computed_aois[frame] = selected_aois[frame]

            # for all upcoming AOI's, this AOI is the previous one
            previous_selected_frame = frame
            next_selected_frame = find_next_frame_with_aoi(previous_selected_frame, selected_aois)
        else:
            # use next and previous selected aoi

            if(next_selected_frame is not None):
                # print('van {} -> {}'.format(previous_selected_frame, next_selected_frame))

                prev_frame = previous_selected_frame
                next_frame = next_selected_frame
                prev_aoi = selected_aois[prev_frame]
                next_aoi = selected_aois[next_frame]
                total_frames_between_aois = next_frame - prev_frame + 1
                
                # AOI: x,y,w,h
                computed_aois[frame] = (
                    calc_transition_values(0, prev_aoi, next_aoi, prev_frame, frame, total_frames_between_aois),
                    calc_transition_values(1, prev_aoi, next_aoi, prev_frame, frame, total_frames_between_aois),
                    calc_transition_values(2, prev_aoi, next_aoi, prev_frame, frame, total_frames_between_aois),
                    calc_transition_values(3, prev_aoi, next_aoi, prev_frame, frame, total_frames_between_aois),
                )

    # Display the computed AOI's to the console
    for fnr in computed_aois:
        if fnr in selected_aois:
            print('{}: {} <- manually selected'.format(fnr, computed_aois[fnr]))
        else:
            print('{}: {}'.format(fnr, computed_aois[fnr]))

    return computed_aois

# find the next selected AOI and return it
def find_next_frame_with_aoi(previous_key, selected_aois):
    temp = list(selected_aois) 
    try: 
        res = temp[temp.index(previous_key) + 1] 
    except (ValueError, IndexError): 
        res = None
    return res

# calculate transition bb values
def calc_transition_values(key, prev_aoi, next_aoi, prev_frame, frame, total_frames_between_aois):
    return int(round((next_aoi[key] - prev_aoi[key])*((frame - prev_frame)/total_frames_between_aois)+prev_aoi[key]))

# to check if we had done it right, show the computed aois over the video
def playback_aois(file, selected_aois, computed_aois, output_file_name, start_frame):
    cap = cv2.VideoCapture(file)

    frame_of_first_aoi = list(selected_aois.keys())[0]
    frame_of_last_aoi = list(selected_aois.keys())[-1]

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_of_first_aoi + start_frame)

    ok, frame = cap.read()

    frames = frame_of_first_aoi
    while ok and frames <= (frame_of_last_aoi):

        # Resize frame and position the window
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Without waiting at least 1ms for a key press, the image would not be shown
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            sys.exit()

        # Draw over the frame
        # this is for drawing the box on the screen
        aoiBB = computed_aois[frames]
        print("Recapping computed aois for frame {}".format(frames))

        p1 = (int(aoiBB[0]), int(aoiBB[1]))
        p2 = (int(aoiBB[0] + aoiBB[2]), int(aoiBB[1] + aoiBB[3]))

        if(frames in selected_aois):
            color = (0, 0, 255)
            cv2.putText(frame, "Selected BB for frame {}: {} (coordinates are scaled to video)".format(frames, aoiBB), (30, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA);
        else:
            color = (255,0,0)
            cv2.putText(frame, "Computed BB for frame {}: {} (coordinates are scaled to video)".format(frames, aoiBB), (30, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA);

        cv2.rectangle(frame, p1, p2, color, 5, 1)

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
def save_to_csv(output_file_name, computed_aois, start_frame, must_or_may, category):
    label = output_file_name.replace('output/', '').replace('.csv', '')
    csv_file = output_file_name

    with open(csv_file, 'w', newline='') as write_obj:
        csv_writer = writer(write_obj)
        csv_writer.writerow(['Frame','Object ID', 'category', 'x1','x2','y1','y2', 'type'])

        for fnr in computed_aois:
            aoi = computed_aois[fnr]

            # Save the csv values, scaled to the original video
            x1 = int(round(aoi[0]/FRAME_WIDTH * VIDEO_WIDTH))
            y1 = int(round(aoi[1]/FRAME_WIDTH * VIDEO_WIDTH))
            x2 = int(round(x1 + aoi[2]/FRAME_WIDTH * VIDEO_WIDTH))
            y2 = int(round(y1 + aoi[3]/FRAME_WIDTH * VIDEO_WIDTH))

            csv_writer.writerow([
                (fnr + start_frame), 
                label, category, x1, x2, y1, y2,
                ('must' if must_or_may == 1 else 'may')
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