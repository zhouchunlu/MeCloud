# coding=utf8
import json
import traceback
from pymongo import MongoClient
from elasticsearch import Elasticsearch

# 建立到MongoDB的连接
_db = MongoClient('mongodb://127.0.0.1:27017')['blog']

# 建立到Elasticsearch的连接
_es = Elasticsearch()

# 初始化索引的Mappings设置
_index_mappings = {
    "mappings": {
        "user": {
            "properties": {
                "title": {"type": "text"},
                "name": {"type": "text"},
                "age": {"type": "integer"}
            }
        },
        "blogpost": {
            "properties": {
                "title": {"type": "text"},
                "body": {"type": "text"},
                "user_id": {
                    "type": "keyword"
                },
                "created": {
                    "type": "date"
                }
            }
        }
    }
}

# 如果索引不存在，则创建索引
if _es.indices.exists(index='blog_index') is not True:
    _es.indices.create(index='blog_index', body=_index_mappings)

# 从MongoDB中查询数据，由于在Elasticsearch使用自动生成_id，因此从MongoDB查询
# 返回的结果中将_id去掉。
user_cursor = _db.user.find({}, projection={'acl': False, 'password': False})
# user_cursor = _db.user.find({})
print user_cursor
user_docs = [x for x in user_cursor]
print user_docs.__len__()

# 记录处理的文档数
processed = 0
# 将查询出的文档添加到Elasticsearch中
for _doc in user_docs:
    try:
        print _doc
        print type(_doc)
        print _doc['_id']
        _doc['id'] = str(_doc['_id'])
        del _doc['_id']
        # print _doc
        # 将refresh设为true，使得添加的文档可以立即搜索到；
        # 默认为false，可能会导致下面的search没有结果
        _es.index(index='blog_index', doc_type='user', refresh=True, body=_doc, id=_doc['id'])
        processed += 1
        print('Processed: ' + str(processed))
    except:
        traceback.print_exc()
# _es.indices.delete(index='blog_index')
print _es.indices.exists(index='blog_index')
# 查询所有记录结果
print('Search all...')
_query_all = {
    'query': {
        'match_all': {}
    }
}
_searched = _es.search(index='blog_index', doc_type='user', body=_query_all)
print(_searched)
print json.dumps(_searched, ensure_ascii=False)
print _searched['hits']['hits'].__len__()


# 输出查询到的结果
for hit in _searched['hits']['hits']:
    print('Search name contains gs.')
    _query_name_contains = {
        'query': {
            'match': {
                'username': 'gs'
            }
        }
    }
    _searched = _es.search(index='blog_index', doc_type='user', body=_query_name_contains)
    print(_searched)
