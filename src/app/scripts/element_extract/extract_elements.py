import json
import re
import pprint
from app.model.base_db import NewDoc
from pprint import pprint
import traceback


def elefrom_para(pattern_dict):
    for docInfo in NewDoc.objects.all():
        doc = NewDoc.objects(docId=docInfo.docId).first()
        paraClauseIndex = doc.paraClauseIndex
        clauseList = doc.clauseList
        docParaIndex = {}
        elemParaIndex = {}
        try:
            for ele, pattern in pattern_dict.items():
                eleParaIndex_dict = {}
                for index, paraList in enumerate(paraClauseIndex):
                    paragraph = "".join([clauseList[i] for i in paraList]).replace('#', '').replace('$', '')
                    eleResult = re.search(pattern, paragraph)
                    docParaIndex[index] = paragraph
                    if eleResult:
                        eleParaIndex_dict[index] = paragraph
                eleParaIndex_dict = json.dumps(eleParaIndex_dict, ensure_ascii=False)
                elemParaIndex[ele] = eleParaIndex_dict

            # ModelDoc.objects(docId=docInfo.docId).update(elemParaIndex=elemParaIndex)
            # print(docParaIndex)
            pprint(elemParaIndex)

        except:
            print(traceback.print_exc())
            print(docInfo.docId)


def eledict_update(ele_dict: dict, para_num, clause_num, paragraph):
    ele_dict['para_num'] = para_num
    ele_dict['clause_num'] = clause_num
    ele_dict['text'] = paragraph
    return ele_dict


def match_para_patt(element, pattern_list, paragraph, para_num='Header', clause_num=[]) -> list:
    for pattern_ele in pattern_list:
        ele_dict = {}
        pattern = re.compile(pattern_ele)
        eleResult = pattern.search(paragraph)
        # eleResult = re.search(pattern_ele, paragraph)
        if not eleResult:
            continue
        # print(pattern_ele)
        ele_dict = eledict_update(ele_dict, para_num, clause_num, paragraph)
        element.append(ele_dict)
        break
    return element


def element_in_header(pattern_list, paraHeaderList) -> list:
    header_element = []
    try:
        for paragraph in paraHeaderList:
            element = []
            mid_res = match_para_patt(element, pattern_list, paragraph)
            if mid_res:
                header_element.extend(mid_res)
    except:
        print(traceback.print_exc())
    finally:
        return header_element


def sent_to_para(paraList, clauseList):
    paragraph = ''.join([clauseList[int(i)] for i in paraList]).replace('#', '').replace('$', '')
    return paragraph


def element_in_sent(start, end, pattern_list, paraClauseIndex, clauseList) -> list:
    text_element = []
    try:
        for index in range(start, end):
            element = []
            paraList = paraClauseIndex[index]
            paragraph = sent_to_para(paraList, clauseList)
            mid_res = match_para_patt(element, pattern_list, paragraph, para_num=index, clause_num=paraList)
            if mid_res:
                text_element.extend(mid_res)
    except:
        print(traceback.print_exc())
    finally:
        return text_element


def extract_plaintiff(paraHeaderList):
    pattern_list = [r'^(?:原审|再审)?原告',
                    r'^(?:原审|再审)?上诉人',
                    r'^申请再审人',
                    r'^再审申请人',
                    r'^(?:原审|再审)?申诉人',
                    r'^(原某|原代|原先)'
                    ]
    plaintiff = element_in_header(pattern_list, paraHeaderList)
    return plaintiff


def extract_defendant(paraHeaderList):
    pattern_list = [r'^(?:第一|第二|第三|第四|第五|再审|原审|共同)?被(?:告|上诉人|申请人|申诉人)',
                    ]
    defendant = element_in_header(pattern_list, paraHeaderList)
    return defendant


def extract_agent(paraHeaderList):
    pattern_list = [r'^委托代理人',
                    r'^共同委托代理人'
                    ]
    agent = element_in_header(pattern_list, paraHeaderList)
    return agent


def extract_plaintiffClaim(paraClauseIndex, clauseList):
    pattern_list = [r'^(?:原告|上诉人).{0,40}诉称']
    para_start = 0
    para_end = len(paraClauseIndex) - 5
    plaintiff_claim = element_in_sent(para_start, para_end, pattern_list, paraClauseIndex, clauseList)
    return plaintiff_claim


