## Data folders (see 1. Data structure in the README)
data_folder = '/Users/treyescan/development/dynamic-aoi-toolkit/data'
input_folder = '{}/input-gp'.format(data_folder)
output_folder = '{}/output'.format(data_folder)

## Frame rate of task video
frame_rate = 25 # fps

## Screen dimensions
total_surface_width = 5760 # in px
total_surface_height = 1200 # in px
screen_middle_y = 600 # in px
screen_middle_x = 2880 # in px

## Physical setup
distance_to_screen = 65 # distance to screen in cm 
ppi = 94.34 # px per inch (monitor specification)
ppc = ppi/2.54 # px per cm
z = d = distance_to_screen * ppc # distance to screen in pixels

## Sample rate eyetracker
sample_rate_ET = 240 # in Hz

## Identifying gaps
confidence_threshold = 0.8 # (value provided by Pupil Labs, indication of quality assessment of pupil detection)
valid_gap_threshold = 0.075 # s (gaps shorter than this treshold are filled in by linear interpolation)
add_gap_samples = 0.1 # s (time to extend valid gaps, both before and after the gap)

## AOI Margins
angle_a = error_angle = 1.5 # in degrees (margin that is added around AOIs)
angle_b = minimal_angle_of_aoi = 1.5 # in degrees (a margin is added if AOIs are smaller than this angle, after that the margin of angle_a is added)

# Filter short times between exits and entries
minimal_threshold_entry_exit = 0.1 # in sec (if time between an entry and exit in an AOI is shorter than this threshold, these visits are combined)
minimal_threshold_dwell = 0.1 # in sec (if the duration of a dwell is below this threshold, it will not be considered in total_dwell_time)

## Surface specifications (as defined in Pupil Labs Capture)
n_surfaces = 9 # number of surfaces
surfaces = {}
surfaces[1] = {'left_border': 0, 'right_border': 691 }
surfaces[2] = {'left_border': 450, 'right_border': 1208 }
surfaces[3] = {'left_border': 1087, 'right_border': 1786 }
surfaces[4] = {'left_border': 1665, 'right_border': 2362 }
surfaces[5] = {'left_border': 2242, 'right_border': 3516 }
surfaces[6] = {'left_border': 3396, 'right_border': 4094 }
surfaces[7] = {'left_border': 3972, 'right_border': 4671 }
surfaces[8] = {'left_border': 4548, 'right_border': 5308 }
surfaces[9] = {'left_border': 5067, 'right_border': 5760 }