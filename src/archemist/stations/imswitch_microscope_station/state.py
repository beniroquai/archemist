from typing import Dict, Union, List, Literal, Type
from archemist.core.persistence.models_proxy import ModelProxy
from .model import ImSwitchMicroscopeResultModel, ImSwitchMicroscopeStationModel
from archemist.core.models.station_op_model import StationSampleOpModel
from archemist.core.state.station import Station
from archemist.core.state.station_op import StationOp, StationSampleOp, StationOpModel
from archemist.core.state.station_op_result import StationOpResult
from archemist.core.state.sample import Sample
from archemist.core.util.enums import OpOutcome
from bson.objectid import ObjectId

# states hold in archemist system

'''
What states are important to expose?
- microscope in loading position?
- microscope is busy?
- which imaging task is the microscope currently performing?
- time left until the current imaging task is complete?
- current position of the microscope stage?
- possible errors the microscope is experiencing?
'''

''' ==== Station Description ==== '''
class MicroscopeStation(Station):
    def __init__(self, microscope_station_model: Union[ImSwitchMicroscopeStationModel, ModelProxy]) -> None:
        super().__init__(microscope_station_model)

    @classmethod
    def from_dict(cls, station_dict: Dict):
        model = ImSwitchMicroscopeStationModel()
        cls._set_model_common_fields(model, station_dict)
        #model.funnel_storage_capacity = station_dict['properties']['funnel_storage_capacity'] # TODO: What is this?
        model.save()
        return cls(model)

    '''backup
    @property
    def balance_doors_open(self) -> bool:
        return self._model_proxy.balance_doors_open

    @balance_doors_open.setter
    def balance_doors_open(self, new_state: bool):
        self._model_proxy.balance_doors_open = new_state
    '''
    
    @property
    def microscope_in_loading_position(self) -> bool:
        return self._model_proxy.microscope_in_loading_position
    
    @microscope_in_loading_position.setter
    def microscope_in_loading_position(self, new_state: bool):
        self._model_proxy.microscope_in_loading_position = new_state
        
    @property
    def microscope_busy(self) -> bool:
        return self._model_proxy.microscope_busy
    
    @microscope_busy.setter
    def microscope_busy(self, new_state: bool):
        self._model_proxy.microscope_busy = new_state
        
    @property
    def imaging_task(self) -> Literal["imaging", "calibration", "none"]:
        return self._model_proxy.imaging_task
    
    @imaging_task.setter
    def imaging_task(self, new_task: Literal["imaging", "calibration", "none"]):
        self._model_proxy.imaging_task = new_task
        
    @property
    def time_left_until_imaging_task_complete(self) -> float:
        return self._model_proxy.time_left_until_imaging_task_complete
    
    @time_left_until_imaging_task_complete.setter
    def time_left_until_imaging_task_complete(self, new_time: float):
        self._model_proxy.time_left_until_imaging_task_complete = new_time
        
    @property
    def current_position_of_microscope_stage(self) -> Dict[str, float]:
        return self._model_proxy.current_position_of_microscope_stage
    
    @current_position_of_microscope_stage.setter
    def current_position_of_microscope_stage(self, new_position: Dict[str, float]):
        self._model_proxy.current_position_of_microscope_stage = new_position
        
    @property
    def errors(self) -> List[str]:
        return self._model_proxy.errors
    
    @errors.setter
    def errors(self, new_errors: List[str]):
        self._model_proxy.errors = new_errors
    
    def complete_assigned_op(self, outcome: OpOutcome, results: List[Type[StationOpResult]]):
        current_op = self.assigned_op
        if isinstance(current_op, MicroscopeInLoadingPositionOp):
            self.microscope_in_loading_position = True
        elif isinstance(current_op, MicroscopeImagingOp):
            self.microscope_busy = False
            self.imaging_task = "none"
            self.time_left_until_imaging_task_complete = 0
        elif isinstance(current_op, MicroscopeCalibrationOp):
            self.microscope_busy = False
            self.imaging_task = "none"
            self.time_left_until_imaging_task_complete = 0
        
        super().complete_assigned_op(outcome, results)



''' ==== Station Operation Descriptors ==== '''
class MicroscopeInLoadingPositionOp(StationOp):
    def __init__(self, op_model: Union[StationOpModel, ModelProxy]) -> None:
        super().__init__(op_model)

    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=ImSwitchMicroscopeStation.__name__)
        model.save()
        return cls(model)

class MicroscopeImagingOp(StationSampleOp):
    def __init__(self, op_model: StationSampleOpModel):
        super().__init__(op_model)
    
    @classmethod
    def from_args(cls, target_sample: Sample):
        model = StationSampleOpModel()
        model.target_sample = target_sample.model
        cls._set_model_common_fields(model, associated_station=ImSwitchMicroscopeStation.__name__)
        model.save()
        return cls(model)
    
class MicroscopeCalibrationOp(StationOp):
    def __init__(self, op_model: Union[StationOpModel, ModelProxy]) -> None:
        super().__init__(op_model)
    
    @classmethod
    def from_args(cls):
        model = StationOpModel()
        cls._set_model_common_fields(model, associated_station=ImSwitchMicroscopeStation.__name__)
        model.save()
        return cls(model)
    
class MicroscopeInLoadingPositionResult(StationOpResult):
    def __init__(self, result_model: Union[ImSwitchMicroscopeResultModel, ModelProxy]):
        super().__init__(result_model)
    
    @classmethod
    def from_args(cls, origin_op: ObjectId):
        model = ImSwitchMicroscopeResultModel()
        cls._set_model_common_fields(model, origin_op)
        model.save()
        return cls(model)
    
class MicroscopeImagingResult(StationOpResult):
    def __init__(self, result_model: Union[ImSwitchMicroscopeResultModel, ModelProxy]):
        super().__init__(result_model)
    
    @classmethod
    def from_args(cls, origin_op: ObjectId):
        model = ImSwitchMicroscopeResultModel()
        cls._set_model_common_fields(model, origin_op)
        model.save()
        return cls(model)
    
class MicroscopeCalibrationResult(StationOpResult):
    def __init__(self, result_model: Union[ImSwitchMicroscopeResultModel, ModelProxy]):
        super().__init__(result_model)
    
    @classmethod
    def from_args(cls, origin_op: ObjectId):
        model = ImSwitchMicroscopeResultModel()
        cls._set_model_common_fields(model, origin_op)
        model.save()
        return cls(model)
    
    @property
    def calibration_result(self) -> Dict[str, float]:
        return self._model_proxy.calibration_result
    
    @calibration_result.setter
    def calibration_result(self, new_result: Dict[str, float]):
        self._model_proxy.calibration_result = new_result

