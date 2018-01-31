# -*- coding: utf-8 -*-
import json

from es_client import es_client
from elasticsearch import helpers


def search():
    es_search_options = set_search_optional()
    es_result = get_search_result(es_search_options)
    final_result = get_result_list(es_result)
    return final_result


def get_result_list(es_result):
    final_result = []
    for item in es_result:
        final_result.append(item['_source'])
    return final_result


def get_search_result(es_search_options, scroll='1m', index='user_index', doc_type='user', timeout="1m"):
    es_result = helpers.scan(
        client=es_client,
        query=es_search_options,
        scroll=scroll,
        index=index,
        doc_type=doc_type,
        timeout=timeout
    )
    return es_result


def set_search_optional():
    # 检索选项
    es_search_options = {
        "query": {
            "match_all": {}
        }
    }
    return es_search_options


if __name__ == '__main__':
    final_results = search()
    print len(final_results)
    print json.dumps(final_results, ensure_ascii=False)
