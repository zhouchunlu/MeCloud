# -*- coding: utf-8 -*-
'''
 * file :   DbHandler.py
 * author : bushaofeng
 * create : 2016-06-08 20:08
 * func : 数据库
 * history:
'''
import pymongo,json,copy,logging
from bson import ObjectId
from bson import json_util
from datetime import datetime
from urllib import unquote
from mecloud.model.MeObject import *
from mecloud.model.MeError import *
from mecloud.lib import *
from Util import *

# 基类
class Db:
    # 数据库连接
    conn = None;
    # 数据库名字
    name = None
    # 事务
    transaction_map = {}

    def __init__(self, db=None):
        if db:
            self.name = db

    @staticmethod
    def selectDb(dbName):
        Db.name = dbName

    def dbName(self):
        if self.name:
            return self.name
        else:
            return Db.name

    def find_one(self, collection, query):
        pass

    def find(self, collection, query):
        pass

    def insert(self, collection, obj):
        pass

    def remove(self, collection, query):
        pass

    def updateOne(self, collection, query, obj):
        pass

    def update(self, collection, query, obj):
        pass

    """
    @souceClass: 源表名，如Followee
    @sourceField:源表字段，如Followee表的user字段
    @destClass: 目标表，如StatCount
    @destField: 目标字段，如Followees_xxx/Followers_xxxx
    @action: 目标动作，如{'$inc:1'}
    """
    @staticmethod
    def transaction(collection, method='create', field=''):
        # update对应的事务, 此处field直接传入query即可
        if isinstance(field, dict):
            for key in field:
                action_name = collection+'_'+str(method)+'_'+key
                # 返回一个事务对象
                if transaction_map.has_key(action_name):
                    return copy.deepcopy(transaction_map[action_name])
            return None
        else:
            # 返回一个事务对象
            if transaction_map.has_key(action_name):
                return copy.deepcopy(transaction_map[action_name])
            else:
                return None

