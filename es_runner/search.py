# -*- coding: utf-8 -*-
import json

from es_client import es_client


def query_Data(mindex, mtype, msize=2):
    '''''查询数据库中指定表所有字段出现的值
    :mindex 查询的数据库
    :mtype 查询的数据库表
    :mstr 匹配的字段
    :mfrom 返回的起始位置
    :msize 需要查询的总条数
    return 返回一个dict
    '''
    if not es_client:
        return False
    if not (mindex and mtype):
        return False
    data = []
    try:
        # querydata = es_client.search(index=mindex, doc_type=mtype, scroll='5m', timeout='3s', \
        #                              body={"query": {
        #                                  "bool": {
        #                                      "must": [{"query_string": {"default_field": "_all", "query": mstr}}]}},
        #                                  "size": msize})
        querydata = es_client.search(index=mindex, doc_type=mtype, scroll='5m', timeout='3s', \
                                     body={"query": {"match_all": {}},
                                           "size": msize})
        print json.dumps(querydata, ensure_ascii=False)
        mdata = querydata.get("hits").get("hits")
        if not mdata:
            return -1  # 没有查询到数据
        # 解析返回的值
        data = [d.get("_source") for d in mdata]
        sid = querydata['_scroll_id']
        while True:
            rs = es_client.scroll(scroll_id=sid, scroll='10s')
            temp = rs.get("hits").get("hits")
            if not temp:
                break
            data += [d.get("_source") for d in temp]
        print("共查询到: %d条数据" % data.__len__())
        return data
    except Exception as ex:
        print("Elasticsearch数据库查询发生异常" + str(ex))
        return False


if __name__ == '__main__':
    query_Data('user_index', 'user', msize=2)
