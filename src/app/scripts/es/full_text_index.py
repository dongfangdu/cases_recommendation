# -*- coding:utf8 -*-

from app import create_app
from app.model.base_db import ModelDoc
from app.libs.common import get_config_dict
import http.client
import json
from flask import current_app
from app.libs.es import ner_conn, rec_model_doc, ner_post, es_search
import logging

app = create_app("develop")


def full_index(element_list, sort_element, sort_sc):
    element_str = " ".join(element for element in element_list)
    if sort_element == []:
        sort_dict = {}
    else:
        sort_dict = {sort_element[0]: {"order": sort_sc}}
    # data_dict = {"query": {"multi_match": {"query": "%s" % element_str, "fields": ["*"]}}}
    data_dict = {"query": {"multi_match": {"query": "%s" % element_str, "fields": ["*"]}}, "sort": sort_dict}
    body = json.dumps(data_dict)
    response = es_search(body)
    res = json.loads(response.read())
    hits = res['hits']['hits']
    docId_list = [dt['_source']['docId'] for dt in hits]
    return docId_list


def execute_index(element_dict, sort_element, sort_sc):
    data_list = []
    for key, value in element_dict.items():
        if key == "relaInfo_trialDate_start":
            data_list.append({"range": {"relaInfo_trialDate": {"gte": value, "format": "yyyy-MM-dd"}}})
        elif key == "relaInfo_trialDate_end":
            data_list.append({"range": {"relaInfo_trialDate": {"lte": value, "format": "yyyy-MM-dd"}}})
        elif key == "delay_pay_start":
            data_list.append({"range": {"delay_pay.amount": {"gte": value}}})
        elif key == "delay_pay_end":
            data_list.append({"range": {"delay_pay.amount": {"lte": value}}})
        elif key == "daily_rate_start":
            data_list.append({"range": {"daily_rate.rate_float": {"gte": value}}})
        elif key == "daily_rate_end":
            data_list.append({"range": {"daily_rate.rate_float": {"lte": value}}})
        elif key == "monthly_rate_start":
            data_list.append({"range": {"monthly_rate.rate_float": {"gte": value}}})
        elif key == "monthly_rate_end":
            data_list.append({"range": {"monthly_rate.rate_float": {"lte": value}}})
        elif key == "annual_rate_start":
            data_list.append({"range": {"annual_rate.rate_float": {"gte": value}}})
        elif key == "annual_rate_end":
            data_list.append({"range": {"annual_rate.rate_float": {"lte": value}}})
        else:
            data_list.append({"term": {key: value}})
    # current_app.logger.info(data_list)
    if sort_element == []:
        sort_dict = {}
    else:
        sort_dict = {sort_element[0]: {"order": sort_sc}}
    # data_dict = {"query": {"bool": {"must": data_list}}}
    data_dict = {"query": {"bool": {"must": data_list}}, "sort": sort_dict}
    body = json.dumps(data_dict)
    # logging.info(body)
    response = es_search(body)
    res = json.loads(response.read())
    # logging.info(res)
    hits = res['hits']['hits']
    docId_list = [dt['_source']['docId'] for dt in hits]
    return docId_list


def keyword_index(element_list, weight_list):
    data_list = []
    for element, weight in zip(element_list, weight_list):
        data_list.append({"term": {"element_query_v1.keyword": {"value": element, "boost": weight}}})
    data_dict = {"query": {"bool": {"minimum_should_match": 1, "should": data_list}}}
    # data_dict = {"query": {"terms": {"element_query_v1.keyword": element_list, "slop": 0}}}
    # data_dict = {"query": {"term": {"element_query_v1.keyword": "金融借款合同纠纷_借款利息_约定月利率超过10‰"}}}
    # data_dict = {"query": {"query_string": {"fields": ["element_query_v1"], "query":
    #     "民间借贷纠纷 and 金融借款合同纠纷_借款利息_约定月利率超过10‰ and 金融借款合同纠纷_借贷情况_借款金额500至1000万元"}}}
    body = json.dumps(data_dict)
    response = es_search(body)
    res = json.loads(response.read())
    hits = res['hits']['hits']
    docId_list = [dt['_source']['docId'] for dt in hits]
    return docId_list


if __name__ == "__main__":
    docId_list = full_index(["抵押", "质押"], "relaInfo_trialDate", "asc")
    print(docId_list)
    # execute_index({"relaInfo_court.keyword": "北京市朝阳区人民法院",
    #                "relaInfo_caseType.keyword": "民事案件",
    #                "relaInfo_reason.keyword": "金融借款合同纠纷",
    #                "relaInfo_trialRound.keyword": "一审",
    #                "relaInfo_trialDate_start": "2013-02-09",
    #                "relaInfo_trialDate_end": "2013-03-09",
    #                "relaInfo_docType.keyword": "判决书",
    #                "relaInfo_processType.keyword": "普通程序",
    #                "mortgage.goods.keyword": "房产",
    #                "pledge.goods.keyword": "汽车",
    #                "delay_pay_start": 1000,
    #                "delay_pay_end": 10000,
    #                "daily_rate_start": 0.0001,
    #                "daily_rate_end": 0.1,
    #                "monthly_rate_start": 0.01,
    #                "monthly_rate_end": 0.1,
    #                "annual_rate_start": 0.01,
    #                "annual_rate_end": 1 })

