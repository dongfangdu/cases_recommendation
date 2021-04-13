import os
from pprint import pprint
import json
import traceback
import re
from app.libs.es import rec_new_doc


###### extract relaInfo from doc_Content
class RelaInfo_FromDocCont:
    def __init__(self, paraHeaderList, paraTailList, clauseList):
        self.paraHeaderList = paraHeaderList
        self.paraTailList = paraTailList
        self.clauseList = clauseList


    @staticmethod
    def Infodict_update(name, key, value, location, span):
        return {'name': name, 'key': key, 'value': value, 'location': location, 'span': span}


    def court(self):
        pattern = '.*?法院'
        pattern = re.compile(pattern)
        location = {'Header': []}
        span = []
        court = []
        try:
            for i, paragraph in enumerate(self.paraHeaderList):
                search_res = pattern.search(paragraph)
                if search_res:
                    location['Header'].append(str(i))
                    court.append(search_res.group())
                    span.append(search_res.span())
                    break
            Info_dict_court = self.Infodict_update('审理法院', 'court', court, location, span)
            # print(Info_dict_court)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_court


    def caseType(self):
        pattern = [r'民事',
                   r'刑事',
                   ]

        location = {'Header': []}
        span = []
        caseType = []
        try:
            for i, paragraph in enumerate(self.paraHeaderList):
                for pattern_ele in pattern:
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['Header'].append(str(i))
                        caseType.append(search_res.group() + '案件')
                        span.append(search_res.span())
                        break
            Info_dict_caseType = self.Infodict_update('案件类型', 'caseType', caseType, location, span)
            # print(Info_dict_caseType)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_caseType


    def reason(self):
        pattern = [r'(金融)?.{0,6}(?:借|贷)(款)?.{0,6}(合同)?(\$)?.{0,4}(纠(\$)?纷)?',
                   r'(民间)?.{0,6}借(\$)?(?:贷|货)(\$)?.{0,4}(?:纠纷|关系)?',
                   r'(?:追偿|返还)?(?:垫付|代垫)款.{0,4}纠纷',  #### 民间借贷
                   r'(?:合伙协议|抵押合同|法律服务合\$同)纠纷',
                   r'执行异议之诉(纠纷)?'
                   ]
        location = {'clause': []}
        span = []
        reason = []
        try:
            for i, paragraph in enumerate(self.clauseList[:8]):
                for j, pattern_ele in enumerate(pattern):
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['clause'].append(str(i))
                        reason.append('金融借款合同纠纷' if j == 0 else '民间借贷纠纷')
                        span.append(search_res.span())
                        break
            Info_dict_reason = self.Infodict_update('案由', 'reason', reason, location, span)
            if not Info_dict_reason['value']:
                location = {'Header': []}
                for i, paragraph in enumerate(self.paraHeaderList):
                    for j, pattern_ele in enumerate(pattern):
                        pattern_co = re.compile(pattern_ele)
                        search_res = pattern_co.search(paragraph)
                        if search_res:
                            location['Header'].append(str(i))
                            reason.append('金融借款合同纠纷' if j == 0 else '民间借贷纠纷')
                            span.append(search_res.span())
                            break
                Info_dict_reason = self.Infodict_update('案由', 'reason', reason, location, span)
            # print(Info_dict_reason)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_reason


    def trialRound(self):
        pattern = [r'(?:初|金|重)(（.*）|\[.*\]|【.*】)?字?',
                   r'(?:终|再|提)(（.*）|\[.*\]|【.*】)?字?',
                   ]
        location = {'Header': []}
        span = []
        trialRound = []
        try:
            for i, paragraph in enumerate(self.paraHeaderList):
                for j, pattern_ele in enumerate(pattern):
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['Header'].append(str(i))
                        trialRound.append('一审' if j == 0 else '二审')
                        span.append(search_res.span())
                        break
            Info_dict_trialRound = self.Infodict_update('审理程序', 'trialRound', trialRound, location, span)
            # print(Info_dict_trialRound)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_trialRound


    def trialDate(self):
        pattern = [r'^.{1,5}年.{1,3}月.{1,3}日']
        # TODO
        # Ch_num = ['〇', 'О', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '']
        location = {'Tail': []}
        span = []
        trialDate = []
        try:
            for i, paragraph in enumerate(self.paraTailList):
                for pattern_ele in pattern:
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['Tail'].append(str(i))
                        trialDate.append(search_res.group())
                        span.append(search_res.span())
                        break
            Info_dict_trialDate = self.Infodict_update('裁判日期', 'trialDate', trialDate, location, span)
            # print(Info_dict_trialDate)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_trialDate


    def appellor(self):
        pattern = [r'^(?:原审|再审)?原告(（.*）)?(.*)',
                   r'^(?:原审|再审)?上诉人(（.*）)?(.*)',
                   r'^申请再审人(（.*）)?(.*)',
                   r'^再审申请人(（.*）)?(.*)',
                   r'^(?:原审|再审)?申诉人(（.*）)?(.*)',
                   r'^(原某|原代|原先)(（.*）)?(.*)',
                   r'^(?:第一|第二|第三|第四|第五|再审|原审|共同)?被(?:告|上诉人|申请人|申诉人)(（.*）)?(.*)',
                   ]
        location = {'Header': []}
        span = []
        all_appellor = []
        try:
            for i, paragraph in enumerate(self.paraHeaderList):
                for pattern_ele in pattern:
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['Header'].append(str(i))
                        appellor = search_res.group(2)
                        if appellor:
                            filter_1 = re.compile(r'，|。|；|（|）')
                            appellor_name = filter_1.split(appellor)[0]
                            filter_2 = re.compile(r'：|$|#')
                            appellor_name = filter_2.sub('', appellor_name)
                            # all_appellor.append(appellor_name)
                            loca_pattern = re.compile(appellor_name)
                            fina_res = loca_pattern.search(paragraph)
                            if fina_res:
                                # print(res.group(), res.span())
                                all_appellor.append(appellor_name)
                                span.append(fina_res.span())
                        break

            Info_dict_appellor = self.Infodict_update('当事人', 'appellor', all_appellor, location, span)
            # print(Info_dict_appellor)
        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_appellor


    def docType(self):
        pattern = [r'判决书',
                   r'裁定书',
                   r'决定书',
                   r'调解书']
        location = {'Header': []}
        span = []
        docType  = []
        try:
            for i, paragraph in enumerate(self.paraHeaderList):
                for pattern_ele in pattern:
                    pattern_co = re.compile(pattern_ele)
                    search_res = pattern_co.search(paragraph)
                    if search_res:
                        location['Header'].append(str(i))
                        docType.append(search_res.group())
                        span.append(search_res.span())
                        break
            Info_dict_docType = self.Infodict_update('文书类型', 'docType', docType, location, span)

        except:
            print(traceback.print_exc())
        finally:
            return Info_dict_docType


    def processType(self):
        pattern = r'简易程序'
        pattern = re.compile(pattern)
        location = {'clause': []}
        span = []
        processType  = []
        try:
            for i, paragraph in enumerate(self.clauseList):
                pattern_co = re.compile(pattern)
                search_res = pattern_co.search(paragraph)
                if search_res:
                    location['clause'].append(str(i))
                    processType.append(search_res.group())
                    span.append(search_res.span())
            Info_dict_processType = self.Infodict_update('程序类型', 'processType', processType, location, span)
            if not processType:
                processType.append('普通程序')
                Info_dict_processType = self.Infodict_update('程序类型', 'processType', processType, location, span)
            # print(Info_dict_processType)
        except:
            print(traceback.print_exc())

        finally:
            return Info_dict_processType


    def extract_all(self):
        court = self.court()
        caseType = self.caseType()
        reason = self.reason()
        trialRound = self.trialRound()
        trialDate = self.trialDate()
        appellor = self.appellor()
        docType = self.docType()
        processType = self.processType()
        return [court, caseType, reason, trialRound, trialDate, appellor, docType, processType]


def ext_relainfo(table, docId):
    for doc in table.find({'docId': docId}, no_cursor_timeout=True):
        if doc['schema_version'] != "2.0":
            RID = RelaInfo_FromDocCont(doc['paraHeaderList'], doc['paraTailList'], doc['clauseList'])
            relaInfo_docCont = RID.extract_all()
            # # pprint(relaInfo_docCont)
            table.update_one({"docId": docId}, {"$set": {'relaInfo_docCont': relaInfo_docCont}})


if __name__ == '__main__':
    new_doc = rec_new_doc()
    ext_relainfo(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9")
