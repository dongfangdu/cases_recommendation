# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings('ignore')
import re
import pymongo
from app.scripts.recommend.recommend import Recommend
from app.libs.common import get_config_dict
from app.libs.es import ner_conn, rec_model_doc, ner_post
import json
from app.scripts.es.num_converter import _format_sentence


# client = pymongo.MongoClient("mongodb://192.168.106.170:27017/")
# rec_db = client["recommend"]
# model_doc = rec_db["model_doc"]
# httpHeaders = {'Content-Type': 'application/json'}
# url = ner_url()
# conn = ner_conn()

model_doc = rec_model_doc()

horse_list = ['房产', '房产证', '房权证', '商品房', '住房', '自有住房', '房地产', '房地产权证', '厂房', '房子', '房屋']
car_list = ['车辆', '汽车', '小汽车', '轿车', '小轿车', '机动车', '客车', '大客车']
equity_list = ['股权', '期权', '股票']


def update_mortgage_pledge(search_dict):
    i = 0
    for info in model_doc.find({}, {"docId": 1, "docContent": 1}, no_cursor_timeout=True):
        docId = info['docId']
        docContent = info['docContent']
        # print(docId)
        i += 1
        if i % 1000 == 0:
            print(i)
        # print(docContent)
        for key, value in search_dict.items():
            # print(key, value)
            # print("="*30)
            if value in docContent:
                pattern = re.compile('[，；。][^，；。]*%s[^，；。]*[，；。]' % value)
                mortgage_list = re.findall(pattern, docContent)
                ele_list = []
                for mortgage in mortgage_list:
                    # print(mortgage)
                    # data_dict = {"q": mortgage}
                    # body = json.dumps(data_dict)
                    # url = '/%s' % index
                    # conn.request(method='POST', url=url, body=body, headers=httpHeaders)
                    # response = conn.getresponse()
                    response = ner_post(mortgage)
                    res = json.loads(response.read())
                    entities = res['entities']
                    for msg in entities:
                        ele_list.append(msg['value'])
                ele_list = list(set(ele_list))
                e_horse_list = [x for x in ele_list if x in horse_list]
                e_car_list = [x for x in ele_list if x in car_list]
                e_equity_list = [x for x in ele_list if x in equity_list]
                # print(e_horse_list, e_car_list, e_equity_list)
                if e_horse_list != []:
                    model_doc.update_one({"docId": docId}, {"$set": {key: '房产'}})
                elif e_car_list != []:
                    model_doc.update_one({"docId": docId}, {"$set": {key: '汽车'}})
                elif e_equity_list != []:
                    model_doc.update_one({"docId": docId}, {"$set": {key: '股权'}})


def update_rate_insert(search_dict):
    i = 0
    for info in model_doc.find({}, {"docId": 1, "docContent": 1}, no_cursor_timeout=True):
        docId = info['docId']
        docContent = info['docContent']
        # print(docId)
        i += 1
        if i % 1000 == 0:
            print(i)
        # print(docContent)
        for key, value in search_dict.items():
            # print(key, value)
            total_rate_list = []
            for val in value:
                # print(val)
                # print("="*30)
                if val in docContent:
                    pattern = re.compile('[;，；。][^;，；。]*%s[^;，；。]*[;，；。]' % val)
                    # pattern = re.compile('[，；。][^，；。]*月利率[^，；。]*?[，；。]')
                    rate_list = re.findall(pattern, docContent)
                    # print(rate_list)
                    rate_list = [m for m in rate_list if "中国人民银行" not in m]
                    total_rate_list.extend(rate_list)
            # print(total_rate_list)
            _total_rate_list = []
            for simp_info in total_rate_list:
                simp_info = re.sub(r"上浮\d+(\.\d+)?[%‰]", "", simp_info)
                simp_info = re.sub(r"加收\d+(\.\d+)?[%‰]", "", simp_info)
                # data_dict = {"q": simp_info}
                # body = json.dumps(data_dict)
                # url = '/%s' % index
                # conn.request(method='POST', url=url, body=body, headers=httpHeaders)
                # response = conn.getresponse()
                response = ner_post(simp_info)
                res = json.loads(response.read())
                entities = res['entities']
                # print(entities)
                if entities != []:
                    for msg in entities:
                        if msg['entity'] == 'loan-interest':
                            current_start = msg['start']
                            current_loc = entities.index(msg)
                            # print(current_loc)
                            if current_loc == 0:
                                _total_rate_list.append(simp_info)
                            else:
                                front = entities[current_loc-1]
                                # print(front)
                                front_end = front['end']
                                # print(current_start, front_end)
                                if current_start >= front_end:
                                    _total_rate_list.append(simp_info)
            # print(_total_rate_list)
            if _total_rate_list != []:
                total_rate_val_list = []
                for _val in _total_rate_list:
                    rate_pattern = re.compile(r'(\d+(\.\d+)?[%‰])')
                    rate_val_list = [m[0] for m in re.findall(rate_pattern, _val)]
                    # rate_val_list = re.findall(rate_pattern, _val)
                    total_rate_val_list.extend(rate_val_list)
                # total_rate_val_list = list(set(total_rate_val_list))
                # print(total_rate_val_list)
                if total_rate_val_list != []:
                    rate = max(total_rate_val_list, key=total_rate_val_list.count)
                    print([docId, key, val, rate])
                    model_doc.update_one({"docId": docId}, {"$set": {key: rate}})


