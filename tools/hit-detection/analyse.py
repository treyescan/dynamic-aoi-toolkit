#!/usr/bin/python3
import sys
import argparse
sys.path.append('../../')

from rich.progress import Progress, TimeElapsedColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Confirm

# our own utilities needed
from utils.utils__general import \
    prepare_aoi_tasks, we_are_not_skipping_task, \
    check_aois_files, check_participant_id
from utils.utils__console import console
from utils.utils__general import show_error

# all analysis steps
from steps.check_synchronization_surfaces import check_synchronization_surfaces
from steps.merge_gaze_positions import merge_gaze_positions
from steps.apply_median_filter_on_coordinates import apply_median_filter_on_coordinates
from steps.identify_gaps_and_to_linear_time import identify_gaps_and_to_linear_time
from steps.identify_hits import identify_hits
from steps.identify_entries_and_exits import identify_entries_and_exits
from steps.generate_output import generate_output

# Gather some input:
parser = argparse.ArgumentParser()
parser.add_argument('--p', help='Particpant ID', type=str, required=True)
parser.add_argument('--mm', help='Measurement Moment', type=str, required=True)
parser.add_argument('--t', help='Task ID', type=str, required=True)
parser.add_argument('--id', help='Batch ID to include in output file names', default='')
parser.add_argument('--st', help='Start at step # from analysis', type=int, default=1)
args = parser.parse_args()

participant_id = args.p
measurement_moment = args.mm
task_id = args.t
starting_task = args.st
batch_id = args.id

check_aois_files(task_id)
check_participant_id(participant_id, measurement_moment, task_id)

# Set up a progress bar
progress_instance = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeRemainingColumn(),
    TimeElapsedColumn(),
)

console.print("[bold yellow]Starting analysis for participant \"{}/{}\" at task {}".format(participant_id, task_id, starting_task))

#### 1) Check synchronization surfaces on expected moments
console.print("[cyan]1. Checking synchronization surfaces")
if(starting_task == 1):
    check_synchronization_surfaces(participant_id, measurement_moment, task_id, '{}.json'.format(task_id), console)

with progress_instance as progress:

    # Setting up all tasks (progress bar)
    tasks = prepare_aoi_tasks(progress)

    #### 2) Merge the gaze_gaze_positions_on_surface_Surface*WB.csv (and dummy)
    if(we_are_not_skipping_task(2, starting_task, progress, tasks)):
        merge_gaze_positions(participant_id, measurement_moment, task_id, progress, tasks[0])

    #### 3) Median filter over the true_x_scaled and true_y_scaled 
    if(we_are_not_skipping_task(3, starting_task, progress, tasks)):
        apply_median_filter_on_coordinates(participant_id, measurement_moment, task_id, progress, tasks[1])

    #### 4) Identify (valid) gaps in the gaze positions data
    if(we_are_not_skipping_task(4, starting_task, progress, tasks)):
        identify_gaps_and_to_linear_time(participant_id, measurement_moment, task_id, progress, tasks[2])

    #### 5) With the AOIs and the GPs: identify hits in the AOIs
    if(we_are_not_skipping_task(5, starting_task, progress, tasks)):
        identify_hits(participant_id, measurement_moment, task_id, '{}.csv'.format(task_id), progress, tasks[3])

    #### 6) Identify entries and exits for all AOIs
    if(we_are_not_skipping_task(6, starting_task, progress, tasks)):
        identify_entries_and_exits(participant_id, measurement_moment, task_id, '{}.csv'.format(task_id), progress, tasks[4])

    #### 7) Generate an output.csv to use in further analysis
    if(we_are_not_skipping_task(7, starting_task, progress, tasks)):
        generate_output(participant_id, measurement_moment, task_id, '{}.csv'.format(task_id), batch_id, progress, tasks[5])

    progress.print('[bold green]Done!')