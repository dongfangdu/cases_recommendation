# -*- coding:utf8 -*-

from app import create_app
from app.model.base_db import ModelDoc
from app.libs.common import get_config_dict
import http.client
import json

app = create_app("develop")
data = ModelDoc.objects().limit(100)
es_db = get_config_dict()["DATABASE_ES"]
host = es_db['host']
port = es_db['port']
index = es_db['index']
httpHeaders = {'Content-Type': 'application/json'}
conn = http.client.HTTPConnection(host, port)

for data_info in data:
    # _id = str(data_info._id)
    docId = data_info.docId
    doc_name = data_info.doc_name
    docContent = data_info.docContent
    relaInfo = data_info.relaInfo
    relaInfo_date = relaInfo[4]['value'].replace('-', '')
    relaInfo[4]['value'] = relaInfo_date
    legalBase = data_info.legalBase
    data_dict = {'docId': docId,
                 'doc_name': doc_name,
                 'docContent': docContent,
                 'relaInfo': relaInfo,
                 'legalBase': legalBase}
    body = json.dumps(data_dict)
    url = '/%s/_doc/%s' % (index, docId)
    conn.request(method='PUT', url=url, body=body, headers=httpHeaders)
    response = conn.getresponse()
    res = response.read()
    print(res)
