import cv2, os, argparse, math, copy
import numpy as np
from pathlib import Path

def main():
    # parse the arguments used to call this script
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, help='name of video file', type=str)
    parser.add_argument('--rows', help='How many apriltags on the y-axis', type=int, default=4)
    parser.add_argument('--cols', help='How many apriltags on the x-axis', type=int, default=6)
    parser.add_argument('--default-scale', help='Scale factor all apriltags', type=int, default=3)
    parser.add_argument('--large-scale', help='Scale factor for specific apriltags', type=int, default=3)
    parser.add_argument('--large-scale-indices', help='Indices of the apriltags to enlarge, split by comma', type=str, default=None)
    parser.add_argument('--with-black-background', help='Whether or not to add a black background behind the apriltags in the video', type=bool, default=True)

    args = parser.parse_args()
    src_video = args.name
    rows = args.rows
    cols = args.cols
    scale_factor = args.default_scale
    scale_factor_large = args.large_scale
    with_black_background = args.with_black_background
    large_scale_indices = args.large_scale_indices.split(',') if args.large_scale_indices is not None else []

    # Settings
    tag_family = "tag36h11"
    out_video = 'output/{}_with_apriltags.mp4'.format(os.path.basename(src_video)[:-4])
    out_img = 'output/{}_grid.png'.format(os.path.basename(src_video)[:-4])
    out_img_with_labels = 'output/{}_grid_with_labels.png'.format(os.path.basename(src_video)[:-4])

    # Input video
    cap = cv2.VideoCapture(src_video)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Output video
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_video, fourcc, src_fps, (frame_width,frame_height))

    # Load apriltags codes
    n_images = (cols - 2) * rows + 4 # total apriltags to load
    files = sorted(str(path) for path in Path(tag_family).glob("tag*.png"))
    files = files[0 : n_images]
    images = [cv2.imread(img_file) for img_file in files]
    april_h, april_w, april_c = images[0].shape

    # Create white empty image for composing
    grid_img = 0 * np.ones((frame_height, frame_width, 3), dtype=images[0].dtype)
    grid_img_with_labels = copy.deepcopy(grid_img)
    offsets = {}

    # Determine hor/ver spacing (middle points)
    hor_spacer = frame_width / (cols - 1)
    ver_spacer = frame_height / (rows - 1)

    # Step 1: set the cols (without the corners)
    for col in range(cols - 2):
        x_offset_middle = hor_spacer * (col + 1)

        # first time: top, second time: bottom
        for i in range(2):
            # Select Apriltag and scale
            april_id = col + i * (rows + cols - 4)
            scale = 2**scale_factor_large if str(april_id) in large_scale_indices else 2**scale_factor
            april = cv2.resize(images[april_id], dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            
            # Calculate offsets
            x_offset = math.floor(x_offset_middle - (april_w * scale / 2))
            y_offset = i * (frame_height - april_h * scale)
            
            if x_offset + april_w * scale <= frame_width:
                # Write to grid img
                grid_img[y_offset : y_offset + (april_h * scale), x_offset : x_offset + april_w * scale] = april

                # Add offsets to dict
                offsets[april_id] = (x_offset, y_offset)

                # Write to label img
                writeToImg(grid_img_with_labels, 'ID:{}'.format(april_id), 
                    math.floor(x_offset_middle), (i * frame_height) + 40 - (100 * i))
                writeToImg(grid_img_with_labels, '{},{}'.format(y_offset, x_offset), 
                    math.floor(x_offset_middle), (i * frame_height) + 60 - (100 * i))

    # Step 2: set the rows (without the corners)
    for row in range(rows - 2):
        y_offset_middle = ver_spacer * (row + 1)

        # first time: top, second time: bottom
        for i in range(2):
            # Select April and scale
            april_id = row + cols - 2 + i * (rows + cols - 4)
            scale = 2**scale_factor_large if str(april_id) in large_scale_indices else 2**scale_factor
            april = cv2.resize(images[april_id], dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

            # Calculate offsets
            x_offset = i * (frame_width - april_w * scale)
            y_offset = math.floor(y_offset_middle - (april_h * scale / 2))

            if y_offset + april_h * scale <= frame_height:
                # Write to grid img
                grid_img[y_offset : y_offset + (april_h * scale), x_offset : x_offset + april_w * scale] = april

                # Add offsets to dict
                offsets[april_id] = (x_offset, y_offset)

                # Write to label img
                writeToImg(grid_img_with_labels, 'ID:{}'.format(april_id), 
                    (i * frame_width) + 20 - (140 * i), math.floor(y_offset_middle) + 40)
                writeToImg(grid_img_with_labels, '{},{}'.format(y_offset, x_offset), 
                    (i * frame_width) + 20 - (140 * i), math.floor(y_offset_middle) + 60)

    # Step 3: set the corners
    for i in range(4):
        # Select April and scale
        april_id = (cols - 2) * rows + i
        scale = 2**scale_factor_large if str(april_id) in large_scale_indices else 2**scale_factor
        april = cv2.resize(images[april_id], dsize=None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        
        # Calculate offsets
        if i == 0:
            x_offset, y_offset = (0, 0) # left top
            top, left = (True, True)
        elif i == 1:
            x_offset, y_offset = (0, frame_height - april_h * scale) # left bottom
            top, left = (False, True)
        elif i == 2:
            x_offset, y_offset = (frame_width - april_w * scale, 0) # right top
            top, left = (True, False)
        elif i == 3:
            x_offset, y_offset = (frame_width - april_w * scale, frame_height - april_h * scale) # right bottom
            top, left = (False, False)

        if (x_offset + april_w * scale <= frame_width) and (y_offset + april_h * scale <= frame_height):
            # Write to grid img
            grid_img[y_offset : y_offset + (april_h * scale), x_offset : x_offset + april_w * scale] = april

            # Add offsets to dict
            offsets[april_id] = (x_offset, y_offset)

            # Write to label img
            writeToImg(grid_img_with_labels, 'ID:{}'.format(april_id), 
                20 if left else frame_width-120, 40 if top else frame_height-60)
            writeToImg(grid_img_with_labels, '{},{}'.format(y_offset, x_offset), 
                20 if left else frame_width-120, 60 if top else frame_height-40)

    # Save image with Apriltags
    cv2.imwrite(out_img, grid_img)

    # Save image with Apriltags and labels
    cv2.imwrite(out_img_with_labels, grid_img_with_labels)

    # Start writing to the video
    ok, frame = cap.read()
    fnr = 1
    while ok:
        # Read frame
        ok, frame = cap.read();

        print('{}/{} frames processed'.format(fnr, total_frames), end='\r')

        try:
            # Add a black background to the grid img if instructed to
            if with_black_background:
                for april_id, x_and_y in offsets.items():
                    x_offset, y_offset = x_and_y
                    scale = 2**scale_factor_large if str(april_id) in large_scale_indices else 2**scale_factor
                    cv2.rectangle(frame, (x_offset, y_offset), (x_offset + april_w * scale - 1, y_offset + april_h * scale - 1), (0, 0, 0), -1)

            # Overlay the grid
            out_frame = cv2.add(frame, grid_img)
            out.write(out_frame)
            
            # Save frame and go to next
            fnr += 1
        except:
            print('warning: did not add grid on frame', fnr)

    print('\033[0;32m' + '----------------------------')
    print('we\'re done!')
    print('----------------------------' + '\033[0m')

    cap.release()
    out.release()

def writeToImg(img, label, x, y):
    return cv2.putText(img, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX , .5, (255, 255, 255), 1, cv2.LINE_AA)

if __name__ == "__main__":
    main()