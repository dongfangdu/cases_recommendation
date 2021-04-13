from pprint import pprint
import re
from mongoengine import *
from app.libs.es import rec_new_doc


def litigant_parse(name, key, litigant_list, pattern_list) -> list:
    litigant_parse = []
    for litigant_ele in litigant_list:
        punc_pattern = r'，|。|；|（|）'
        pattern = re.compile(punc_pattern)
        litigant_text = pattern.split(litigant_ele['text'])
        litigant_list = [keyword_sub(x, pattern_list) for x in litigant_text if x]
        litigant_d = litigant_dict(name, key, litigant_list)
        litigant_parse.append(litigant_d)

    return litigant_parse


def litigant_dict(name, key, litigant_list):
    litigant = {'name': name, 'key': key}
    punc_pattern = r'：|$|#'
    pattern = re.compile(punc_pattern)
    litigant['role'] = pattern.sub('', litigant_list[0])
    litigant['attribute'] = litigant_list[1:]
    return litigant


def keyword_sub(str, pattern_list):
    for pattern_ele in pattern_list:
        pattern = re.compile(pattern_ele)
        res = pattern.sub('', str)
        if res != str:
            break
    return res


def gen_lit_det(table, docId):
    plaintiff_pattern = [r'^(?:原审|再审)?原告',
                         r'^(?:原审|再审)?上诉人',
                         r'^申请再审人',
                         r'^再审申请人',
                         r'^(?:原审|再审)?申诉人',
                         r'^(原某|原代|原先)'
                         ]
    defendant_pattern = [r'^(?:第一|第二|第三|第四|第五|再审|原审|共同)?被(?:告|上诉人|申请人|申诉人)',
                         ]
    agent_pattern = [r'^委托代理人',
                     r'^共同委托代理人'
                     ]
    ################# single element test
    for doc in table.find({'docId': docId}, no_cursor_timeout=True):
        roleInfo = []
        if doc['schema_version'] != "2.0":
            plaintiff = doc['elemParaIndex']['plaintiff']
            defendant = doc['elemParaIndex']['defendant']
            agent = doc['elemParaIndex']['agent']
            name_plaintiff = '原告/上诉人'
            name_defendant = '被告/被上诉人'
            name_agent = '委托代理人'

            plaintiff_info = litigant_parse(name_plaintiff, 'plaintiff', plaintiff, plaintiff_pattern)
            defendant_info = litigant_parse(name_defendant, 'defendant', defendant, defendant_pattern)
            agent_info = litigant_parse(name_agent, 'agent', agent, agent_pattern)

            roleInfo.extend(plaintiff_info)
            roleInfo.extend(defendant_info)
            roleInfo.extend(agent_info)
            # print(roleInfo)
            table.update_one({"docId": docId}, {"$set": {'roleInfo': roleInfo}})


if __name__ == '__main__':
    new_doc = rec_new_doc()
    gen_lit_det(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9")
