from archemist.core.models.station_model import StationModel
from archemist.core.models.station_op_result_model import StationOpResultModel
from mongoengine import fields

'''
What states are important to expose?
- microscope in loading position?
- microscope is busy?
- which imaging task is the microscope currently performing?
- time left until the current imaging task is complete?
- current position of the microscope stage?
- possible errors the microscope is experiencing?
'''
# model.py : defines the database models for the station and all of its operations

class ImSwitchMicroscopeStationModel(StationModel):
    microscope_in_loading_position = fields.BooleanField(default=False)
    microscope_busy = fields.BooleanField(default=False)
    current_imaging_task = fields.StringField(default="none")
    time_left_until_imaging_task_complete = fields.IntField(min_value=0)
    current_stage_position = fields.StringField(default="none")
    microscope_error = fields.StringField(default="none")    
    
class ImSwitchMicroscopeResultModel(StationOpResultModel):
    current_image = fields.FloatField()# fields.ImageField()
