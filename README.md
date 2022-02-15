# Dynamic AOI Toolkit

This toolkit includes tools to measure widescreen, dynamic, areas of interests (AOI) based on the Pupil Labs Core eye tracker data. The tools built include an (1) AOI selector (both automatic and manual), a tool to (2) overlay AOI's on the stimuli (videos) and (3) AOI hit detection.

## Table of Contents

TODO: (joris) links maken van TOC

1. Installation
1. Usage
   1. AOI Selector
      1. Method 1: Tracking objects semi-automatically
      1. Method 2: Selection ROI
      1. Combining the AOI Selector output
   1. AOI Overlay
      1. Overlaying ROIS and gaze positions over a video
      1. Overlaying ROIS over a video
   1. AOI Hit detection
1. Contribution
1. License

## Installation

To use the toolkit, make sure python3 is installed. To use the install the latest version of this toolkit, use:

```bash
git clone git@github.com:treyescan/dynamic-aoi-toolkit.git

pip3 install -m requirements.txt
```

## Usage

### 1. AOI Selector

The goal of the AOI Selector is to translate humanly-identified MUST/MAY be seen hazards to data files. This can be done semi-automatically or manually. Both methods can be used intertwined, after which we can comnine the data files. We can check the data files by overlaying the csv files over a video.

#### Method 1: Tracking objects semi-automatically

```bash
python3 object_tracking.py --name="video.mp4" --start_frame=70
```

**Usage:**

1. Run the command above, replacing `vid.mp4` with the path to your video
1. The video will open a preview screen
1. If you want to select an object to track from the first frame, draw a box on the video
1. If not: hint `[enter]` to play the video, hit `[s]` when you want to select an object
1. The video starts playing and shows the tracked object. In this state, the results are directly saved to your output csv
1. When you're done, stop the script by hitting `[q]`

#### Method 2: Selection ROI

```bash
python3 roi_selection.py --name="video.mp4" --start-frame=100
```

**Usage:**

1. Run the command above, replacing `videos/vid.mp4` with the path to your video
1. The video will open a preview screen
1. If you want to select a ROI from the first frame
1. If not: hint `[enter]` to play the video, hit `[s]` when you want to select a ROI
1. The video starts playing **without** showing the ROI. when you want to select a new ROI, hit `[s]`
1. When you're done, stop the script by hitting `[q]`
1. The script will print the selected bounding boxes to the console and calculate the coordinates of the ROI in between
1. The script will show you the computed ROI's by showing the video again and save it to the output file.

#### Combining the AOI Selector output

```bash
python3 concat_files.py --folder data/testvideo
```

1. Make sure all output files from script 1 and 2 are saved in one folder
1. Run the command above, replacing `data/testvideo` with the path to your output folder
1. The files will be concatenated to a single file. The console will show you the path of this file

### 2. AOI Overlay

TODO:

#### Overlaying ROIS and gaze positions over a video

```bash
# for one participant
python3 overlay_with_roi_and_gaze.py --video="../inputs/Deel1.mp4" --data="../rois/deel1.csv" --participant="../../pilot-data/P-022/Deel1" --start_frame=800

# for multiple participants
python3 overlay_multiple_participants.py --video="../inputs/Deel1.mp4" --data="../rois/deel1.csv" --deel="Deel1" --start_frame=800
```

#### Overlaying ROIS over a video

```bash
python3 overlay_with_rois.py --video="../inputs/Deel1.mp4" --data="../rois/deel1.csv" --start_frame=1000
```

**Usage**

- Run the command above
- The video will be outputted to `video_with_labels.mp4` in the same folder
- Make sure to move this video before creating a new video
- NB: video processing make take a while since every frame has to be processed at full resolution

### 3. AOI Hit detection

TODO:

```bash
python3 analyse.py
```

**Usage**

1. TODO:

## 3. Contribution

[Issues](https://github.com/treyescan/dynamic-aoi-toolkit/issues/new) and other contributions are welcome.

## 4. License

This toolkit is licsensed under [GNU GENERAL PUBLIC LICENSE V3](/LICENSE)
