# -*- encoding: utf8 -*-

'''
__author__ = Jocky Hawk
__copyright__ = Copyright 2020
__version__ = 0.1
__status = Dev
'''

import glob
import os
import pickle
import re
from copy import deepcopy
from tqdm import tqdm
import time
from multiprocessing import Pool

from collections import defaultdict

from itertools import product, islice
from LAC import LAC

import numpy as np


def gen_inversed_idx(idx_dict):
    inv_idx = defaultdict(list)
    for k, v in idx_dict.items():
        inv_idx[v].append(k)
    return inv_idx


def merge_line_by_inv_idx(line_list, inv_idx):
    res_line_dict = {}
    for line_no, sub_line_list in inv_idx.items():
        sub_lineno_start = min([int(i) for i in sub_line_list])
        sub_lineno_stop = max([int(i) for i in sub_line_list]) + 1

        merge_line = ''.join(line_list[slice(sub_lineno_start, sub_lineno_stop)])
        res_line_dict[line_no] = merge_line

    # res_line_dict = sorted(res_line_dict, key=lambda x: int(x[0]))
    return [s for i, s in sorted(res_line_dict.items(), key=lambda x: int(x[0]))]


def load_corpus_pickle():
    glob_pattern = './corpus_data/*.clean.clause.pickle'

    res_dict = {}

    for f in glob.glob(glob_pattern):

        corpus_list = None
        with open(f, 'rb') as handle:
            corpus_list = pickle.load(handle)

        if not corpus_list:
            continue

        loop_counter = 0
        loop_limit = None

        if not loop_limit:
            loop_limit = len(corpus_list)

        with tqdm(total=loop_limit) as pbar:

            for c in corpus_list:
                if loop_counter > loop_limit:
                    break
                loop_counter += 1
                pbar.update(1)

                doc_id = c['docId']
                clause_list = c['clauseList']
                c_s_idx = c['clauseSentIndex']
                s_p_idx = c['sentParaIndex']

                ############ merge to sentence
                c_s_inv_idx = gen_inversed_idx(c_s_idx)
                sentence_list = merge_line_by_inv_idx(clause_list, c_s_inv_idx)
                sentence_list = [sent.replace('$', '').replace('#', '').replace('＊', '×') for sent in sentence_list]

                ############ merge to paragraph
                # c_p_idx = {c:s_p_idx[s]  for c, s in  c_s_idx.items()}
                # c_p_inv_idx = gen_inversed_idx(c_p_idx)
                # paragraph_list = merge_line_by_inv_idx(clause_list, c_p_inv_idx)

                for _idx, _sent in enumerate(sentence_list):
                    _key = '{}:{}'.format(doc_id, str(_idx).zfill(3))
                    res_dict[_key] = _sent

    return res_dict


def find_position_by_pattern(lac_res, pattern_list):
    if not pattern_list:
        return

    p_list = []
    for p_str in pattern_list:
        p_list.append(re.compile(p_str))

    pos_list = lac_res[1]
    pos_list_with_bound = [_token + '/' + _pos + '$' for _token, _pos in zip(*lac_res)]

    pos_list_str = ''.join(pos_list_with_bound)
    pos_len_list = [len(_pos) for _pos in pos_list_with_bound]
    pos_len_position_list = np.cumsum(pos_len_list)
    pos_len_position_list = np.insert(pos_len_position_list, 0, 0)

    len_positon = [(_p, m.span()) for _p in p_list for m in _p.finditer(pos_list_str)]

    find_position_list = []
    try:
        for _p, (_s, _e) in len_positon:
            _start = np.where(pos_len_position_list == _s)[0][0]
            _end = np.where(pos_len_position_list == _e)[0][0]
            find_position_list.append((_p.pattern, _start, _end))
    except:
        from pprint import pprint
        # pprint(len_positon)
        # print(lac_res)

    return find_position_list