def extract_defendantArgue(paraClauseIndex, clauseList):
    pattern_list = [r'^被(?:告|上诉人).{0,40}辩称',
                   r'^被(?:告|上诉人).{0,40}(?:未|没有)(?:应诉|答辩|出庭|辩称|提供证据|提出)']
    para_start = 0
    para_end = len(paraClauseIndex) - 5
    defendant_argue = element_in_sent(para_start, para_end, pattern_list, paraClauseIndex, clauseList)
    return defendant_argue


def match_paras_index(start, end, pattern_list, paraClauseIndex, clauseList):
    index_list = []
    for index in range(start, end):
        paraList = paraClauseIndex[index]
        paragraph = sent_to_para(paraList, clauseList)
        for pattern_ele in pattern_list:
            pattern = re.compile(pattern_ele)
            eleResult = pattern.search(paragraph)
            if eleResult:
                # print(pattern_ele)
                # print(paragraph)
                index_list.append(index)
                break
    return index_list


def courtFact_filter(start, end, judge_pattern,
                     filter_pattern, paraClauseIndex, clauseList):
    court_fact = []
    match_judgeparas = match_paras_index(start, end, judge_pattern, paraClauseIndex, clauseList)
    match_deemparas = match_paras_index(start, end, filter_pattern, paraClauseIndex, clauseList)
    # print(match_judgeparas, match_deemparas)
    try:
        if min(match_judgeparas) < min(match_deemparas):
            for index in range(min(match_judgeparas), min(match_deemparas)):
                ele_dict = {}
                paraList = paraClauseIndex[index]
                paragraph = sent_to_para(paraList, clauseList)
                ele_dict = eledict_update(ele_dict, index, paraList, paragraph)
                court_fact.append(ele_dict)
        elif min(match_judgeparas) < max(match_deemparas):
            for index in range(min(match_judgeparas), max(match_deemparas)):
                ele_dict = {}
                paraList = paraClauseIndex[index]
                paragraph = sent_to_para(paraList, clauseList)
                ele_dict = eledict_update(ele_dict, index, paraList, paragraph)
                court_fact.append(ele_dict)
        else:
            ele_dict = {}
            index = min(match_judgeparas)
            paraList = paraClauseIndex[index]
            paragraph = sent_to_para(paraList, clauseList)
            ele_dict = eledict_update(ele_dict, index, paraList, paragraph)
            court_fact.append(ele_dict)
    except:
        # print(traceback.print_exc())
        pass
    return court_fact


def courtFact_extract(start, end, pattern_v1, pattern_v2,
                      filter_pattern, paraClauseIndex, clauseList, trialRound):
    if trialRound == "二审":
        courtfact_1st = element_in_sent(start, start+5, pattern_v1, paraClauseIndex, clauseList)
        courtfact_2st = courtFact_filter(start, end, pattern_v2, filter_pattern, paraClauseIndex, clauseList)
        court_fact = courtfact_1st + courtfact_2st
    else:
        court_fact = courtFact_filter(start, end, pattern_v2, filter_pattern, paraClauseIndex, clauseList)
    return court_fact


