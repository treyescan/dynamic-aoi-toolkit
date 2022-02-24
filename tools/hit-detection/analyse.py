import sys
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Confirm

sys.path.append('../../')

# our own utilities needed
from utils.utils__general import \
    ask_for_participant_id, ask_for_starting_task, \
    prepare_aoi_tasks, we_are_not_skipping_task, \
    ask_for_video_id, check_participant_id
from utils.utils__console import console
from utils.utils__general import show_error

# all analysis steps
from steps.check_synchronization_surfaces import check_synchronization_surfaces
from steps.merge_gaze_positions import merge_gaze_positions
from steps.apply_median_filter_on_coordinates import apply_median_filter_on_coordinates
from identify_gaps_and_to_linear_time import identify_gaps_and_to_linear_time
from identify_hits import identify_hits
from identify_entries_and_exits import identify_entries_and_exits
from generate_output import generate_output

# Gather some input:
# We'll run an analysis for a specific participant, thus we need an ID
participant_id = ask_for_participant_id()
video_id = ask_for_video_id()
starting_task = ask_for_starting_task()
check_participant_id(participant_id, video_id)

# Set up a progress bar
progress_instance = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeRemainingColumn(),
    TimeElapsedColumn(),
)

console.print("[bold yellow]Starting analysis for participant \"{}/{}\" at task {}".format(participant_id, video_id, starting_task))

#### 1) Check synchronization surfaces on expected moments
console.print("[cyan]1. Checking synchronization surfaces")
if(starting_task == 1):
    check_synchronization_surfaces(participant_id, video_id, '{}.json'.format(video_id), console)
    if(not Confirm.ask("May we continue?")):
        show_error('Aborted by user')

with progress_instance as progress:

    # Setting up all tasks (progress bar)
    tasks = prepare_aoi_tasks(progress)

    #### 2) Merge the gaze_gaze_positions_on_surface_Surface*WB.csv (and dummy)
    if(we_are_not_skipping_task(2, starting_task, progress, tasks)):
        merge_gaze_positions(participant_id, video_id, progress, tasks[0])

    #### 3) Median filter over the true_x_scaled and true_y_scaled 
    if(we_are_not_skipping_task(3, starting_task, progress, tasks)):
        apply_median_filter_on_coordinates(participant_id, video_id, progress, tasks[1])

    #### 4) Identify (valid) gaps in the gaze positions data
    if(we_are_not_skipping_task(4, starting_task, progress, tasks)):
        identify_gaps_and_to_linear_time(participant_id, video_id, progress, tasks[2])

    #### 5) With the ROIs and the GPs: identify hits in the ROIs
    if(we_are_not_skipping_task(5, starting_task, progress, tasks)):
        identify_hits(participant_id, video_id, '{}.csv'.format(video_id), progress, tasks[3])

    #### 6) Identify entries and exits for all ROIs
    if(we_are_not_skipping_task(6, starting_task, progress, tasks)):
        identify_entries_and_exits(participant_id, video_id, '{}.csv'.format(video_id), progress, tasks[4])

    #### 7) Generate an output.csv to use in further analysis
    if(we_are_not_skipping_task(7, starting_task, progress, tasks)):
        generate_output(participant_id, video_id, '{}.csv'.format(video_id), progress, tasks[5])

    progress.print('[bold green]Done!')