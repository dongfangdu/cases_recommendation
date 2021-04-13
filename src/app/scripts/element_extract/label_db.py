# -*- encoding: utf8 -*-

'''
__author__ = Jocky Hawk
__copyright__ = Copyright 2020
__version__ = 0.1
__status = Dev
'''

# from pymongo import Mongo
from pymongo import MongoClient
from bson.json_util import dumps
from pymongo.cursor import CursorType

from itertools import zip_longest
from collections import defaultdict, Counter

import pickle
import html

import bson
import re
import codecs
from pprint import pprint
from app.libs.es import rec_model_doc, rec_new_doc


hanzi_punt_not_stops = '＂＃＄％＆＇（）＊＋，：；－／＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏'
hanzi_punt_stops = '！？｡。'
hanzi_clause_punt_stops = '，；'


def unmerge_rules(line):
    if not line:
        return True

    punt_stops = '！？｡。；：'
    if line[-1] in punt_stops:
        return False

    clerk_p = [
        r'书记员.{0,6}?$',
        r'记录.{0,6}?$',
        r'书记书.{0,6}?$',  # 错字例外
    ]
    for p in clerk_p:
        if re.search(p, line[-10:]):
            return False

    return True


def merge_lines(line_list, seg='', unmerge_filter=None):
    if not callable(unmerge_filter):
        return ''.join(line_list)

    res_line_list = []
    _merged = None
    for _line in line_list:
        if _merged is None:
            _merged = _line
        else:
            _merged = _merged + seg + _line

        if not unmerge_filter(_merged):
            res_line_list.append(_merged)
            _merged = None
    if _merged:
        res_line_list.append(_merged)
    return res_line_list


def clean_unvalid(raw_str, words=[], placeholder='', del_blank=True, del_doc_html=True):
    res_str = raw_str
    if del_doc_html:
        # m = re.finditer(r'\n', res_str, flags=re.S)
        for m in re.finditer(r'[^\\n]*?[法院|书|号]', res_str, flags=re.S):
            res_pre = res_str[:m.start()]
            res_pre = re.sub(r'<([a-z0-9]+?)[>|\b].*/\1>', '', res_pre, flags=re.S)
            res_str = res_pre + res_str[m.start():]
            break
        # res_str = re.sub(r'<([a-z0-9]+?)[>|\b].*/\1>','', res_str, flags=re.S)
        res_str = re.sub(r'<\\?/[a-z0-9]*?>', '', res_str, flags=re.S)
        res_str = re.sub(r'<!--.*?-->', '', res_str, flags=re.S)
        res_str = re.sub(r'<[a-z0-9].*?>', '', res_str, flags=re.S)
    # 清楚空格
    if del_blank:
        res_str = re.sub(r'\s+', '', res_str)

    if words:
        pattern = r'({})'.format(')|('.join(words))
        p = re.compile(pattern)

        res_str = re.sub(pattern, placeholder, res_str)

    return res_str


def clean_substitude(raw_str, num_comma=True, html_escape=True):
    res_str = raw_str

    # 阿拉伯数字表示中~中文，~的处理（改成~英文,~，以免后续clause切分的时候切错）
    if num_comma:
        # 参考
        # line = re.sub(r"(?<!')'t'(?=.)", r"THIS_IS_TRUE", line)
        pattern = r'(\d)，(?=(\d{3}))'
        res_str = re.sub(pattern, r'\1,', res_str)

    # 替换HTML escape字符
    if html_escape:
        loop_counter = 0
        loop_limit = 4
        while True:
            if loop_counter > loop_limit:
                break
            loop_counter += 1

            if res_str == html.unescape(res_str):
                break

            res_str = html.unescape(res_str)

    return res_str


