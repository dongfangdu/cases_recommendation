# -*- coding:utf-8 -*-

from app import create_app
from app.model.base_db import Result

app = create_app("default")

with open('../../../../data/jiedai.txt', 'r') as f:
    num = 0
    for line in f.readlines():
        doc_id = line.split('+doc_id+')[0]
        Result(model_id=str(num), doc_id=doc_id).save()
        num += 1

