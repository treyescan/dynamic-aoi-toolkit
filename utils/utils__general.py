import sys
sys.path.append('../')

import __constants, os.path
from genericpath import isdir
from os import mkdir
from utils.utils__console import console

def we_are_not_skipping_task(current_task, starting_task, progress, tasks):
    if(current_task < starting_task):
        progress.print('[i bright_black]Skipping task {}... Assuming we already did this.'.format(current_task))
        progress.update(tasks[current_task - 1], total=1, completed=1)

        return False
    else:
        return True

def show_error(message, progress):
    progress.print("[bold red]{}".format(message))
    raise Exception(message)

def ask_for_participant_id():
    id = console.input("Provide the [bold cyan]participant id[/bold cyan] [i bright_black](default: P-001)[/i bright_black]: ") or "P-001"
    return id

def ask_for_measurement_moment():
    m = console.input("Provide the [bold cyan]measurement moment[/bold cyan] [i bright_black](default: T1)[/i bright_black]: ") or "T1"
    return m

def ask_for_task_id():
    file = console.input("Provide the [bold cyan]task ID (e.g. Deel1)[/bold cyan] (for input folder and both AOI & synchronization file) [i bright_black](default: Deel1)[/i bright_black]: ") or "Deel1"
    check_aois_files(file)
    return file

def ask_for_starting_task():
    return int(console.input('At [bold cyan]which task[/bold cyan] are we starting? [i bright_black](default: 1)[/i bright_black] ') or "1")

def check_aois_files(file):
    if file == "":
        raise Exception('No AOI file provided')
    elif not os.path.isfile('{}/input-aoi/{}.csv'.format(__constants.data_folder, file)):
        raise Exception('AOIs file for {}.csv not found'.format(file))
    elif not os.path.isfile('{}/videos/start_end_frames/synchronization/{}.json'.format(__constants.data_folder, file)):
        location = '{}/videos/start_end_frames/synchronization/{}.json'.format(__constants.data_folder, file)
        raise Exception('synchronization file for {}.json not found, location: {}'.format(file, location))

def check_participant_id(id, measurement_moment, task_id):
    if id == "":
        raise Exception('No participant ID provided')
    elif measurement_moment == "":
        raise Exception('No measurement moment provided')
    elif not os.path.isdir('{}/{}'.format(__constants.input_folder, id)):
        raise Exception('Input folder for participant {} not found'.format(id))

    if not os.path.isdir(__constants.output_folder):
        os.mkdir(__constants.output_folder)

    if not os.path.isdir('{}/{}'.format(__constants.output_folder, id)):
        os.mkdir('{}/{}'.format(__constants.output_folder, id))

    if not os.path.isdir('{}/{}/{}'.format(__constants.output_folder, id, measurement_moment)):
        os.mkdir('{}/{}/{}'.format(__constants.output_folder, id, measurement_moment))

    if not os.path.isdir('{}/{}/{}/{}'.format(__constants.output_folder, id, measurement_moment, task_id)):
        os.mkdir('{}/{}/{}/{}'.format(__constants.output_folder, id, measurement_moment, task_id))

def prepare_aoi_tasks(progress):
     return [
        progress.add_task("[cyan]2. Merging gaze positions", total=20), # 0
        progress.add_task("[cyan]3. Median filter", total=1), # 1
        progress.add_task("[cyan]4. Identifying gaps in gaze positions", total=1), # 2
        progress.add_task("[cyan]5. Identifying hits", total=50), # 3
        progress.add_task("[cyan]6. Identifying entries and exits", total=50), # 4
        progress.add_task("[cyan]7. Generating output", total=9), # 5
     ]