def detect_case_summary_lineno(line_list, start=0, stop=None, step=1, merge_limit=1):
    pattern_list = [
        r'[^。\$]*?原[告某、][^。]*?被告[^。]*?[一二三四五六七八九十]\$?案',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?[一二三四五六七八九十]\$?案',
        r'[^。\$]*?申请再审人[^。]*?被申请人[^。]*?[一二三四五六七八九十]\$?案',
        r'[^。\$]*?再审申请人[^。]*?被申请人[^。]*?[一二三四五六七八九十]\$?案',

        r'原[告某、][^。]*?被告[^。]*?[一二三四五六七八九十]\$?案',

        r'[^。\$]*?原[告某、][^。]*?。[^。]*?被告[^。]*?[一二三四五六七八九十]\$?案',
        r'[^。\$]*?[上申]诉人?[^。]*?。[^。]*?被[上申]诉人?[^。]*?[一二三四五六七八九十]\$?案',

        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?[受审]理',
        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?[上起申]诉',
        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?再审',
        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?法律效力',
        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?诉讼',
        r'[^。\$]*?原[告某][^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?[受审]理',
        r'[^。\$]*?原[告某][^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?[上起申]诉',
        r'[^。\$]*?原[告某][^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?再审',
        r'[^。\$]*?原[告某][^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?法律效力',
        r'[^。\$]*?原[告某][^。]*?[一二三四五六七八九十]\$?案[^。]*?[本法]院[^。]*?诉讼',

        r'[^。\$]*?原[告某][^。]*?被告[^。]*?案[^。]*?[本法]院[^。]*?[受审]理',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?案[^。]*?[本法]院[^。]*?[上起申]诉',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?案[^。]*?[本法]院[^。]*?再审',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?案[^。]*?[本法]院[^。]*?法律效力',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?案[^。]*?[本法]院[^。]*?诉讼',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?案[^。]*?[本法]院[^。]*?[受审]理',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?案[^。]*?[本法]院[^。]*?[上起申]诉',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?案[^。]*?[本法]院[^。]*?再审',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?案[^。]*?[本法]院[^。]*?法律效力',
        r'[^。\$]*?[上申]诉人?[^。]*?被[上申]诉人?[^。]*?案[^。]*?[本法]院[^。]*?诉讼',

        r'[^。\$]*?原[告某][^。*?[一二三四五六七八九十]\$?案[^。]*?不服[^。]*?判决[^。]*?[本法]院[^。]*?[上起申]诉',  # 有点弱
        r'[^。\$]*?[上申]诉人[^。]*?[一二三四五六七八九十]\$?案[^。]*?不服[^。]*?判决[^。]*?[本法]院[^。]*?[上起申]诉',  # 有点弱
        r'[^。\$]*?原[告某][^。]*?案[^。]*?不服[^。]*?判决[^。]*?[本法]院[^。]*?[上起申]诉',  # 有点弱
        r'[^。\$]*?[上申]诉人[^。]*?案[^。]*?不服[^。]*?判决[^。]*?[本法]院[^。]*?[上起申]诉',  # 有点弱
        r'[^。\$]*?[一二三四五六七八九十]\$?案[^。]*?不服[^。]*?判决[^。]*?[本法]院[^。]*?[上起申]诉',  # 有点弱
        r'[^。\$]*?[一二三四五六七八九十]\$?案[^。]*?[本法]\$?院[^。]*?受\$?理[^。]*?审\$?理',
        r'[^。\$]*?[一二三四五六七八九十]\$?案[^。]*?[本法]\$?院[^。]*?提起诉讼[^。]*?立案受理',
        r'[^。\$]*?[一二三四五六七八九十]\$?案[^。]*?[本法]\$?院[^。]*?诉讼[^。]*?立案[^。]*?审案',

        r'[^。\$]*?原[告某][^。]*?被告[^。]*?[本法]院[^。]*?诉讼[^。]*?[受审]理',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?[本法]院[^。]*?受理[^。]*?审理[^。]*?诉讼',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?[本法]院[^。]*?提起[^。]*?诉讼',
        r'[^。\$]*?原[告某][^。]*?被告[^。]*?向本院起诉',
        r'[^。\$]*?登记立案[^。]*?开庭[^。]*?审理',
        r'[^。\$]*?原告[^。]*?本院[^。]*?开庭[^。]*?审理',
        # 上诉人李樱、李涛因民间借贷纠纷案，不服重庆市南川区人民法院（2013）南川法民初字第03058号民事判决，向本院提起上诉。
        # r'[^。\$]*?原[告某、][^。]*?被告[^。]*?案[^。]*?[受审]理',
        # r'[^。\$]*?原[告某][^。]*?案[^。]*?[上起]诉',
        # r'[^。\$]*?原[告某][^。]*?案[^。]*?[受审]理',
        # r'[^。\$]*?[上申]诉人[^。]*?被[上申]诉[^。]*?案[^。]*?[受审]理',
        # r'[^。\$]*?[上申]诉人[^。]*?案[^。]*?[受审]理',
        # r'[^。\$]*?[上申]诉人[^。]*?案[^。]*?[上起]诉',
        # r'[^。\$]*?[一二三四五六七八九十]案[^。]*?[受审]理',
        # r'[^。\$]*?[一二三四五六七八九十]案[^。]*?[上起申]诉',
        # r'[^。\$]*?[一二三四五六七八九十]案[^。]*?审判',
        # r'[^。\$]*?[一二三四五六七八九十]案[^。]*?作出[^。]*?判决',
        # r'[^。\$]*?原[告某、][^。]*?被告[^。]*?[受审]理',
        # r'[^。\$]*?原[告某、][^。]*?被告[^。]*?[上起]诉',
        # r'[^。\$]*?原[告某、][^。]*?被告[^。]*?[本法]院[^。]*?诉讼',
        # r'[^。\$]*?原[告某、][^。]*?被告[^。]*?参加[^。]*?诉讼',
        # r'[^。\$]*?原[告某、][^。]*?[本法]院[^。]*?[受审]理',
        # r'[^。\$]*?原[告某、][^。]*?[本法]院[^。]*?[上起]诉',
        # r'[^。\$]*?原[告某、][^。]*?[本法]院[^。]*?诉讼',
        # r'[^。\$]*?[上申]诉人[^。]*?被[上申]诉[^。]*?[受审]理',
        # r'[^。\$]*?[上申]诉人[^。]*?被[上申]诉[^。]*?[上起]诉',
        # r'[^。\$]*?[上申]诉人[^。]*?[本法]院[^。]*?[受审]理',
        # r'[^。\$]*?[上申]诉人[^。]*?[本法]院[^。]*?[上起]诉',

        # r'[^。]*?[一二三四五六七八九十]案[^。]*?[本法]院[^。]*?。[^。]*?[上起申]诉',
        # r'[^。]*?[一二三四五六七八九十]案[^。]*?[本法]院[^。]*?。[^。]*?再审',
        # r'[^。]*?[一二三四五六七八九十]案[^。]*?[本法]院[^。]*?[^。]*?诉讼',
        # r'原[告|某|、][^。]*?被告[^。]*?[一二三四五六七八九十]案',
        # r'[上申]诉人[^。]*?被[上申]诉[^。]*?[一二三四五六七八九十]案',

        # r'立案[^。]*?公开开庭[^。]*?审理'

    ]

    check_list = line_list[slice(start, stop, step)]
    res_idx = None
    res_line = None

    matching_list = check_list
    cur_pattern = None
    for _merge_counter in range(merge_limit):
        if _merge_counter > 0:
            matching_list = [f'{_i}{_j}' for _i, _j in zip(matching_list[:-1], check_list[_merge_counter:])]

        for idx, line in enumerate(matching_list):
            break_flag = False
            for p in pattern_list:
                if re.search(p, line):
                    res_idx, res_line = idx, line
                    break_flag = True
                    cur_pattern = p
            if break_flag:
                # print(res_idx, cur_pattern)
                break
        if (res_idx is not None) and (res_line is not None):
            return res_idx + start, res_line

    return res_idx, res_line


