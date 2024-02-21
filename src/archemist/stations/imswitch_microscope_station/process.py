from transitions import State
from archemist.core.persistence.models_proxy import ModelProxy
from archemist.core.state.station_process import StationProcess, StationProcessModel
from archemist.core.state.robot_op import RobotTaskOp, RobotWaitOp

from archemist.core.state.lot import Lot
from .state import (MicroscopeInLoadingPositionOp,
                    MicroscopeInLoadingPositionResult,
                    MicroscopeImagingOp,
                    MicroscopeImagingResult,
                    MicroscopeCalibrationOp,
                    MicroscopeCalibrationResult
                    )
from typing import Union, List, Dict, Any
from .model import ImSwitchMicroscopeStation

# process.py : defines the flow of operation that the station will go through in order to execute its operations and
# perform its function. This include both station operation and required robot tasks to proceed. 
# Currently, the process is represented using a finite state machine, where its states represent the various 
# station operations and robot task requests required to complete the process. 
class ImSwitchMicroscopeProcess(StationProcess):
    
    def __init__(self, process_model: Union[StationProcessModel, ModelProxy]) -> None:
        super().__init__(process_model)

        ''' States '''
        self.STATES = [
            State(name='init_state', on_enter='initialise_process_data'),
            State(name='load_position', on_enter='request_load_position'),
            State(name='imaging', on_enter='request_imaging'),
            State(name='calibration', on_enter='request_calibration'),
            State(name='final_state')
        ]
        
        ''' Transitions '''
        self.TRANSITIONS = [
            { 'source':'init_state','dest':'load_position'},
            { 'source':'load_position','dest':'imaging', 'conditions':'is_imaging_required'},
            { 'source':'imaging', 'dest': 'load_position', 'conditions':'is_imaging_done'}
            ]

    @classmethod
    def from_args(cls, lot: Lot,
                  target_batch_index: int,
                  target_sample_index: int,
                  operations: List[Dict[str, Any]] = None,
                  is_subprocess: bool=False,
                  skip_robot_ops: bool=False,
                  skip_station_ops: bool=False,
                  skip_ext_procs: bool=False
                  ):
        model = StationProcessModel()
        cls._set_model_common_fields(model,
                                     ImSwitchMicroscopeStation.__name__,
                                     lot,
                                     operations,
                                     is_subprocess,
                                     skip_robot_ops,
                                     skip_station_ops,
                                     skip_ext_procs)
        model.data["target_batch_index"] = int(target_batch_index)
        model.data["target_sample_index"] = int(target_sample_index)
        model.save()
        return cls(model)
    
    ''' States callbacks. '''

    def initialise_process_data(self):
        pass

    def request_load_position(self):
        station_op = MicroscopeInLoadingPositionOp.from_args()
        self.request_station_op(station_op)

    def request_microscopic_imaging(self):
        station_op = MicroscopeImagingOp.from_args()
        self.request_station_op(station_op)

    '''
    def request_load_funnel(self):
        robot_task = RobotTaskOp.from_args(
            name="LoadFunnel",
            target_robot="KMRIIWARobot"
        )
        wait_for_next_op = RobotWaitOp.from_args("KMRIIWARobot", 3)
        self.request_robot_ops([robot_task, wait_for_next_op])

    def request_close_balance_door(self):
        station_op = APCCloseBalanceDoorOp.from_args()
        self.request_station_op(station_op)

    def request_weigh(self):
        batch_index = self.data["target_batch_index"]
        sample_index = self.data["target_sample_index"]
        sample = self.lot.batches[batch_index].samples[sample_index]
        station_op = APCWeighingOp.from_args(target_sample=sample)
        self.request_station_op(station_op)
        self.data['is_weighing_complete'] = True

    def request_unload_funnel(self):
        # TODO add parameter for funnel index?
        robot_task = RobotTaskOp.from_args(name="UnloadFunnel",
                                           target_robot="KMRIIWARobot")
        self.request_robot_ops([robot_task])

    def increment_funnel_index(self):
        weighing_station: APCWeighingStation = self.get_assigned_station()
        weighing_station.funnel_storage_index += 1
    '''
    ''' transition callbacks '''
    def is_weighing_complete(self):
        return self.data['is_weighing_complete']