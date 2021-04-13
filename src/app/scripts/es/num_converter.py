# -*- coding: utf-8 -*-
"""
"""
import re


def get_number(str_han):
    res = 0
    if str_han in '一壹幺':
        res = 1
    elif str_han in '二贰两':
        res = 2
    elif str_han in '三叁':
        res = 3
    elif str_han in '四肆':
        res = 4
    elif str_han in '五伍':
        res = 5
    elif str_han in '六陆':
        res = 6
    elif str_han in '七柒':
        res = 7
    elif str_han in '八捌':
        res = 8
    elif str_han in '九玖':
        res = 9
    elif str_han in '十拾':
        res = 10
    return res


def get_base_number(str_han):
    res = 1
    if str_han in '十拾':
        res = 10
    elif str_han in '百佰':
        res = 100
    elif str_han in '千仟':
        res = 1000
    elif str_han in '万萬':
        res = 10000
    elif str_han in '亿億':
        res = 100000000

    return res


def format_text_to_number(text_han_unicode, level=0):
    res = 0
    if len(text_han_unicode) == 1:
        res = get_number(text_han_unicode)
    else:
        str_number = text_han_unicode[:-1]
        str_maybe_base = text_han_unicode[-1]
        if len(text_han_unicode) == 2:
            res = get_number(str_number) * get_base_number(str_maybe_base)
        else:
            re_rule = '([零一幺二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟亿]+亿)?零?([一幺二两三四五六七八九百千壹贰叁肆伍陆柒捌玖十拾佰仟]+万)?零?([一幺二两三四五六七八九十百壹贰叁肆伍陆柒捌玖拾佰][千仟])?零?([一幺二两三四五六七八九十壹贰叁肆伍陆柒捌玖拾][百佰])?零?([一幺二两三四五六七八九壹贰叁肆伍陆柒捌玖]?[十拾])?零?([一幺二两三四五六七八九壹贰叁肆伍陆柒捌玖])?'
            result = re.finditer(re_rule, str_number)

            counter = 0
            start_idx = 0
            for p in result:
                for g in p.groups():
                    if g:
                        tmp = format_text_to_number(g, level + 1)
                        idx = text_han_unicode.index(g, start_idx)
                        if tmp < 10:
                            if idx > 0:
                                if text_han_unicode[idx - 1] != '零':
                                    base = (get_base_number(text_han_unicode[idx - 1]) / 10)
                                    if base == 0:
                                        res *= 10
                                    tmp *= base or 1
                        res += tmp
                        start_idx = idx + len(g)
                    counter += 1
            res *= get_base_number(str_maybe_base)
    res = int(res)
    return res


def format_sentence(sentence):
    re_rule = '([零一幺二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟亿]+亿)?零?([一幺二两三四五六七八九百千壹贰叁肆伍陆柒捌玖十拾佰仟]+万)?零?([一幺二两三四五六七八九十百壹贰叁肆伍陆柒捌玖拾佰][千仟])?零?([一幺二两三四五六七八九十壹贰叁肆伍陆柒捌玖拾][百佰])?零?([一幺二两三四五六七八九壹贰叁肆伍陆柒捌玖]?[十拾])?零?([一幺二两三四五六七八九壹贰叁肆伍陆柒捌玖])?'
    result = re.finditer(re_rule, sentence)
    new_sentence = sentence

    for p in result:
        sub_str = p.group()
        if sub_str:
            place_str = ''
            for c in sub_str:
                if c != '零':
                    break
                place_str += '0'
            if len(place_str) == len(sub_str):
                new_sentence = new_sentence.replace(sub_str, place_str, 1)
            else:
                new_sentence = new_sentence.replace(
                    sub_str, '{}{}'.format(place_str, format_text_to_number('{} '.format(sub_str))), 1
                )
    return new_sentence


def _format_sentence(str_han):
    pattern = re.compile(r'(\d+(\.\d+)?)')
    if ('点' in str_han or '.' in str_han) and ('万' in str_han or '亿' in str_han) \
            and (('点' in str_han and (str_han.find('点') < str_han.find('万') or str_han.find('点') < str_han.find('亿')))
                 or ('.' in str_han and (str_han.find('.') < str_han.find('万') or str_han.find('.') < str_han.find('亿')))):
        if '万' in str_han and '亿' not in str_han:
            str_han = str_han.replace('万', '')
            str_han = format_sentence(str_han)
            if '点' in str_han:
                str_han = str_han.replace('点', '.')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han*10000
            elif re.search(pattern, str_han) is None:
                str_han = 0
        elif '亿' in str_han and '万' not in str_han:
            str_han = str_han.replace('亿', '')
            str_han = format_sentence(str_han)
            if '点' in str_han:
                str_han = str_han.replace('点', '.')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han*100000000
            elif re.search(pattern, str_han) is None:
                str_han = 0
        elif '亿' in str_han and '万' in str_han:
            str_han = str_han.replace('万', '')
            str_han = str_han.replace('亿', '万')
            str_han = format_sentence(str_han)
            if '点' in str_han:
                str_han = str_han.replace('点', '.')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han * 10000
            elif re.search(pattern, str_han) is None:
                str_han = 0
    elif '点' in str_han:
        str_han = format_sentence(str_han)
        str_han = str_han.replace('点', '.')
        if re.search(pattern, str_han) is not None:
            str_han = float(re.search(pattern, str_han).group(0))
        elif re.search(pattern, str_han) is None:
            str_han = 0
    else:
        str_han = format_sentence(str_han)
        if '万' in str_han and '亿' not in str_han:
            str_han = str_han.replace('万', '')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han*10000
            elif re.search(pattern, str_han) is None:
                str_han = 0
        elif '亿' in str_han and '万' not in str_han:
            str_han = str_han.replace('亿', '')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han*100000000
            elif re.search(pattern, str_han) is None:
                str_han = 0
        elif '亿' in str_han and '万' in str_han:
            str_han = str_han.replace('万', '')
            str_han = str_han.replace('亿', '万')
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
                str_han = str_han * 10000
            elif re.search(pattern, str_han) is None:
                str_han = 0
        else:
            if re.search(pattern, str_han) is not None:
                str_han = float(re.search(pattern, str_han).group(0))
            elif re.search(pattern, str_han) is None:
                str_han = 0
    return str_han


if __name__ == '__main__':
    print(_format_sentence('最高限额为捌亿伍仟万元'))