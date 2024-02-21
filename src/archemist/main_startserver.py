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

import sys
if __name__ == '__main__':
    workflow_dir = Path('./examples/apc_workflow/')
    existing_db = False
    server = ArchemistServer(workflow_dir,existing_db)
    server.run()

    