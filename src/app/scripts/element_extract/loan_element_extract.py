# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings('ignore')
import re
from app.libs.es import rec_model_doc, rec_new_doc
import json
from app.scripts.es.num_converter import _format_sentence
import copy
from app.scripts.recommend.corpus_prepare import process_lac_per_sent


house_list = ['房产', '房产证', '房权证', '商品房', '住房', '自有住房', '房地产', '房地产权证', '厂房', '房子', '房屋']
car_list = ['车辆', '汽车', '小汽车', '轿车', '小轿车', '机动车', '客车', '大客车']
equity_list = ['股权', '期权', '股票']
goods_dict = {"房产": house_list, "汽车": car_list, "股权": equity_list}

daily_rate_list = ['日息', '日利率', '日利息']
monthly_rate_list = ['月息', '月利率', '月利息']
annual_rate = ['年息', '年利率', '年利息']
rate_dict = {"日利率": daily_rate_list, "月利率": monthly_rate_list, "年利率": annual_rate}


def merge_value(info):
    new_info = []
    val_list = []
    for inf in info:
        value = inf["value"]
        if value not in val_list:
            val_list.append(value)
            new_info.append(copy.deepcopy(inf))
        else:
            for new_inf in new_info:
                if new_inf["value"] == value:
                    new_inf["location"].extend(inf["location"])
    return new_info


def gen_location(clause, value, clause_idx):
    location = []
    find_start = 0
    while True:
        start = clause.find(value, find_start)
        # print(start)
        if start == -1:
            break
        end = start + len(value)
        location.append({"clause_idx": clause_idx, "start": start, "end": end})
        find_start = start + 1
    return location


class update_mortgage_pledge():
    def __init__(self):
        pass

    def gen_info(self, clause, clause_idx):
        goods = []
        info = []
        for goods_type, goods_val_list in goods_dict.items():
            for goods_val in goods_val_list:
                # print(goods_val)
                if goods_val not in clause:
                    continue
                goods.append(goods_type)
                location = gen_location(clause, goods_val, clause_idx)
                info.append({"type": goods_type, "value": goods_val, "location": location})
        return goods, info

    def gen_total_info_and_save(self, key, value, clauseList, table, docId):
        total_goods = []
        total_info = []
        for clause_idx, clause in enumerate(clauseList):
            if value not in clause:
                continue
            # print(clause)
            goods, info = self.gen_info(clause, clause_idx)
            total_goods.extend(goods)
            total_info.extend(info)
        goods = list(set(total_goods))
        info = merge_value(total_info)
        print({"goods": goods, "info": info})
        if goods != []:
            table.update_one({"docId": docId}, {"$set": {key: {"goods": goods, "info": info}}})

    def main(self, table, doc_Id, search_dict):
        i = 0
        for info in table.find({'docId': doc_Id}, {"docId": 1, "clauseList": 1}, no_cursor_timeout=True):
            docId = info['docId']
            clauseList = info['clauseList']
            print(docId)
            i += 1
            if i % 1000 == 0:
                print(i)
            for key, value in search_dict.items():
                self.gen_total_info_and_save(key, value, clauseList, table, docId)


class update_rate_insert():
    def __init__(self):
        pass

    def clause_update(self, clause):
        clause = re.sub(r"上浮\d+(\.\d+)?[%‰]", "", clause)
        clause = re.sub(r"加收\d+(\.\d+)?[%‰]", "", clause)
        clause = re.sub(r"\d+年\d+月\d+日", "", clause)
        return clause

    def gen_info(self, new_rate_dict, clause_idx, ini_clause, update_clause):
        tot_rate_list = []
        info = []
        for rate_type, rate_type_value in new_rate_dict.items():
            new_rate_type_value = [_v for _v in rate_type_value if (_v in update_clause and "中国人民银行" not in update_clause)]
            for val in new_rate_type_value:
                rate_pattern = re.compile(r'(\d+(\.\d+)?[%‰])')
                rate_val_list = [m[0] for m in re.findall(rate_pattern, update_clause)]
                tot_rate_list.extend(rate_val_list)
                for rate_val in rate_val_list:
                    location = gen_location(ini_clause, rate_val, clause_idx)
                    info.append({"type": val, "value": rate_val, "location": location})
        return tot_rate_list, info

    def rate_2_ratefloat(self, rate):
        rate_float = float(re.sub(r"[%‰]", "", rate))
        if "%" in rate:
            rate_float = round(rate_float / 100, len(str(rate_float).split(".")[1]) + 2)
        elif "‰" in rate:
            rate_float = round(rate_float / 1000, len(str(rate_float).split(".")[1]) + 3)
        else:
            rate_float = 0
        return rate_float

    def gen_total_info_and_save(self, key, value, clauseList, table, docId):
        total_info = []
        total_rate_list = []
        for clause_idx, ini_clause in enumerate(clauseList):
            update_clause = self.clause_update(ini_clause)
            new_rate_dict = {_k: _v for _k, _v in rate_dict.items() if _k == value}
            tot_rate_list, info = self.gen_info(new_rate_dict, clause_idx, ini_clause, update_clause)
            total_rate_list.extend(tot_rate_list)
            total_info.extend(info)
        if total_rate_list != []:
            rate = max(total_rate_list, key=total_rate_list.count)
            rate_float = self.rate_2_ratefloat(rate)
            info = merge_value(total_info)
            print({"rate": rate, "rate_float": rate_float, "info": info})
            table.update_one({"docId": docId}, {"$set": {key: {"rate": rate, "rate_float": rate_float, "info": info}}})

    def main(self, table, doc_Id, search_dict):
        i = 0
        for info in table.find({'docId': doc_Id}, {"docId": 1, "clauseList": 1}, no_cursor_timeout=True):
            docId = info['docId']
            clauseList = info['clauseList']
            # print(docId)
            i += 1
            if i % 1000 == 0:
                print(i)
            for key, value in search_dict.items():
                self.gen_total_info_and_save(key, value, clauseList, table, docId)


