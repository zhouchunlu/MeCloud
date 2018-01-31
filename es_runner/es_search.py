# coding=utf8
import json
import traceback
from pymongo import MongoClient
from elasticsearch import Elasticsearch

# 建立到Elasticsearch的连接
es = Elasticsearch()
query_keywords_contains = {
    'query': {
        'multi_match': {
            "query": "爹",
            "fields": ["nickName", "pinyin", "pinyinsmall"],
            "fuzziness": "AUTO"
        }
    },
    'size': 5,
    "sort": [
        {"_score": {"order": "desc"}}
    ]
}

query_all = {
    'query': {
        'match_all': {}
    },
    'size': 5
}
searched = es.search(index='user_index', doc_type='user', body=query_keywords_contains, scroll='3m')
print searched['_scroll_id']
json_str = json.dumps(searched, ensure_ascii=False)
print json_str

# scroll_searched1 = es.scroll(scroll_id=searched['_scroll_id'], scroll='3m')
#
# print json.dumps(scroll_searched1, ensure_ascii=False)
#
# scroll_searched2 = es.scroll(scroll_id=scroll_searched1['_scroll_id'], scroll='3m')
#
# print json.dumps(scroll_searched2, ensure_ascii=False)
