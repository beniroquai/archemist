from bson.objectid import ObjectId
from pymongo import MongoClient, results
import pickle

class DbObjProxy:
    def __init__(self, db: str, collection: str, obj_data):
        self._mongo_client = MongoClient("mongodb://localhost:27017")
        self._db_collection = self._mongo_client[db][collection]
        if isinstance(obj_data, dict):
            stored_document = self._db_collection.find_one({'object': obj_data['object'], 'id': obj_data['id']})
            if stored_document is None:
                self._db_id = self._db_collection.insert_one(obj_data).inserted_id
            else:
                self._db_id = stored_document['_id']
                self._db_collection.replace_one({'_id': self._db_id}, obj_data)
        elif isinstance(obj_data, ObjectId):
            self._db_id = obj_data

    def get_db_proxy(self):
        db, collection = self._db_collection.full_name.split('.')
        return DbObjProxy(db, collection, self._db_id)

    def update_field(self, field_key: str, value):
        self._db_collection.update_one({'_id': self._db_id}, {'$set': {field_key: value}})

    def get_field(self, field_key:str):
        return self._db_collection.find_one({'_id': self._db_id})[field_key]

    def get_nested_field(self, field_key:str):
        nested_keys = field_key.split('.')
        nested_value = self._db_collection.find_one({'_id': self._db_id})[nested_keys.pop(0)]
        for key in nested_keys:
            nested_value = nested_value[key]
        return nested_value

    def increment_field(self, field_key:str):
        self._db_collection.update_one({'_id': self._db_id}, {'$inc': {field_key: 1}})

    def decrement_field(self, field_key:str):
        self._db_collection.update_one({'_id': self._db_id}, {'$inc': {field_key: -1}})

    def push_to_array_field(self, arrary_key:str, value):
        self._db_collection.update_one({'_id': self._db_id}, {'$push': {arrary_key: value}})

    def pop_from_array_field(self, arrary_key:str):
        self._db_collection.update_one({'_id': self._db_id}, {'$pop': {arrary_key: 1}})

    def update_doc_in_array_field(self, array_key:str, index:int, doc_field: str, value):
        self._db_collection.update_one({'_id': self._db_id}, {'$set': {f'{array_key}.{index}.{doc_field}': value}})

    def get_doc_from_array_field(self, array_key:str, index:int):
        return self._db_collection.find_one({'_id': self._db_id})[array_key][index]

    @staticmethod
    def encode_object(object):
        return pickle.dumps(object)

    @staticmethod
    def decode_object(object):
        return pickle.loads(object)