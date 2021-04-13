# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings('ignore')
from app.libs.es import rec_model_doc

model_doc = rec_model_doc()
i = 0
for info in model_doc.find({}, {"docId": 1, "relaInfo_docCont": 1,
                           "daily_rate": 1, "monthly_rate": 1, "annual_rate": 1, "appeal_amount": 1, "affirm_amount": 1,
                            "judge_amount": 1}, no_cursor_timeout=True):
    # print(info)
    docId = info['docId']
    # print(docId)
    try:
        relaInfo = info['relaInfo_docCont']
        for rela in relaInfo:
            if rela['name'] == '案由':
                relaInfo_reason = rela['value'][0]
        # print(relaInfo)
        # print(relaInfo_reason)
        element_query = []
        if "monthly_rate" in info.keys():
            monthly_rate = info['monthly_rate']['rate_float']
            if relaInfo_reason == "金融借款合同纠纷":
                if monthly_rate < 0.005:
                    element_query.append("金融借款合同纠纷_借款利息_约定月利率不足5‰")
                elif monthly_rate >= 0.005 and monthly_rate < 0.008:
                    element_query.append("金融借款合同纠纷_借款利息_约定月利率5至8‰")
                elif monthly_rate >= 0.008 and monthly_rate < 0.01:
                    element_query.append("金融借款合同纠纷_借款利息_约定月利率8至10‰")
                elif monthly_rate >= 0.01:
                    element_query.append("金融借款合同纠纷_借款利息_约定月利率超过10‰")

        if "annual_rate" in info.keys():
            annual_rate = info['annual_rate']['rate_float']
            if relaInfo_reason == "金融借款合同纠纷":
                if monthly_rate < 0.05:
                    element_query.append("金融借款合同纠纷_借款利息_约定年利率不足5%")
                elif monthly_rate >= 0.05 and monthly_rate < 0.08:
                    element_query.append("金融借款合同纠纷_借款利息_约定年利率5至8%")
                elif monthly_rate >= 0.08 and monthly_rate < 0.1:
                    element_query.append("金融借款合同纠纷_借款利息_约定年利率8至10%")
                elif monthly_rate >= 0.1:
                    element_query.append("金融借款合同纠纷_借款利息_约定年利率超过10%")
            elif relaInfo_reason == "民间借贷纠纷":
                if monthly_rate < 0.24:
                    element_query.append("民间借贷纠纷_借款利息_年利率未超过24%")
                elif monthly_rate >= 0.36:
                    element_query.append("民间借贷纠纷_借款利息_年利率36%以上")

        if "appeal_amount" in info.keys():
            appeal_amount = info['appeal_amount']['amount']
            if relaInfo_reason == "金融借款合同纠纷":
                if appeal_amount < 500000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额不足50万元")
                elif appeal_amount >= 500000 and appeal_amount < 1000000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额50至100万元")
                elif appeal_amount >= 1000000 and appeal_amount < 5000000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额100至500万元")
                elif appeal_amount >= 5000000 and appeal_amount < 10000000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额500至1000万元")
                elif appeal_amount >= 10000000 and appeal_amount < 50000000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额1000至5000万元")
                elif appeal_amount >= 50000000:
                    element_query.append("金融借款合同纠纷_借贷情况_借款金额超过5000万")
        # print(monthly_rate)
        # print(annual_rate)
        # print(appeal_amount)
        # print(element_query)
        model_doc.update_one({"docId": docId}, {"$set": {"element_query_v1": element_query}})
    except:
        i += 1
        print(i)
        print(docId)
