# -*- coding: utf-8 -*-

import time
from datetime import datetime
from flask_mongoengine import MongoEngine
from app.libs.response_code import error_map

db = MongoEngine()


def timestamp_to_date(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


class Result(db.Document):
    meta = {
        'collection': 'result',
        'ordering': ['-create_at'],
        'strict': False,
    }
    model_id = db.StringField()
    doc_id = db.StringField()
    score = db.StringField()


class ModelDoc(db.Document):
    meta = {
        'collection': 'model_doc',
        # 'ordering': ['-create_at'],
        'strict': False,
    }
    docId = db.StringField()
    doc_name = db.StringField()
    docContent = db.StringField()
    relaInfo = db.ListField()
    legalBase = db.ListField()
    relaInfo_court = db.StringField()
    relaInfo_caseType = db.StringField()
    relaInfo_reason = db.StringField()
    relaInfo_trialRound = db.StringField()
    relaInfo_trialDate = db.StringField()
    relaInfo_appellor = db.StringField()
    relaInfo_docType = db.StringField()
    relaInfo_processType = db.StringField()
    relaInfo_docCont = db.ListField()
    roleInfo = db.ListField()
    mortgage = db.ListField()
    pledge = db.ListField()
    delay_pay = db.ListField()
    daily_rate = db.ListField()
    monthly_rate = db.ListField()
    annual_rate = db.ListField()
    appeal_amount = db.ListField()
    affirm_amount = db.ListField()
    judge_amount = db.ListField()

    def to_dict_list(self):
        res_data = {
            "docId": self.docId,
            "doc_name": self.doc_name,
        }
        return res_data

    def to_dict_detail(self):
        res_data = {
            "docId": self.docId,
            "doc_name": self.doc_name,
            "docContent": self.docContent,
            "legalBase": self.legalBase,
            "relaInfo_court": self.relaInfo_court,
            "relaInfo_caseType": self.relaInfo_caseType,
            "relaInfo_reason": self.relaInfo_reason,
            "relaInfo_trialRound": self.relaInfo_trialRound,
            "relaInfo_trialDate": self.relaInfo_trialDate,
            "relaInfo_appellor": self.relaInfo_appellor,
            "relaInfo_docType": self.relaInfo_docType,
            "relaInfo_processType": self.relaInfo_processType,
            "roleInfo": self.roleInfo,
            'mortgage': self.mortgage,
            'pledge': self.pledge,
            'delay_pay': self.delay_pay,
            'daily_rate': self.daily_rate,
            'monthly_rate': self.monthly_rate,
            'annual_rate': self.annual_rate,
            'appeal_amount': self.appeal_amount,
            'affirm_amount': self.affirm_amount,
            'judge_amount': self.judge_amount,
        }
        return res_data


class NewDoc(db.Document):
    meta = {
        'collection': 'new_doc',
        'ordering': ['-create_at'],
        # 'index_background': True,
        # "indexes": [
        #     {'fields': ('create_at'), 'unique': True, 'sparse': True},  # sparse 稀疏索引，允许值为空
        # ],
        'strict': False,
    }
    docId = db.StringField(unique=True)
    doc_name = db.StringField()
    docContent = db.StringField()
    create_at = db.FloatField(default=time.time())
    element = db.ListField()
    newdoc_status = db.StringField()
    recommend_status = db.StringField()
    recommend = db.ListField()
    relaInfo_docCont = db.ListField()
    roleInfo = db.ListField()
    mortgage = db.ListField()
    pledge = db.ListField()
    delay_pay = db.ListField()
    daily_rate = db.ListField()
    monthly_rate = db.ListField()
    annual_rate = db.ListField()
    appeal_amount = db.ListField()
    affirm_amount = db.ListField()
    judge_amount = db.ListField()

    def to_dict_list(self):
        res_data = {
            "docId": self.docId,
            "doc_name": self.doc_name,
            "create_at": timestamp_to_date(self.create_at),
            "newdoc_status": error_map[self.newdoc_status],
            "recommend_status": error_map[self.recommend_status],
        }
        return res_data

    def to_dict_detail(self):
        res_data = {
            "docId": self.docId,
            "doc_name": self.doc_name,
            "docContent": self.docContent,
            "element": self.element,
            "recommend": self.recommend,
            "relaInfo_docCont": self.relaInfo_docCont,
            "roleInfo": self.roleInfo,
            'mortgage': self.mortgage,
            'pledge': self.pledge,
            'delay_pay': self.delay_pay,
            'daily_rate': self.daily_rate,
            'monthly_rate': self.monthly_rate,
            'annual_rate': self.annual_rate,
            'appeal_amount': self.appeal_amount,
            'affirm_amount': self.affirm_amount,
            'judge_amount': self.judge_amount,
        }
        return res_data