def detect_clerk_lineno(line_list, start=0, stop=None, step=1, merge_limit=1):
    # p = r'^.{0,4}书记员.{0,13}$'

    # 书记员章苏红 797ea4e5-e031-4c65-a361-bec71ba51983
    # 代书记员吴庆燕 5b73102a-7440-462a-85f0-97cb8b8c3c27
    pattern_list = [
        r'[^。\$]*?.{4}年.{0,2}月.{0,3}日?(\$[^。\$]*?){0,4}书记员',
        r'[^。\$]*?.{4}年.{0,2}月日.{0,3}日?(\$[^。\$]*?){0,4}书记员',  # 错字问题
        r'[^。\$]*?.{4}年?.{1,2}月.{1,3}日(\$[^。\$]*?){0,4}书记员',  # 错字问题
        r'[^。\$]*?.{4}年.{0,2}月.{0,3}日?(\$[^。\$]*?){0,4}书记书',
        r'[^。\$]*?.{4}年.{0,2}月.{0,3}日?(\$[^。\$]*?){0,4}记录',
        # r'[^。\$]*?审判[员长].{1,5}[^。\$]*?.{0,4}书记员',
        r'[^。\$]*?审判[员长].{1,5}[^。\$]*?.{0,4}书记员',
        r'[^。\$]*?审判[员长].{1,5}[^。]*?.{0,4}书记员',
        # r'[^。\$]*?审判[员长].{1,5}[^。]*?.{0,4}书记员',
        # r'^.{4}年.{1,2}月.{1,3}日?.{0,4}书记员.{0,13}$',
        # r'^.{0,4}书记.{0,13}$',    # 处理错字的
        # r'^.{4}年.{1,2}月.{1,3}日?.{0,4}书记.{0,13}$',    # 处理错字的
        # r'^[^，。]+.{4}年.{1,2}月.{1,3}日?.{0,4}书记员.{0,13}$',
        # r'^[^，。]+.{4}年.{0,2}月.{0,3}日.{0,4}书记员.{0,13}$', # 处理特殊情况   如 审判长曹志宇审判员李建新代理审判员姜文二○一四年月日书记员张智
        # r'^.{0,4}书记员.{0,13}[法附].{0,5}$',# 书记员赵晓丹本案判决所依据的相关法律
        # r'^记录.{1,5}$',    # 处理特殊情况
    ]

    check_list = line_list[slice(start, stop, step)]
    res_idx = None
    res_line = None

    matching_list = check_list
    cur_pattern = None
    for _merge_counter in range(merge_limit):
        if _merge_counter > 0:
            # TODO step = -1 的时候，
            matching_list = [f'{_i}{_j}' for _i, _j in zip(matching_list[:-1], check_list[_merge_counter:])]

        for idx, line in enumerate(matching_list):
            break_flag = False
            for p in pattern_list:
                if re.search(p, line):
                    res_idx, res_line = idx, line
                    break_flag = True
                    cur_pattern = p
            if break_flag:
                break
        if (res_idx is not None) and (res_line is not None):
            return res_idx + start, res_line

    return None, None


