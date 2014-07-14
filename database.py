class BaseDataStore(object):
    def save_match(self, match_id, match):
        pass

    def save_block(self, block_id, block):
        pass

    def save_list(self, list_id, list_model):
        pass

    def save_deleted_list(self, deleted_list_id, deleted_list):
        pass

    def save_record(self, record_id, record):
        pass


import pymongo
import bson


class MongoDataStore(BaseDataStore):
    def __init__(self):
        self._client = pymongo.MongoClient()
        self._db = self._client.tinder_db
        self._matches = self._db.matches
        self._blocks = self._db.blocks
        self._lists = self._db.lists
        self._deleted_lists = self._db.deleted_lists
        self._records = self._db.records

    def save_match(self, match_id, match):
        match_id = bson.ObjectId(match_id)
        self._matches.update({'_id': match_id}, match, upsert=True)

    def save_block(self, block_id, block):
        #block_id = bson.ObjectId(block_id)
        #self._blocks.update({'_id': block_id}, block, upsert=True)
        pass

    def save_list(self, list_id, list_model):
        list_id = bson.ObjectId(list_id)
        self._lists.update({'_id': list_id}, list_model, upsert=True)

    def save_deleted_list(self, deleted_list_id, deleted_list):
        deleted_list_id = bson.ObjectId(deleted_list_id)
        self._deleted_lists.update({'_id': deleted_list_id}, deleted_list, upsert=True)

    def save_record(self, record_id, record):
        record_id = bson.ObjectId(record_id)

        record = record.copy()
        del record['_id']
        self._records.find_and_modify({'_id': record_id}, update=record, upsert=True)
