# -*- coding: utf-8 -*-
import elasticsearch

ES_SERVERS = [{
    'host': 'localhost',
    'port': 9200
}]

es_client = elasticsearch.Elasticsearch(
    hosts=ES_SERVERS
)