# test_clean = "&amp;#xA;审判长吴国斌&amp;#xA;人民陪审员陈建平&amp;#xA;人民陪审员李宝弟&amp;#xA;二〇   一三年四月五日&amp;#xA;代理书记员吕美萍&amp;#xA;附法律条文：&amp;#xA;《中华人民共和国合同法》：&amp;#xA;第二百零五条借款人应当按照约定的期限支付利息。"

# print(clean_unvalid(test_clean, words=['&amp;', '#xA;'], placeholder='\n'))

# tetst_clean = '告自贡唐人商贸有限公司自本判决生效之日起十日内向原告自贡市商业银行股份有限公司归还借款本金33，000，000.00元，并支付从2013年9月25日起按照双'
# print(clean_substitude(tetst_clean))
# test_clean = clean_substitude(tetst_clean)

# test_clean = '借款月利率为11.7875&amp;amp;permil;，'

# pattern = r'&amp.+;'

# test_clean = re.sub(pattern, '', test_clean)

# print(test_clean)


# from LAC import LAC
# lac = LAC(mode='lac')
# lac_result = lac.run(test_clean)
# lac_result2 = [f'{char}/{pos}' for char, pos in zip(*lac_result)]

# print(lac_result2)


def paragraph_segment(full_doc):
    full_doc = clean_unvalid(full_doc, words=['&amp;#xA;', '<br/>', r'{C}', ], placeholder=r'\\n')
    full_doc = full_doc.replace('（本页无正文）', '\n')
    full_doc = full_doc.replace('（此页无正文）', '\n')
    full_doc = full_doc.replace('（该页无正文）', '\n')
    full_doc = clean_unvalid(full_doc, words=['\?', ], placeholder='')
    full_doc = clean_substitude(full_doc)
    full_doc = clean_unvalid(full_doc)
    # para = [line for line in full_doc.split('\n') ]
    para = [line for line in full_doc.split(r'\n')]
    para = [line for line in para if line]

    return para


