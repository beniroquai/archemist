from archemist.application.archemist_server import ArchemistServer
from archemist.application.archemist_cli import ArchemistCLI
from archemist.core.persistence.yaml_handler import YamlHandler
from archemist.core.processing.handler import StationHandler, RobotHandler
from archemist.core.persistence.object_factory import StationFactory, RobotFactory
from archemist.core.persistence.objects_getter import StationsGetter, RobotsGetter
from archemist.core.persistence.db_handler import DatabaseHandler
import multiprocessing as mp
from pathlib import Path
import argparse
import time
import sys

def run_station_handler(db_host, db_name, station_object_id, use_sim_handler):
        db_handler = DatabaseHandler(db_host, db_name) # needed to establish connection with db
        station = StationFactory.create_from_object_id(station_object_id)
        handler = StationHandler(station, use_sim_handler)
        handler.initialise()
        handler.run()


def run_robot_handler(db_host, db_name, robot_object_id, use_sim_handler):
    db_handler = DatabaseHandler(db_host, db_name) # needed to establish connection with db
    robot = RobotFactory.create_from_object_id(robot_object_id)
    handler = RobotHandler(robot, use_sim_handler)
    handler.initialise()
    handler.run()


def launch_stations():
    workflow_dir = Path('./examples/apc_workflow/')
    existing_db = False


    server_config_file_path = workflow_dir.joinpath(f'config_files/server_settings.yaml')
    server_settings = YamlHandler.load_server_settings_file(server_config_file_path)
    db_name = server_settings['db_name']
    db_host = server_settings['mongodb_host']

    try:
        db_handler = DatabaseHandler(db_host, db_name)

        start_time = time.time()
        while not db_handler.is_database_existing():
            print('waiting on database state to exist')
            time.sleep(0.5)
            if time.time() - start_time > 5:
                sys.exit('timeout reached! no db state is available. Exiting')

        mp.set_start_method('spawn') # to avoid forking error with mongodb
        # define robot handlers processes
        robot_handlers_processes = []
        for robot in RobotsGetter.get_robots():
            kwargs = {
                'db_host': db_host,
                'db_name': db_name,
                'robot_object_id': robot.object_id,
                'use_sim_handler': True
                }
            robot_handlers_processes.append(mp.Process(target=run_robot_handler, kwargs=kwargs))
        # define station handlers processes
        station_handlers_processes = []
        for station in StationsGetter.get_stations():
            kwargs = {
                'db_host': db_host,
                'db_name': db_name,
                'station_object_id': station.object_id,
                'use_sim_handler': True
                }
            station_handlers_processes.append(mp.Process(target=run_station_handler, kwargs=kwargs))
        # launch handlers this assumes the state was constructed from a config file before hand
        processes = robot_handlers_processes + station_handlers_processes
        for p in processes:
            p.daemon = True
            p.start()
        while any(p.is_alive() for p in processes):
            time.sleep(0.1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
            p.join()

if __name__ == '__main__':
    import time 
    time.sleep(5)
    launch_stations()