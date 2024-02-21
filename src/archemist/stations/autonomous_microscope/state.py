from archemist.core.state.station import Station
from archemist.core.state.station_op import StationOp
from archemist.core.state.station_op_result import StationOpResult
from archemist.core.persistence.models_proxy import ModelProxy
from .model import AutonomousMicroscopeStationModel, MicroscopeImagingResultModel
from archemist.core.state.station import Station, StationModel
from bson.objectid import ObjectId
from typing import Dict, Union

class AutonomousMicroscopeStation(Station):
    def __init__(self, model: Union[StationModel, ModelProxy]):
        super().__init__(model)

    @classmethod
    def from_dict(cls, station_dict: Dict):
        model = StationModel()
        cls._set_model_common_fields(model, station_dict)
        model.save()
        return cls(model)

class StartImagingOp(StationOp):
    # Assuming a simple operation without additional parameters for simplicity
    pass

class ImagingResult(StationOpResult):
    def __init__(self, result_model: Union[MicroscopeImagingResultModel, Dict]):
        super().__init__(result_model)

    @classmethod
    def from_args(cls, origin_op: ObjectId, image_url: str, analysis_results: Dict):
        model = MicroscopeImagingResultModel(origin_op=origin_op, image_url=image_url, analysis_results=analysis_results)
        return cls(model)