def sentence_segment(full_paragraph):
    split_pattern = r'({})'.format(')|('.join(list(hanzi_punt_stops)))
    sent = [line for line in re.split(split_pattern, full_paragraph)]
    sent = [line for line in sent if line]
    sent = [txt + punt if punt else txt for txt, punt in zip_longest(sent[0:][::2], sent[1:][::2])]

    res_sent = []
    for s in sent:
        if s == '#':
            res_sent[-1] = res_sent[-1] + '#'
        else:
            res_sent.append(s)

    return res_sent


def clause_segment(full_sent):
    split_pattern = '(' + ')|('.join(list(hanzi_clause_punt_stops)) + ')'
    clause = [line for line in re.split(split_pattern, full_sent)]
    clause = [line for line in clause if line]
    clause = [txt + punt if punt else txt for txt, punt in zip_longest(clause[0:][::2], clause[1:][::2])]

    return clause


def paragraph_sents_map(para_list):
    s_p_mapping = {}  # 段落和句子的索引字段
    s_list_for_doc = []

    send_idx = 0
    for p_idx, p in enumerate(para_list):
        sent_list = sentence_segment(p)
        s_idx, s_list = zip(*enumerate(sent_list))
        s_idx = [idx + send_idx for idx in s_idx]
        for s_i in s_idx:
            s_p_mapping[str(s_i)] = str(p_idx)
        s_list_for_doc.extend(s_list)
        send_idx += len(sent_list)
    return s_list_for_doc, s_p_mapping


def sentence_clause_map(sent_list):
    c_s_mapping = {}
    c_list_for_doc = []

    clause_idx = 0
    for s_idx, s in enumerate(sent_list):
        clause_list = clause_segment(s)
        c_idx, c_list = zip(*enumerate(clause_list))
        c_idx = [idx + clause_idx for idx in c_idx]
        for c_i in c_idx:
            c_s_mapping[str(c_i)] = str(s_idx)
        c_list_for_doc.extend(clause_list)
        clause_idx += len(clause_list)

    return c_list_for_doc, c_s_mapping


def para_unmerge_rules(line):
    if not line:
        return True
    punt_stops = '！？｡。；：'
    if line[-1] in punt_stops:
        return False
    return True


