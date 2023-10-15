from mongoengine import Document, EmbeddedDocument, fields
from archemist.core.models.station_op_model import StationOpDescriptorModel

class SampleModel(EmbeddedDocument):
    materials = fields.ListField(fields.DictField(), default=[])
    station_ops = fields.ListField(fields.ReferenceField(StationOpDescriptorModel), default=[])
    details = fields.DictField(default={})

class BatchModel(Document):
    location = fields.DictField(default={})
    parent_lot_id = fields.ObjectIdField(null=True)
    samples = fields.EmbeddedDocumentListField(SampleModel)
    station_stamps = fields.ListField(fields.StringField(), default=[])

    meta = {'collection': 'batches', 'db_alias': 'archemist_state'}

