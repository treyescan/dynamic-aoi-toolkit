import __constants
import sys
import subprocess
import glob
import re
import argparse
import iterm2
import asyncio
import time
from rich.progress import Progress
sys.path.append('../../')

with Progress() as progress:

    async def analyse_single(participant_id, measurement_moment, task_id, starting_task, progress, i, total_files, sub, connection, app):
        # make the command and execute it
        cmd = 'python3 ./analyse.py --p={} --mm={} --t={} --st={} && exit\n'.format(
            participant_id, measurement_moment, task_id, starting_task)
        await sub.async_send_text(cmd)

        # give some time for the cmd to start
        time.sleep(1)

        # progress.print('Set up a monitor for session {}'.format(session_id))

        async with iterm2.SessionTerminationMonitor(connection) as mon:
            closed = False
            while not closed:
                a = await mon.async_get()
                if a == sub.session_id:
                    closed = True
                    # progress.print("Session {} closed".format(a))

    async def main(connection):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--st', help='Start at step # from analysis', type=int, default=1)
        args = parser.parse_args()

        starting_task = args.st

        participants_to_analyse = glob.glob(
            "{}/*/*/*/gaze_positions_on_surface_Surface1WB.csv".format(__constants.input_folder))
        total_files = len(participants_to_analyse)

        # Get app
        app = await iterm2.async_get_app(connection)

        # Ensure window
        window = app.current_terminal_window
        if app.current_terminal_window is None:
            exit()

        progress.print('Analysing {} files'.format(total_files))
        task1 = progress.add_task(
            "[red]Analysing {} files".format(total_files), total=total_files)

        i = 1

        for file_name in participants_to_analyse:
            regex = re.findall(
                "(P-[0-9]..)\/(T[0-9])\/([a-zA-Z0-9]*)", file_name)

            participant_id = regex[0][0]
            measurement_moment = regex[0][1]
            task_id = regex[0][2]

            # Split main
            sess = window.current_tab.current_session
            sub = await sess.async_split_pane(vertical=True)

            progress.print('Analysing {}, {}, {} ({}/{})'.format(participant_id,
                           measurement_moment, task_id, i, total_files))
            # progress.print('(ID: {})'.format(sub.session_id))

            await analyse_single(participant_id, measurement_moment, task_id, starting_task, progress, i, total_files, sub, connection, app)

            progress.update(task1, advance=1)
            i = i + 1

    iterm2.run_until_complete(main)
