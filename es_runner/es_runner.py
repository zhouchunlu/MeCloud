# coding=utf8
# pip install xpinyin
# pip install elasticsearch
# 　启动命令　nohup python -u es_runner.py &
import json
import threading
import traceback
import datetime

import time
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from xpinyin import Pinyin

# 建立到MongoDB的连接
# db = MongoClient('mongodb://127.0.0.1:27017')['blog']
db = MongoClient('mongodb://biliankeji:biliankeji@n01.me-yun.com:27017')['honey']

# 建立到Elasticsearch的连接
# hosts={"host": "127.0.0.1", "port": 9200}
es = Elasticsearch(hosts=[{'host': 't02.me-yun.com', 'port': 9200}])
print es
# 拼音
pinyin = Pinyin()

# 初始化索引的Mappings设置
_index_mappings = {
    "mappings": {
        "user": {
            "properties": {
                "username": {"type": "text"},
                "id": {"type": "text"}
            }
        }
    }
}
# es.indices.delete(index='user_index')
# 如果索引不存在，则创建索引
if es.indices.exists(index='user_index') is not True:
    es.indices.create(index='user_index', body=_index_mappings)


def processData():
    # 从MongoDB中查询数据，由于在Elasticsearch使用自动生成_id，因此从MongoDB查询
    while (True):
        user_cursor = db.UserInfo.find({'nickName': {'$exists': True}},
                                       projection={'nickName': True, 'user': True, 'avatar': True})
        # user_cursor = db.user.find({})
        print user_cursor
        user_docs = [x for x in user_cursor]
        print user_docs.__len__()
        processed = 0
        for doc in user_docs:
            try:
                print doc
                # print type(doc)
                # print doc['_id']
                print doc['nickName']
                print pinyin.get_pinyin(doc['nickName'], '')
                print pinyin.get_initials(doc['nickName'], '').lower()
                doc['pinyin'] = pinyin.get_pinyin(doc['nickName'], '')
                doc['pinyinsmall'] = pinyin.get_initials(doc['nickName'], '').lower()
                doc['id'] = str(doc['_id'])
                # 返回的结果中将_id去掉.否则存入essearch会格式化报错
                del doc['_id']
                es.index(index='user_index', doc_type='user', refresh=True, body=doc, id=doc['id'])
                processed += 1
                print('Processed: ' + str(processed))

            except Exception, e:
                print e
                msg = traceback.format_exc()
                print msg
        print('finish at ', datetime.datetime.now())
        time.sleep(10)


# 删除索引的语句
# es.indices.delete(index='user_index')
threads = []
t1 = threading.Thread(target=processData)
threads.append(t1)

if __name__ == '__main__':
    processData()
    # for t in threads:
    #     t.setDaemon(False)
    #     t.start()
