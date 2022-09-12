from time import sleep
from archemist.processing.prcessor import WorkflowManager
from archemist.persistence.persistenceManager import PersistenceManager
from archemist.persistence.recipe_files_watchdog import RecipeFilesWatchdog
from archemist.persistence.yamlHandler import YamlHandler
from archemist.util.location import Location
from pathlib import Path
from datetime import datetime
from archemist.state.robots.kukaLBRIIWA import KukaNAVTask, KukaLBRTask, KukaLBRMaintenanceTask
from archemist.state.robot import RobotOutputDescriptor
import zmq

if __name__ == '__main__':
    current_dir = Path.cwd()
    server_config_file_path = current_dir.joinpath(f'server_settings.yaml')
    server_setttings = YamlHandler.loadYamlFile(server_config_file_path)

    workflow_dir = Path(server_setttings['workflow_dir_path'])
    workflow_config_file_path = workflow_dir.joinpath(f'config_files/workflow_config.yaml')
    recipes_dir_path = workflow_dir.joinpath(f'recipes')

    db_name = server_setttings['db_name']
    batch_addition_location = Location(server_setttings['batch_addition']['location']['node_id'],
                                        server_setttings['batch_addition']['location']['graph_id'], 
                                        server_setttings['batch_addition']['location']['frame_name'])
    batch_num_vials = server_setttings['batch_addition']['num_vials']
    recipe_loop_mode = server_setttings['recipe_loop_mode']
    auto_batch_addition = server_setttings['auto_batch_addition']
    
    batch_id = 0
    recipe_to_loop = None
    loop_batch_added = False

    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.bind('tcp://127.0.0.1:5555')
    # Construct state from config file
    pers_manager = PersistenceManager(db_name)
    state = pers_manager.construct_state_from_config_file(workflow_config_file_path)
    # construct the state manager
    wm_manager = WorkflowManager(state)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f'[{current_time}] Started workflow Server')

    recipes_watcher = RecipeFilesWatchdog(recipes_dir_path)
    recipes_watcher.start()


    # recipe_index = 0
    # init = False
    
    # spin
    while True:

        if recipe_loop_mode:
            if recipe_to_loop is None:
                if recipes_watcher.recipes_queue:
                    recipe_file_path = recipes_watcher.recipes_queue.pop()
                    recipe_to_loop = YamlHandler.loadYamlFile(recipe_file_path)
            elif len(wm_manager.recipes_queue) == 0:
                wm_manager.queue_recipe(recipe_to_loop)
        else:
            while recipes_watcher.recipes_queue:
                recipe_file_path = recipes_watcher.recipes_queue.pop()
                recipe_dict = YamlHandler.loadYamlFile(recipe_file_path)
                wm_manager.queue_recipe(recipe_dict)
                print(f'new recipe file queued')

        if auto_batch_addition:
            if not loop_batch_added:
                state.add_clean_batch(batch_id, batch_num_vials, batch_addition_location)
                print(f'Batch (id: {batch_id}) is added')
                loop_batch_added = True
            elif state.is_batch_complete(batch_id):
                batch_id += 1
                state.add_clean_batch(batch_id, batch_num_vials, batch_addition_location)
                print(f'Batch (id: {batch_id}) is added')

        try:
            msg = socket.recv_string(flags=zmq.NOBLOCK)
            if msg == 'start':
                if not wm_manager._running:
                    wm_manager.start_processor()
                    init = True
                else:
                    wm_manager.pause_workflow = False
            elif msg == 'pause':
                wm_manager.pause_workflow = True
            elif msg == 'add_batch':
                state.add_clean_batch(batch_id, batch_num_vials, batch_addition_location)
                batch_id += 1
            elif msg == 'charge':
                wm_manager.queue_robot_op(KukaLBRMaintenanceTask('ChargeRobot',[False,85],RobotOutputDescriptor()))
            elif msg == 'stop_charge':
                wm_manager.queue_robot_op(KukaLBRMaintenanceTask('StopCharge',[False],RobotOutputDescriptor()))
            elif msg == 'resume_app':
                wm_manager.queue_robot_op(KukaLBRMaintenanceTask('resumeLBRApp',[False],RobotOutputDescriptor()))
            elif msg == 'terminate':
                if wm_manager._running:
                    wm_manager.stop_processor()
                    break
        except zmq.ZMQError:
            sleep(0.2)
        except KeyboardInterrupt:
            if wm_manager._running:
                wm_manager.stop_processor()
                break