def extract_courtFact(paraClauseIndex, clauseList, trialRound):
    pattern_v1 = [r'(?:原审|一审)(法院)?(?:经|根据|基于|结合)?(?:审理|庭审|审查|质证|判决)(?:认定|认证|确认|查明)',
                 ]

    pattern_v2 = [r'^[^(一审法院)|(原审法院)](?:经|根据|基于|结合)?(?:审理|庭审|二审|再审|查明)(?:查明|认定|质证|认证|审查|确认)',
                  r'^.{0,20}[^(一审)|(原审)](?:法院|本院)(?:经|根据|基于|结合)?.{0,10}(?:审理|庭审|一审|再审|二审).{0,5}(?:查明|认定|质证|认证|审查|确认)',
                  r'^.{0,30}[^(本院认为)|(原审法院认为)|(一审)|(原审)].*?(?:法院|本院)?(?:审理|庭审|审查|质证|再审)?(?:认证|认定|查明|确认).{0,5}(:?事实如下|如下事实|以下事实|下列事实)',
                  r'^.{0,30}[^(本院认为)|(原审法院认为)|(一审)|(原审)].*?法律事实',
                  r'^[^(本院认为)|(原审法院认为)|(一审)|(原审)].*?另查(明)?',
                  r'本院.{0,15}分析和认定',
                  r'^.*?[^(诉称)|(辩称)].*?(?:经|根据|基于|结合|综上).{0,20}(?:查明|认定|质证|认证|审查|确认)事实(?:查明|认定|质证|认证|审查|确认)?',
                  r'^.*?[^(诉称)|(辩称)].*?(?:经|根据|基于|结合|综上).{0,20}(?:查明|认定|质证|认证|审查|确认)?事实(?:查明|认定|质证|认证|审查|确认)',
                  r'现(?:查明|认定|质证|认证|审查|确认)',
                  r'^(?:经|根据|基于|结合|综上)(?:审理|庭审|一审|再审|二审)?(?:查明|认定|质证|认证|审查|确认)',
                  ]

    # sub_pattern = [r'^[一二三四五六七八九十]、',
    #                r'^\d、'
    #                ]

    filter_pattern = [r'(?:本院|本庭)(?:再审|经审理|审理)?(?:认为|以为)',
                      # r'判决如下：'
                    ]
    para_start = 0
    para_end = len(paraClauseIndex)
    try:
        court_fact = courtFact_extract(para_start, para_end, pattern_v1, pattern_v2,
                                       filter_pattern, paraClauseIndex, clauseList, trialRound)
        # pprint(court_fact)
    except :
        # print(traceback.print_exc())
        pass
    finally:
        return court_fact


def extract_courtDeem(paraClauseIndex, clauseList):
    pattern_list = [r'(?:本院|本庭)(?:再审|经审理|审理)?(?:认为|以为)',
                    r'(?:原审|一审)?法院.{0,10}(?:审理|一审|经审理)(?:认为|以为)'
                    ]
    para_start = 0
    para_end = len(paraClauseIndex)
    courtDeem = element_in_sent(para_start, para_end, pattern_list, paraClauseIndex, clauseList)
    return courtDeem


def courtJudgment_extract(start, end, pre_pattern, pattern_list, paraClauseIndex, clauseList):
    courtJudgment = []
    for index in range(start, end):
        pre_paraList = paraClauseIndex[index]
        pre_paragraph = sent_to_para(pre_paraList, clauseList)
        for pattern_ele in pre_pattern:
            # eleResult = extract_ele(pattern_ele, pre_paragraph)
            pattern = re.compile(pattern_ele)
            eleResult = pattern.search(pre_paragraph)
            if not eleResult:
                continue
            judgment_hit = 0
            judgment_num = end - index
            courtJudgment, judgment_hit = courtJudgment_subextract(judgment_num, judgment_hit, index,
                                                            pattern_list, courtJudgment, paraClauseIndex, clauseList)
            if judgment_hit != 0:
                continue
            ele_dict = {}
            judge_paraList = paraClauseIndex[index + 1]
            judge_paragraph = sent_to_para(judge_paraList, clauseList)
            ele_dict = eledict_update(ele_dict, index+1, judge_paraList, judge_paragraph)
            courtJudgment.append(ele_dict)
            break
    return courtJudgment


def courtJudgment_subextract(judgment_num, judgment_hit, index,
                             pattern_list, courtJudgment, paraClauseIndex, clauseList):
    for sub_index in range(1, judgment_num):
        judge_paraList = paraClauseIndex[index + sub_index]
        judge_paragraph = sent_to_para(judge_paraList, clauseList)
        for sub_pattern_ele in pattern_list:
            # sub_eleResult = extract_ele(sub_pattern_ele, judge_paragraph)
            sub_pattern = re.compile(sub_pattern_ele)
            sub_eleResult = sub_pattern.search(judge_paragraph)
            if not sub_eleResult:
                continue
            ele_dict = {}
            ele_dict = eledict_update(ele_dict, index+sub_index, judge_paraList, judge_paragraph)
            courtJudgment.append(ele_dict)
            judgment_hit += 1
            break
    return courtJudgment, judgment_hit


def extract_courtJudgment(paraClauseIndex, clauseList, docId):
    pre_pattern = [r'(判决如下：)']
    pattern_list = [r'^[一二三四五六七八九十]、',
                   r'^\d、',
                   ]
    para_start = 4
    para_end = len(paraClauseIndex)

    try:
        courtJudgment = courtJudgment_extract(para_start, para_end, pre_pattern, pattern_list, paraClauseIndex, clauseList)
    except :
        print(docId)
        print(traceback.print_exc())
    finally:
        return courtJudgment