def update_delay_pay(search_dict):
    i = 0
    for info in model_doc.find({}, {"docId": 1, "docContent": 1}, no_cursor_timeout=True):
        docId = info['docId']
        docContent = info['docContent']
        print(docId)
        i += 1
        if i % 10 == 0:
            print(i)
        # print(docContent)
        for key, value in search_dict.items():
            # print(key, value)
            # print("="*30)
            if value in docContent:
                pattern = re.compile(r'(%s\d+(\.\d+)?元)' % value)
                # print(pattern)
                # pattern = re.compile('[，；。][^，；。]*%s[^，；。]*[，；。]' % value)
                delay_pay_list = [m[0] for m in re.findall(pattern, docContent)]
                delay_pay_list = list(set(delay_pay_list))
                print(delay_pay_list)
                val_pattern = re.compile(r'(\d+(\.\d+)?)')
                total_delay_pay_val_list = []
                for delay_pay_val in delay_pay_list:
                    delay_pay_val_list = [m[0] for m in re.findall(val_pattern, delay_pay_val)]
                    total_delay_pay_val_list.extend(delay_pay_val_list)
                print(total_delay_pay_val_list)
                if total_delay_pay_val_list != []:
                    model_doc.update_one({"docId": docId}, {"$set": {key: total_delay_pay_val_list}})


def update_amount(search_dict):
    i = 0
    for info in model_doc.find({}, {"docId": 1, "elemParaIndex": 1}, no_cursor_timeout=True):
        docId = info['docId']
        elemParaIndex = info['elemParaIndex']
        plaintiffClaim = "".join(json.loads(elemParaIndex['plaintiffClaim']).values())
        courtFact = "".join(json.loads(elemParaIndex['courtFact']).values())
        courtJudgment = "".join(json.loads(elemParaIndex['courtJudgment']).values())
        # print(plaintiffClaim)
        # print(courtFact)
        # print(courtJudgment)
        # print("=" * 30)
        # print(docId)
        i += 1
        if i % 1000 == 0:
            print(i)
        # print(docContent)
        for key, value in search_dict.items():
            # print(key, value)
            if key == "appeal_amount":
                amount = doc_to_money(plaintiffClaim)
                # print(amount)
            elif key == "affirm_amount":
                amount = doc_to_money(courtFact)
                # print(amount)
            elif key == "judge_amount":
                amount = doc_to_money(courtJudgment)
                # print(amount)
            model_doc.update_one({"docId": docId}, {"$set": {key: amount}})


def doc_to_money(text):
    # data_dict = {"q": text}
    # body = json.dumps(data_dict)
    # url = '/%s' % index
    # conn.request(method='POST', url=url, body=body, headers=httpHeaders)
    # response = conn.getresponse()
    response = ner_post(text)
    res = json.loads(response.read())
    entities = res['entities']
    money_list = [m['value'] for m in entities if m['entity'] == 'Money']
    # print(money_list)
    money_list = [_format_sentence(m) for m in money_list]
    # print(money_list)
    if money_list != []:
        money = max(money_list)
    else:
        money = 0
    return money


if __name__ == "__main__":
    # update_mortgage_pledge({'mortgage': '抵押', 'pledge': '质押'})
    # update_delay_pay({'delay_pay': '滞纳金'})
    # update_rate_insert({'daily_rate': ['日息', '日利率', '日利息'], 'monthly_rate': ['月息', '月利率', '月利息'], 'annual_rate': ['年息', '年利率', '年利息']})
    update_amount({'appeal_amount': '诉请金额', 'affirm_amount': '认定金额', 'judge_amount': '判决金额'})

