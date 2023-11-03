from archemist.core.models.station_model import StationModel
from archemist.core.models.station_op_model import StationBatchOpDescriptorModel
from mongoengine import fields

class ShakerPlateStationModel(StationModel):
    is_shaking = fields.BooleanField(default=False)

class ShakerPlateOpModel(StationBatchOpDescriptorModel):
    duration = fields.IntField(min_value=0)
    time_unit = fields.StringField(choices=["second", "minute", "hour"], default="second")