def merge_book_name(lac_res):
    res = deepcopy(lac_res)

    # token_pos_list = [f'{_token}/{_pos}' for _token, _pos in zip(*res)]
    # book_punt_pair = _find_book_punt_position_pair(token_pos_list)  # TODO use pattern like regex
    patter_list = ['(《/w\$)[^《]*?(》/w\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'BOOK'
        if '法' in merge_token:
            merge_pos = 'LAWBOOK'
        elif '合同' in merge_token:
            merge_pos = 'CONTRACT'
        res[1][front: rear] = [merge_pos, ]

    return res


def merge_money(lac_res):
    res = deepcopy(lac_res)

    patter_list = ['((?<=\$)￥/[^\$]+?\$)?([^\$]+?元[^\$]*?/m\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'MONEY'
        res[1][front: rear] = [merge_pos, ]

    patter_list = ['(((?<=\$)￥[0-9,，]+/m?\$)(,/w\$))?(((?<=\$)[0-9,，]+/m?\$)(,/w\$))*?([^\$]+?元[^\$]*?/MONEY\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        merge_token = merge_token.replace('，', ',')
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'MONEY'
        res[1][front: rear] = [merge_pos, ]

    # 处理如下情况
    # '文金连现金壹万贰仟伍佰元正￥', '12500.00元'
    patter_list = ['(([^\$]+?￥/[^\$]+?\$)([^\$]+?元[^\$]*?/MONEY\$))', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token_list = []
        merge_token_list.append((res[0][front][:-1]))
        merge_token_list.append(('￥' + ''.join(res[0][rear - 1])))
        res[0][front: rear] = merge_token_list
        merge_pos_list = []
        merge_pos_list.append(res[1][front])
        merge_pos_list.append('MONEY')
        res[1][front: rear] = merge_pos_list

    patter_list = [
        '([^\$]+?/MONEY\$)(([零一二三四五六七八九十]+?/m\$)([角分]/[^\$]+?\$))*?([零一二三四五六七八九十]+?[角分]/[^\$]+?\$)+?',

    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'MONEY'
        res[1][front: rear] = [merge_pos, ]

    return res


def merge_loc(lac_res):
    res = deepcopy(lac_res)
    patter_list = [
        '([^\$]+?/LOC\$)(?:[^\$]+?/[sf]\$|[^\$]+?/LOC\$)+',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'LOC'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?/LOC\$)(、/w\$)([^\$]+?/LOC\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'LOC'
        res[1][front: rear] = [merge_pos, ]

    return res


def merge_org(lac_res):
    res = deepcopy(lac_res)
    patter_list = [
        '([^\$]+?/LOC\$)([^\$]+?/[^\$]+?\$){0,3}((?:银行|支行|联社|信用社|分社|分理处|公司|分行)/[^\$]+?\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'ORG'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?/ORG\$)+',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'ORG'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?/LOC\$)([^\$]+?/ORG\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'ORG'
        res[1][front: rear] = [merge_pos, ]

    return res


def merge_time(lac_res):
    res = deepcopy(lac_res)
    patter_list = [
        '([^\$]+?/TIME\$)+',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'TIME'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?年/TIME\$)(([0-9]{1,2}/m\$)(./w\$))*?([0-9]{1,2}/m\$)(月[份底初]?/[^\$]+?\$)',
        '([^\$]+?年/TIME\$)(([0-9]{1,2}/m\$)(./w\$))*?([0-9]{1,2}月[份底初]?/TIME\$)',
        '([^\$]+?年/TIME\$)([一二三四五六七八九十]+?/m\$)(月[份底初]?/[^\$]+?\$)',
        '([^\$]+?分/TIME\$)([0-9]{1,2}秒/m\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'TIME'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?[^日]/TIME\$)(日/[^\$]+?\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'TIME'
        res[1][front: rear] = [merge_pos, ]

    # ['2010年11月8', '日向'] ['2010年11月8', '日起']
    # 将“日”字挪到前面，后面词性不清楚，大多十p
    patter_list = ['([^\$]+?[^日]/TIME\$)(\d+/m\$)?(日[向起经]/[^\$]+?\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        # merge_token = ''.join(res[0][front:rear])
        merge_token_list = []
        merge_token_list.append((''.join(res[0][front:rear - 1]) + '日'))
        merge_token_list.append((res[0][rear - 1][1:]))
        res[0][front: rear] = merge_token_list
        merge_pos_list = ['TIME', 'v']
        res[1][front: rear] = merge_pos_list

    patter_list = ['([^\$]+?[^月]/TIME\$)(\d+/m\$)?(月[向起经]/[^\$]+?\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        # merge_token = ''.join(res[0][front:rear])
        merge_token_list = []
        merge_token_list.append((''.join(res[0][front:rear - 1]) + '月'))
        merge_token_list.append((res[0][rear - 1][1:]))
        res[0][front: rear] = merge_token_list
        merge_pos_list = ['TIME', 'v']
        res[1][front: rear] = merge_pos_list

    patter_list = ['([^\$]+?[^日]/TIME\$)(\d+/m\$)?(日向[^\$]+?/[^\$]+?\$)', ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        # merge_token = ''.join(res[0][front:rear])
        merge_token_list = []
        merge_token_list.append((''.join(res[0][front:rear - 1]) + '日'))
        # merge_token_list.append((res[0][front]+'日'))
        merge_token_list.append('向')
        merge_token_list.append((res[0][rear - 1][2:]))
        res[0][front: rear] = merge_token_list
        merge_pos_list = ['TIME', 'v']
        merge_pos_list.append(res[1][rear - 1])
        res[1][front: rear] = merge_pos_list

    return res


def merge_sensitive_mask(lac_res):
    res = deepcopy(lac_res)
    patter_list = [
        '((?<=\$)[×xX]+?/[^\$]+?\$)+',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'rs'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '((?<=\$)\d+?/[^\$]+?\$)([^\$]+?/rs\$)(\d+?/[^\$]+?\$)',
        '((?<=\$)第/[^\$]+?\$)([^\$]+?/rs\$)(号/[^\$]+?\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'm'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '([^\$]+?/rs\$)(县/[^\$]+?\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'LOC'
        res[1][front: rear] = [merge_pos, ]

    patter_list = [
        '((?<=\$)./PER\$)([^\$]+?/rs\$)',
    ]
    position_pair = find_position_by_pattern(res, patter_list)

    for _, front, rear in reversed(position_pair):
        merge_token = ''.join(res[0][front:rear])
        res[0][front: rear] = [merge_token, ]
        merge_pos = 'PER'
        res[1][front: rear] = [merge_pos, ]

    return res


lac = LAC(mode='lac')  # TODO 单例化
# lac.load_customization('./custom_file.txt', sep=None)


def process_lac_per_sent(sent):
    lac_result = lac.run(sent)

    # merge some pattern
    lac_result = merge_sensitive_mask(lac_result)
    lac_result = merge_book_name(lac_result)
    lac_result = merge_money(lac_result)
    lac_result = merge_time(lac_result)
    lac_result = merge_loc(lac_result)
    lac_result = merge_org(lac_result)

    return lac_result


def process_lac_per_sent_wrapper(args):
    uuid = args[0]
    sent = args[1]
    return uuid, process_lac_per_sent(sent)


def process_lac(sent_dict, process_max=None):
    # sent_dict = dict(islice(sent_dict.items(), 5))
    if process_max:
        sent_dict = dict(islice(sent_dict.items(), process_max))

    res = {}
    with Pool(55) as p:
        max_ = len(sent_dict)
        with tqdm(total=max_) as pbar:
            for i, r in enumerate(p.imap_unordered(process_lac_per_sent_wrapper, sent_dict.items())):
                res[r[0]] = r[1]
                pbar.update()
    return res


def save_lac_res(sent_lac_dict, file_basename):
    cur_dir = os.path.dirname(__file__)
    proj_dir = os.path.dirname(cur_dir)

    save_filepath = os.path.join(proj_dir, f'./corpus_data/{file_basename}.lac.pickle')

    with open(save_filepath, 'wb') as handle:
        pickle.dump(sent_lac_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


def main():
    # load pickle
    sent_dict = load_corpus_pickle()

    # 分词，词性标注
    # sent_lac_dict = process_lac(sent_dict, process_max=1000)
    sent_lac_dict = process_lac(sent_dict)

    # 保存结果
    save_lac_res(sent_lac_dict, 'lac_test')

    print('*' * 50)
    print('all finish')

    pass


if __name__ == "__main__":
    # main()
    print(process_lac_per_sent("奖金10.7万元和10.7万元"))
    # num_list = list(range(10))
    # print(list(product(num_list, repeat=2)))