def data_clean(table, docId):
    cur = table.find({'docId': docId})
    w_file = codecs.open('./maybe.txt', 'w', encoding='utf8')
    for result in cur:
        doc_id = result['docId']
        src_para_list = paragraph_segment(result['docContent'])
        src_para_list = merge_lines(src_para_list, seg='$', unmerge_filter=unmerge_rules)
        src_para_list = [line + '#' for line in src_para_list]

        # pprint([line[:80] for line in src_para_list])

        # print(src_para_list[14])

        ##
        case_summary_lineno, _line = detect_case_summary_lineno(src_para_list, start=1, merge_limit=2)
        if case_summary_lineno is None:
            case_summary_lineno, _line = detect_case_summary_lineno(src_para_list, start=0, stop=5, merge_limit=2)
        if case_summary_lineno is None:
            w_file.writelines(f'{doc_id},-,-\n')
            continue
        else:
            w_file.writelines(f'{doc_id},{case_summary_lineno},{_line}\n')
            pass

        para_header_list = src_para_list[:case_summary_lineno]  # 包含法院、案号，被告、原告、
        para_left_list = src_para_list[case_summary_lineno:]

        #### 案件详情行
        case_summary_sent_list = sentence_segment(_line)

        case_summary_sent_lineno, _line = detect_case_summary_lineno(case_summary_sent_list, merge_limit=2)
        if case_summary_sent_lineno is None:
            w_file.writelines(f'{doc_id},-,-\n')
            continue
        else:
            w_file.writelines(f'{doc_id},{case_summary_sent_lineno},{_line}\n')
            pass
        para_header_list.extend(case_summary_sent_list[:case_summary_sent_lineno])

        if '$' in _line:
            case_summary_piece_list = _line.split('$')
            case_summary_piece_lineno, _line = detect_case_summary_lineno(case_summary_piece_list,
                                                                          merge_limit=len(case_summary_piece_list))
            para_header_left_list = case_summary_piece_list[:case_summary_piece_lineno]
            case_summary_sent = '$'.join(case_summary_piece_list[case_summary_piece_lineno:])

            para_header_list.extend(para_header_left_list)
            para_left_list[0] = case_summary_sent

        ## 定位 clerk

        paraTailList = None
        paraAppendixList = None
        clerk_para_lineno, _line = detect_clerk_lineno(para_left_list)
        if clerk_para_lineno is None:
            w_file.writelines(f'{doc_id},-,-\n')
            continue
        else:
            w_file.writelines(f'{doc_id},{clerk_para_lineno},{_line}\n')

            paraTailList = para_left_list[clerk_para_lineno].split('$')

            if len(para_left_list) >= (clerk_para_lineno + 1):
                slice_start = clerk_para_lineno + 1
                paraAppendixList = para_left_list[slice_start:]

            para_left_list = para_left_list[:clerk_para_lineno]
        # if paraAppendixList:
        #     print(doc_id, len(paraAppendixList), paraAppendixList[0])
        # para_left_list = merge_lines(para_left_list, unmerge_filter=unmerge_rules)

        # pprint([line[:80] for line in para_left_list])
        src_sent_list, src_s_p_index = paragraph_sents_map(para_left_list)
        # pprint([line[:80] for line in src_sent_list])

        src_clause_list, src_c_s_index = sentence_clause_map(src_sent_list)
        # pprint([line[:80] for line in src_clause_list])
        # pprint([(_idx, line[:80]) for _idx,  line in zip(src_c_s_index.values(),src_clause_list)])

        para_header_list = ''.join(para_header_list).split('#')
        tmp = []
        for p_h in para_header_list:
            tmp.extend(p_h.split('$'))
        para_header_list = [line for line in tmp if line]

        update_dict = {
            "paraHeaderList": para_header_list,
            "sentList": src_sent_list,
            "sentParaIndex": src_s_p_index,
            "clauseList": src_clause_list,
            "clauseSentIndex": src_c_s_index,
            "schema_version": "2.4"
        }
        if paraTailList:
            update_dict['paraTailList'] = paraTailList
        if paraAppendixList:
            update_dict['paraAppendixList'] = paraAppendixList
        # pprint(update_dict)
        query_parameter = {'docId': result['docId']}
        update_parameter = {
            "$set": update_dict,
        }
        # # update_parameter =  {
        # #     "$set":
        # #     {
        # #         "paraList":src_para_list,
        # #     }

        table.update_one(query_parameter, update_parameter)
    w_file.close()


if __name__ == "__main__":
    new_doc = rec_new_doc()
    data_clean(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9")




