# -*- coding:utf-8 -*-

from app import create_app
from app.model.base_db import Result

app = create_app("develop")


with open('/home/user/linjr/cases_recommendation/data/jiedai/jiedai.txt', 'r') as f:
    num = 0
    for line in f.readlines():
        doc_id = line.split('+')[0]
        Result(model_id=str(num), doc_id=doc_id).save()
        num += 1