## MongoDb封装
class MongoDb(Db):
    @staticmethod
    def connect(addr, port = 27017, replica_set=None, user=None, password=None):
        if isinstance(addr, str) or isinstance(addr, unicode):
            if not port:
                Db.conn = pymongo.MongoClient(addr)
            else:
                Db.conn = pymongo.MongoClient(addr, port)
        elif isinstance(addr, list) and replica_set!=None:
            Db.conn = pymongo.MongoClient(addr, replicaSet=replica_set)
        if user!=None and password!=None:
            Db.conn.admin.authenticate(user, password)

    ### 构造函数
    def __init__(self, dbName=None):
        Db.__init__(self, dbName)
        self.db = Db.conn[self.dbName()]

    ### 查找第一个
    def find_one(self, collection, query, keys=None):
        doc = self.db[collection].find_one(MongoDb.toBson(query), keys);
        if not doc:
            return None
        if '__transaction' in doc:
            del(doc['__transaction'])
        return MongoDb.toJson(doc)

    ### 查询
    def find(self, collection, query, keys=None, sort=None, limit=8, skip=0):
        results = []
        if sort == None:
            items = self.db[collection].find(MongoDb.toBson(query), keys).sort('_id', -1).skip(skip).limit(limit)
        else:
            items = self.db[collection].find(MongoDb.toBson(query), keys).sort(self.sortToTuple(sort)).skip(0).limit(limit)
        for item in __items:
            if '__transaction' in item:
                del(item['__transaction'])
            results.append(MongoDb.toJson(item))
        return results;
    
    """
    游标遍历
    """
    def cursor(self, collection, query, keys=None, sort=None, limit=10, skip=0):
        if sort == None:
            return self.db[collection].find(MongoDb.toBson(query), keys).sort('_id', -1).skip(skip).limit(limit)
        else:
            return self.db[collection].find(MongoDb.toBson(query), keys).sort(self.sortToTuple(sort)).skip(skip).limit(limit)
    """
    游标遍历
    """
    def next(self, cursor):
        try:
            obj = cursor.next()
            if '__transaction' in obj:
                del(obj['__transaction'])
            return MongoDb.toJson(obj)
        # except StopIteration,e:
        #     return None
        except Exception, __e:
            raise __e

    ### 使用skip查询
    # @deprecated
    # def find_use_skip(self, collection, query, keys=None, sort=None, skip=0, limit=8):
    #     results = []
    #     if sort == None:
    #         items = self.db[collection].find(MongoDb.toBson(query), keys).sort('_id', -1).skip(skip).limit(limit)
    #     else:
    #         items = self.db[collection].find(MongoDb.toBson(query), keys).sort(self.sortToTuple(sort)).skip(skip).limit(
    #             limit)
    #     for item in items:
    #         if '__transaction' in item:
    #             del(item['__transaction'])
    #         results.append(MongoDb.toJson(item))
    #     return results;

    ### 管道查询查询
    def aggregate(self, collection, query):
        results = []
        items = self.db[collection].aggregate(self.aggregateJson(query))
        for item in items:
            if '__transaction' in item:
                del(item['__transaction'])
            results.append(MongoDb.toJson(item))
        return results;

    '''
    带有事务检查的新建操作，如果外部没有传入事务，则从事务管理器中获取事务
    @action: 事务对象
    '''
    def insert(self, collection, obj, transactions=None):
        # if action==None:
        #     action = Db.transaction(collection)
        if transactions==None:
            return self.insertOnly(collection, obj)

        # prepare及写数据过程，此过程出错不需要回滚
        try:
            # 查找一个空闲状态并改为pending, 如果没有查找到则插入一个
            actions = {'transaction:':transactions, 'status':1}
            actions = self.insertOnly('Transaction', actions)

            # 将事务写入数据表, 返回更新之前的数据，如果出错，用于回滚
            obj['__transaction'] = [actions['_id']]
            obj = self.insertOnly(collection, obj)
        except Exception,e:
            logging.exception(e)
            raise ERR_TRANSACTION
            
        #action = self.db.updateOneOnly('Transaction',{'_id':self.action['_id']}, {'$set':{'sourceId': source['_id']}})
        # commit过程
        try:
            for action in transactions:
                dest_action = self.parse(action['action'])
                dest_action['$push'] = {'__transaction': actions['_id']}
                destination = self.updateOneOnly(action['destClass'], action['query'], dest_action, upsert=True, new=True)
        except Exception,e:
            # 回滚
            log.err('Insert transaction error! object[%s: %s]: %s', collection, obj['_id'], str(e))
            try:
                self.remove(collection, {'_id': obj['_id']})
                self.updateOneOnly('Transaction', {'_id':actions['_id']}, {'$set': {'status':4}})
            except Exception,e:
                log.err('Insert transaction rollback error! object[%s: %s]: %s', collection, obj['_id'], str(e))
            raise e

        # 事务状态改为已经提交，下面如果出错已经不影响数据
        # self.action = self.db.updateOneOnly('Transaction', {'_id':self.action['_id']}, {'$set': {'status', 2}})
        try:
            obj = self.updateOneOnly(collection, {'_id': obj['_id']}, {'$pull':{'__transaction': actions['_id']}})
            for action in transactions:
                self.updateOneOnly(action['destClass'], action['query'], {'$pull':{'__transaction': actions['_id']}})
            self.remove('Transaction', {'_id':actions['_id']})
        except Exception,e:
            log.err('Insert transaction done error! transaction[%s: %s] source[%s]: %s', collection, actions['_id'], obj['_id'], str(e))
            raise e

        if '__transaction' in obj:
            del(obj['__transaction'])
        return obj
    
    '''
    单纯的新建操作
    '''
    def insertOnly(self, collection, obj):
        if obj.has_key("_id"):
            obj["_sid"] = MongoDb.toId(obj['_id'])
            obj['_id'] = ObjectId(obj['_id'])

        if 'updateAt' not in obj:
            obj['updateAt'] = datetime.now()
            if 'createAt' not in obj:
                obj['createAt'] = obj['updateAt']

        try:
            obj['_id'] =  MongoDb.toId(self.db[collection].insert(MongoDb.toBson(obj)))
            if '_sid' not in obj:
                obj = self.updateOneOnly(collection, {'_id': obj['_id']}, {'$set':{'_sid': obj['_id']}})
            if '__transaction' in obj:
                del(obj['__transaction'])
            return obj
        except Exception,e:
            log.err('insert[%s] object[%s] error:%s', collection, MongoDb.toJson(obj), str(e))
            ###TODO: insert的不同错误抛出不同异常，如数据库挂掉、唯一冲突等
            if e.code==11000:
                err = copy.deepcopy(ERR_OBJECT_DUP)
                err.message['info'] = e.message
                raise err
            return None

    ### 删除
    def remove(self, collection, query):
        self.db[collection].remove(MongoDb.toBson(query))
        return True

    def updateOne(self, collection, query, obj, transactions=None, upsert=False):
        # if action==None:
        #     action = Db.transaction(collection, query)
        if transactions==None:
            return self.updateOneOnly(collection, query, obj, upsert)

        # prepare及写数据过程，此过程出错不需要回滚
        try:
            # 查找一个空闲状态并改为pending, 如果没有查找到则插入一个
            actions = {'transaction': transactions, 'status':1}
            actions = self.insertOnly('Transaction', actions)

            # 将事务写入数据表, 返回更新之前的数据，如果出错，用于回滚
            update_obj = copy.deepcopy(obj)
            update_obj.update({'$push':{'__transaction': actions['_id']}})
            old_obj = self.updateOneOnly(collection, query, update_obj, upsert=upsert, new=False)
        except Exception,e:
            logging.exception(e)
            raise ERR_TRANSACTION
            
        #action = self.db.updateOneOnly('Transaction',{'_id':self.action['_id']}, {'$set':{'sourceId': source['_id']}})
        # commit过程
        try:
            for action in transactions:
                dest_action = self.parse(action['action'])
                dest_action.update({'$push':{'__transaction': actions['_id']}})
                destination = self.updateOneOnly(action['destClass'], action['query'], dest_action, upsert=True, new=True)
        except Exception,e:
            # 回滚
            log.err('Transaction commit error! transaction[%s: %s] error[%s]', actions['_id'], transactions, str(e))
            obj_id = old_obj['_id']
            del(old_obj['_id'])
            try:
                # old_obj只返回了一个_id，代表updateOneOnly执行了插入操作，回滚需要删除该数据
                if len(old_obj)<=0:
                    self.remove(collection, {'_id': obj_id})
                else:
                    self.updateOneOnly(collection, {'_id': obj_id}, {'$set': old_obj})
                self.updateOneOnly('Transaction', {'_id':actions['_id']}, {'$set': {'status': 4}})
            except Exception,e:
                log.err('Update transaction rollback error! object[%s: %s\t%s]: %s', collection, obj_id, json.dumps(old_obj),str(e))
            # self.remove(collection, {'_id': old_obj['_id']})
            raise e

        # 事务状态改为已经提交，下面如果出错已经不影响数据
        # self.action = self.db.updateOneOnly('Transaction', {'_id':self.action['_id']}, {'$set': {'status', 2}})
        try:
            obj = self.updateOneOnly(collection, {'_id': old_obj['_id']}, {'$pull':{'__transaction': actions['_id']}})
            for action in transactions:
                self.updateOneOnly(action['destClass'], action['query'], {'$pull':{'__transaction': actions['_id']}})
            self.remove('Transaction', {'_id':actions['_id']})
        except Exception,e:
            logging.exception(e)
            log.err('Update transaction done error! transaction[%s:%s] source[%s] destination[%s]: %s', collection, action['_id'], old_obj['_id'], destination['_id'], str(e))
            raise e

        return self.find_one(collection, {'_id': old_obj['_id']})

    """
    @ upsert: 没有是否新建
    @ new: 是否返回更新后的值, 如果upsert为True, 且之前没有数据，则返回新创建的数据的id
    """
    def updateOneOnly(self, collection, query, obj, upsert=False, new=True):
        if new:
            return_doc = pymongo.ReturnDocument.AFTER
        else:
            return_doc = pymongo.ReturnDocument.BEFORE


        doc = self.db[collection].find_one_and_update(MongoDb.toBson(query), obj, upsert=upsert, return_document= return_doc);
        if not doc:
            # 如果upsert为True， 则返回新创建数据的id
            if upsert:
                doc = self.find_one(collection, query)
                obj={}
                if '_sid' not in doc:
                    obj["_sid"]=str(doc['_id'])
                if 'createAt' not in doc:
                    obj['createAt']=doc['updateAt']
                if obj:
                    doc = self.updateOneOnly(collection,{"_id":doc['_id']}, {'$set': obj})
                if doc:
                    return {'_id': doc['_id']}
            log.err('update[%s: %s] not found:%s', collection, json.dumps(query), json.dumps(obj))
            raise copy.deepcopy(ERR_NOTFOUND)
        else:
            obj = {}
            if '_sid' not in doc:
                obj["_sid"] = str( doc['_id'] )
            if 'updateAt' not in doc:
                obj['updateAt'] = datetime.now()
                obj['createAt'] = obj['updateAt']
            if obj:
                doc = self.updateOneOnly( collection, {"_id": doc['_id']}, {'$set': obj}, upsert=False)
        if '__transaction' in doc:
            del(doc['__transaction'])
        return MongoDb.toJson(doc)

    ### 更新，返回更新后的整个对象，多数据量的更新不处理事务
    @deprecated
    def update(self, collection, query, obj, upsert=False):
        log.warn('Function update is deprecated, please use updateOneOnly updateOne updateMany!')
        doc = self.db[collection].find_and_modify(MongoDb.toBson(query), obj, upsert=upsert, new=True);
        if '__transaction' in doc:
            del(doc['__transaction'])
        return MongoDb.toJson(doc)

    ### 数量
    def query_count(self, collection, query):
        return self.db[collection].find(MongoDb.toBson(query)).count()

    def count(self, collection):
        return self.db[collection].count()

    ### 去重
    def distinct(self, collection, query=None, field=None):
        return self.db[collection].distinct(field, MongoDb.toBson(query))

    ### 更新many
    def update_many(self, collection, query, obj):
        doc = self.db[collection].update(MongoDb.toBson(query), obj, multi=True)
        return MongoDb.toJson(doc)

    ### 设置索引, eg. [("date", DESCENDING), ("author", ASCENDING)]
    def index(self, collection, query, **kwargs):
        self.db[collection].create_index(query, **kwargs);

    ### 查看索引
    def listIndex(self, collection):
        result = []
        items = self.db[collection].list_indexes()
        for item in items:
            result.append(item['key'])
        return result

    ### 唯一索引
    def unique(self, collection, key):
        self.db[collection].ensure_index(key, unique=True)

    ### ObjectId转换为字符串
    @staticmethod
    def toId(oid):
        if type(oid) == unicode  or type(oid) == dict or type(oid) == str:
            return oid
        id = eval(json_util.dumps(oid))
        return id['$oid']

    ### 字符串转换为ObjectId
    @staticmethod
    def toOId(id):
        oid = json_util.loads({'$oid': id})
        return oid

    ### 将Bson转换为普通json
    @staticmethod
    def toJson(obj):
        if obj.has_key('_id') and obj['_id']:
            obj['_id'] = MongoDb.toId(obj['_id'])
        for key in obj.iterkeys():
            if type(obj[key]) == list:
                for item in obj[key]:
                    try:
                        if item.has_key('_id') and item['_id']:
                            item['_id'] = MongoDb.toId(item['_id'])
                    except Exception:
                        continue
        return obj

    ### 将json转换为mongodb可用的bson
    @staticmethod
    def toBson(obj):
        ##modify by fangming.fm
        if obj.has_key('_id'):
            ##单id查询
            if isinstance(obj['_id'], ObjectId):
                pass
            elif isinstance(obj['_id'], str) or isinstance(obj['_id'], unicode):
                obj['_id'] = ObjectId(obj['_id'])
            ##id支持in条件查询
            elif obj['_id'].has_key('$in'):
                inobj = [];
                for _id in obj['_id']['$in']:
                    inobj.append(ObjectId(_id));
                obj['_id'] = {'$in': inobj};
                return obj;
            else:
                for k in obj['_id']:
                    obj['_id'][k] = ObjectId(obj['_id'][k])
                return obj;

        #obj = {'updateAt':{'$gt':'2017-01-01 00:00:00'}}
        if obj.has_key("updateAt") and isinstance(obj['updateAt'],dict):
            item = obj['updateAt']
            for key, value in item.items():
                if isinstance(value, str) or isinstance(value, unicode):
                    try:
                        item[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        item[key] = datetime.strptime(value.split('.')[0], "%Y-%m-%d %H:%M:%S")
            obj['updateAt'] = item

        if obj.has_key("createAt") and isinstance(obj['createAt'],dict):
            item = obj['createAt']
            for key, value in item.items():
                if isinstance(value, str) or isinstance(value, unicode):
                    try:
                        item[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        item[key] = datetime.strptime(value.split('.')[0], "%Y-%m-%d %H:%M:%S")
            obj['createAt'] = item
        if obj.has_key("shotTime") and obj['shotTime']:
            obj['shotTime'] = datetime.strptime(obj['shotTime'].split('.')[0], "%Y-%m-%d %H:%M:%S")
        return obj

    @staticmethod
    def sortToTuple(obj):
        sort = []
        for key, value in obj.items():
            item = (key, value)
            sort.append(item)
        return sort

    @staticmethod
    def aggregateJson(obj):
        '''
        :param obj: 
        :return: 
        '''
        for item in obj:
            match = item.get("$match")
            if match:
                updateAt = match.get("updateAt")
                if updateAt:
                    for key, value in updateAt.items():
                        match['updateAt'][key] = datetime.strptime(unquote(value).split('.')[0], "%Y-%m-%d %H:%M:%S")
                createAt = match.get("createAt")
                if createAt:
                    for key, value in createAt.items():
                        match['createAt'][key] = datetime.strptime(unquote(value).split('.')[0], "%Y-%m-%d %H:%M:%S")
        return obj

    def parse(self, obj):
        new_obj = {}
        for (k,v) in obj.items():
            if isinstance(v, dict):
                v = self.parse(v)
            if k=='@inc':
                new_obj['$inc'] = v
            elif k=='@set':
                new_obj['$set'] = v
            elif k=='@push':
                new_obj['$push'] = v
            elif k=='@pull':
                new_obj['$pull'] = v
            else:
                new_obj[k] = v
        return new_obj

## MySql封装
class MySqlDb(Db):
    def __init__(self, dbName):
        Db.__init__(self, dbName)


## SqlServer封装
class SqlServerDb(Db):
    def __init__(self, dbName):
        Db.__init__(self, dbName)