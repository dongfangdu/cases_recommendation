from app.libs.common import get_config_dict
import http.client
import pymongo
import json


def es_conn():
    es_db = get_config_dict()["DATABASE_ES"]
    host = es_db['host']
    port = es_db['port']
    conn = http.client.HTTPConnection(host, port)
    return conn


def ner_conn():
    es_db = get_config_dict()["ENGINE_NER"]
    host = es_db['host']
    port = es_db['port']
    conn = http.client.HTTPConnection(host, port)
    return conn


def ner_post(text):
    data_dict = {"q": text}
    body = json.dumps(data_dict)
    ner_engine = get_config_dict()["ENGINE_NER"]
    index = ner_engine['index']
    url = '/%s' % index
    conn = ner_conn()
    httpHeaders = {'Content-Type': 'application/json'}
    conn.request(method='POST', url=url, body=body, headers=httpHeaders)
    response = conn.getresponse()
    return response


def es_search(body):
    es_db = get_config_dict()["DATABASE_ES"]
    index = es_db['index']
    httpHeaders = {'Content-Type': 'application/json'}
    url = '/%s/_search' % index
    conn = es_conn()
    conn.request(method='GET', url=url, body=body, headers=httpHeaders)
    response = conn.getresponse()
    return response


def rec_model_doc():
    es_db = get_config_dict()["DATABASE_COMMON"]
    host = es_db['host']
    port = es_db['port']
    client = pymongo.MongoClient("mongodb://%s:%s/" % (host, port))
    rec_db = client["recommend"]
    model_doc = rec_db["model_doc"]
    return model_doc


def rec_new_doc():
    es_db = get_config_dict()["DATABASE_COMMON"]
    host = es_db['host']
    port = es_db['port']
    client = pymongo.MongoClient("mongodb://%s:%s/" % (host, port))
    rec_db = client["recommend"]
    new_doc = rec_db["new_doc"]
    return new_doc
