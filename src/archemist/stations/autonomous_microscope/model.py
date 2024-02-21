from mongoengine import fields
from archemist.core.models.station_model import StationModel
from archemist.core.models.station_op_result_model import StationOpResultModel

class AutonomousMicroscopeStationModel(StationModel):
    # Additional fields can be added as needed
    current_task_id = fields.StringField()

class MicroscopeImagingResultModel(StationOpResultModel):
    image_url = fields.URLField()
    analysis_results = fields.DictField()