class update_delay_pay():
    def __init__(self):
        pass

    def gen_info_and_save(self, key, value, clauseList, table, docId):
        info = []
        total_delay_pay_list = []
        total_delay_pay_val_list = []
        for clause_idx, clause in enumerate(clauseList):
            if value not in clause:
                continue
            pattern = re.compile(r'(%s\d+(\.\d+)?元)' % value)
            delay_pay_list = [m[0] for m in re.findall(pattern, clause)]
            total_delay_pay_list.extend(delay_pay_list)
            for delay_pay_ele in delay_pay_list:
                location = gen_location(clause, delay_pay_ele, clause_idx)
                info.append({"type": value, "value": delay_pay_ele, "location": location})

        if total_delay_pay_list != []:
            val_pattern = re.compile(r'(\d+(\.\d+)?)')
            for delay_pay_val in total_delay_pay_list:
                delay_pay_val_list = [m[0] for m in re.findall(val_pattern, delay_pay_val)]
                total_delay_pay_val_list.extend(delay_pay_val_list)
            total_delay_pay_val_list = [float(m) for m in total_delay_pay_val_list]
            amount = max(total_delay_pay_val_list)
            info = merge_value(info)
            print({"amount": amount, "info": info})
            table.update_one({"docId": docId}, {"$set": {key: {"amount": amount, "info": info}}})

    def main(self, table, doc_Id, search_dict):
        i = 0
        for info in table.find({'docId': doc_Id}, {"docId": 1, "clauseList": 1}, no_cursor_timeout=True):
            docId = info['docId']
            clauseList = info['clauseList']
            # print(docId)
            i += 1
            if i % 1000 == 0:
                print(i)
            for key, value in search_dict.items():
                self.gen_info_and_save(key, value, clauseList, table, docId)


class update_amount():
    def __init__(self):
        pass

    def text_to_money(self, elemParaIndex_info, clauseList, value):
        clause_idx_list = []
        for clause_info in elemParaIndex_info:
            clause_idx_list.extend(clause_info['clause_num'])
        total_money_list = []
        total_info = []
        for clause_idx in clause_idx_list:
            clause = clauseList[int(clause_idx)]
            res_money_list = process_lac_per_sent(clause)
            money_list = [res_money_list[0][n] for n, m in enumerate(res_money_list[1]) if m == "MONEY"]
            # print(money_list)
            total_money_list.extend(money_list)
            info = []
            for money in money_list:
                location = gen_location(clause, money, clause_idx)
                money_float = _format_sentence(money)
                info.append({"type": value, "value": money, "value_float": money_float, "location": location})
            total_info.extend(info)
        total_info = merge_value(total_info)
        total_money_list = [_format_sentence(m) for m in total_money_list]
        # print(total_money_list)
        if total_money_list != []:
            amount = max(total_money_list)
        else:
            amount = 0
        return amount, total_info

    def main(self, table, doc_Id, search_dict):
        i = 0
        for info in table.find({"docId": doc_Id, "schema_version": {"$ne": "2.0"}}, {"docId": 1, "clauseList": 1, "elemParaIndex": 1}, no_cursor_timeout=True):
            docId = info['docId']
            clauseList = info['clauseList']
            elemParaIndex = info['elemParaIndex']
            plaintiffClaim = elemParaIndex['plaintiffClaim']
            courtFact = elemParaIndex['courtFact']
            courtJudgment = elemParaIndex['courtJudgment']
            i += 1
            if i % 100 == 0:
                print(i)
            # print(docContent)
            for key, value in search_dict.items():
                # print(key, value)
                if key == "appeal_amount":
                    amount, info = self.text_to_money(plaintiffClaim, clauseList, value)
                    print({"amount": amount, "info": info})
                elif key == "affirm_amount":
                    amount, info = self.text_to_money(courtFact, clauseList, value)
                    print({"amount": amount, "info": info})
                elif key == "judge_amount":
                    amount, info = self.text_to_money(courtJudgment, clauseList, value)
                    print({"amount": amount, "info": info})
                table.update_one({"docId": docId}, {"$set": {key: {"amount": amount, "info": info}}})


if __name__ == "__main__":
    new_doc = rec_new_doc()
    # model_doc = rec_model_doc()
    # update_mortgage_pledge().main(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9", {'mortgage': '抵押', 'pledge': '质押'})
    update_delay_pay().main(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9", {'delay_pay': '滞纳金'})
    # update_rate_insert().main(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9", {'daily_rate': '日利率', 'monthly_rate': '月利率', 'annual_rate': '年利率'})
    # update_amount().main(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9", {'appeal_amount': '诉请金额', 'affirm_amount': '认定金额', 'judge_amount': '判决金额'})
