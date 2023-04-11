from mongoengine import Document, EmbeddedDocument, fields
from archemist.core.util.enums import StationState, OpState
from archemist.core.models.batch_model import BatchModel
from archemist.core.models.station_op_model import StationOpDescriptorModel
from archemist.core.models.robot_op_model import RobotOpDescriptorModel

class StationProcessDataModel(EmbeddedDocument):
    uuid = fields.UUIDField(binary=False)
    batches = fields.ListField(fields.ReferenceField(BatchModel), default=[])
    req_robot_ops = fields.EmbeddedDocumentListField(RobotOpDescriptorModel,default=[])
    req_station_ops = fields.EmbeddedDocumentListField(StationOpDescriptorModel,default=[])
    status = fields.DictField(default={})

class StationModel(Document):
    ''' internal '''
    _type = fields.StringField(required=True)
    _module = fields.StringField(required=True)

    ''' general '''
    exp_id = fields.IntField(required=True)
    location = fields.DictField()
    batch_capacity = fields.IntField(min_value=1, default=1)
    selected_handler = fields.StringField(required=True)
    state = fields.EnumField(StationState, default=StationState.INACTIVE) # this needs to be streamlined
    
    ''' process '''
    process_batch_capacity = fields.IntField(min_value=1, default=1)
    process_state_machine = fields.DictField(required=True)
    process_data_map = fields.MapField(fields.EmbeddedDocumentField(StationProcessDataModel), default={})
    
    ''' batches '''
    assigned_batches = fields.ListField(fields.ReferenceField(BatchModel), default=[])
    processed_batches = fields.ListField(fields.ReferenceField(BatchModel), default=[])
    
    ''' robot ops '''
    requested_robot_op = fields.EmbeddedDocumentListField(RobotOpDescriptorModel,default=[])
    completed_robot_ops = fields.MapField(fields.EmbeddedDocumentField(RobotOpDescriptorModel, default={}))
    
    ''' station ops '''
    station_op_history = fields.EmbeddedDocumentListField(StationOpDescriptorModel,default=[])

    queued_ops = fields.EmbeddedDocumentListField(StationOpDescriptorModel,default=[])
    assigned_op = fields.EmbeddedDocumentField(StationOpDescriptorModel, null=True)
    assigned_op_state = fields.EnumField(OpState,default=OpState.INVALID)
    completed_station_ops = fields.MapField(fields.EmbeddedDocumentField(StationOpDescriptorModel, default={}))

    meta = {'collection': 'stations', 'db_alias': 'archemist_state', 'allow_inheritance': True}