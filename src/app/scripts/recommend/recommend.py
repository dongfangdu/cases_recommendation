# -*- coding: utf-8 -*-

import jieba
import re
import pickle
import os
from jieba.analyse import extract_tags, textrank
from gensim import corpora, models
from gensim.similarities import Similarity
from app.model.base_db import NewDoc, ModelDoc
from app.model.base_db import Result
from app.configure import Config
from app.libs.common import get_abs_path
from app.libs.deal_func import clean_doc, clean_ner, get_lda_path
from time import time
import logging
import random
import numpy as np
import faiss


aggregate_dict = get_abs_path(get_lda_path()['aggregate_dict_path'])
jieba.load_userdict(aggregate_dict)


class Recommend:
    def __init__(self):
        data_pickle = get_abs_path(get_lda_path()['pickle_path'])
        lda_model = get_abs_path(get_lda_path()['model_path'])
        data_dict = get_abs_path(get_lda_path()['dict_path'])
        data_lda_list_pickle = get_abs_path(get_lda_path()['data_lda_path'])
        stopwords_path = get_abs_path(get_lda_path()['stopwords_path'])

        with open(data_pickle, 'rb') as f:
            self.corpus = pickle.load(f)

        stopwords = open(stopwords_path, 'r', encoding='utf8').readlines()
        self.lda = models.LdaModel.load(lda_model)
        self.dictionary = corpora.Dictionary.load(data_dict)
        self.num_feature = int(get_lda_path()['num_feature'])
        self.num_best = int(get_lda_path()['num_best'])
        self.index = get_lda_path()['index']
        self.stopwords = [w.strip() for w in stopwords]

        with open(data_lda_list_pickle, 'rb') as f:
            self.corpus_lda = pickle.load(f)

        self.faiss_index_sv_path = get_abs_path(get_lda_path()['faiss_index_sv_path'])

    def get_info(self, doc_id):
        info = NewDoc.objects(docId=doc_id).first()
        return info

    def recommend(self, doc_id):
        # 采用lda模型计算相似度推荐
        # corpus_lda = [self.lda[doc] for doc in self.corpus]
        corpus_lda = self.corpus_lda
        similarity_lda = Similarity(self.index, corpus_lda, self.num_feature, self.num_best)
        # print(similarity_lda)
        # 测试数据
        info = self.get_info(doc_id)
        test_data = info.docContent
        test_cut_raw = jieba.cut(test_data)
        # 转换成bow向量 # [(51, 1), (59, 1)]，即在字典的52和60的地方出现重复的字段，这个值可能会变化
        test_corpus = self.dictionary.doc2bow(test_cut_raw)
        # print('测试语料', test_corpus)
        # 计算lda值
        test_corpus_lda = self.lda[test_corpus]
        # print('Lda值', test_corpus_lda)
        # print('——————————————lda———————————————')
        # print('相似度:', similarity_lda[test_corpus_lda])
        result_dict = self.gen_result_dict(similarity_lda[test_corpus_lda])
        return result_dict

    def faiss_recommend(self, doc_id):
        # 采用lda模型、faiss计算相似度推荐

        corpus_lda = self.corpus_lda
        similarity_lda = Similarity(self.index, corpus_lda, self.num_feature, self.num_best)

        info = self.get_info(doc_id)
        test_data = info.docContent
        test_cut_raw = jieba.cut(test_data)
        # 转换成bow向量 # [(51, 1), (59, 1)]，即在字典的52和60的地方出现重复的字段，这个值可能会变化
        test_corpus = self.dictionary.doc2bow(test_cut_raw)
        # print('测试语料', test_corpus)
        # 计算lda值
        test_corpus_lda = self.lda[test_corpus]
        new_test_corpus_lda = []
        if len(test_corpus_lda) == 1:
            if test_corpus_lda[0][0] == 0:
                new_test_corpus_lda.append(test_corpus_lda[0][1])
                new_test_corpus_lda.append(0)
            elif test_corpus_lda[0][0] == 1:
                new_test_corpus_lda.append(0)
                new_test_corpus_lda.append(test_corpus_lda[0][1])
        elif len(test_corpus_lda) == 2:
            new_test_corpus_lda.append(test_corpus_lda[0][1])
            new_test_corpus_lda.append(test_corpus_lda[1][1])
        _test_corpus_lda = np.array([new_test_corpus_lda]).astype('float32')
        index = faiss.read_index(self.faiss_index_sv_path)
        D, I = index.search(_test_corpus_lda, 20)
        D_max = 1/min(D[0])
        D_min = 1/max(D[0])
        similarity_test_corpus_lda = []

        for i in range(20):
            score = ((1-0.8)/(D_max-D_min))*(1/D[0, i]-D_min) + 0.8
            similarity_test_corpus_lda.append(tuple([I[0, i], score]))
        result_dict = self.gen_result_dict(similarity_test_corpus_lda)
        return result_dict

    def get_new_doc_element(self, doc_id):
        info = self.get_info(doc_id)
        text = info.docContent
        keyword_list = self.gen_element(text)
        return keyword_list

    def gen_element(self, text, typ="extract_tags"):
        text = clean_doc(text)
        text = clean_ner(text)
        text = ' '.join(jieba.cut(text))
        text = ' '.join(w for w in text.split(' ') if w not in self.stopwords)
        keyword_list = []
        
        #  if typ == "extract_tags":
            # for keyword, weight in extract_tags(text, withWeight=True):
                # keyword_list.append(keyword)
        # elif typ == "textrank":
            # for keyword, weight in textrank(text, withWeight=True):
                #  keyword_list.append(keyword)

        mid_aggregate_keyword_list = []
        fina_aggregate_keyword_list = []
        with open(aggregate_dict, 'r') as f:
            aggregate_words_list = f.readlines()
            for aggregate_word in aggregate_words_list:
                if aggregate_word.strip() in text:
                    mid_aggregate_keyword_list.append(aggregate_word.strip())
            # mid_aggregate_keyword_list.sort(key=lambda x:len(x), reverse=True)
            if typ == "extract_tags":
                for keyword, weight in extract_tags(text, topK=20, withWeight=True):
                    keyword_list.append(keyword)
                    if keyword in mid_aggregate_keyword_list:
                        fina_aggregate_keyword_list.append({keyword: weight})
                fina_aggregate_keyword_list.sort(key=lambda e: [i for i in e.values()][0], reverse=True)
                if len(mid_aggregate_keyword_list) > 10:
                    keyword_list = keyword_list[:10] + mid_aggregate_keyword_list[:10]
                else:
                    keyword_list = keyword_list[:-len(mid_aggregate_keyword_list)] + mid_aggregate_keyword_list
                random.shuffle(keyword_list)
                # print(keyword_list)

            elif typ == "textrank":
                for keyword in textrank(text):
                    keyword_list.append(keyword)
        return keyword_list
# 
    # def gen_result_dict(self, similarity_list):
        # h_score = similarity_list[0][1]
        # l_score = similarity_list[-1][1]
        # result_list = []
        # i = 1
        # for result in similarity_list:
            # result_dict = {}
            # model_id = result[0]
            # doc_id = self.model_id_2_doc_id(model_id)
            # score = result[1]
            # score = round((score-0.01)*(0.997**i)*10, 1)
            # i += 1
            # rec_title, rec_text = self.doc_id_2_rec_title_text(doc_id)
            # keyword_list = self.gen_element(rec_text)
            # result_dict["docId"] = doc_id
            # result_dict["score"] = self.stand_score(score, h_score, l_score)
            # result_dict["score"] = score
            # result_dict["element"] = keyword_list
            # result_dict["title"] = rec_title
            # result_list.append(result_dict)
        # return result_list

    def gen_result_dict(self, similarity_list):
        h_score = similarity_list[0][1]
        l_score = similarity_list[-1][1]
        result_list = []

        i = 1
        for result in similarity_list:
            result_dict = {}
            model_id = result[0]
            doc_id = self.model_id_2_doc_id(model_id)
            score = result[1]
            # score = round((score-0.01)*(0.997**i)*10, 1)
            score = round((score - 0.01) * (0.9999 ** i) * 10, 1)
            i += 1
            rec_title, rec_text = self.doc_id_2_rec_title_text(doc_id)
            if not rec_title:
                continue
            keyword_list = self.gen_element(rec_text)

            ### extract info
            info = ModelDoc.objects(docId=doc_id).first()
            rela = {}
            for rela_dict in info.relaInfo:
                rela[rela_dict["name"]] = rela_dict["value"]
            legal = {}
            for legal_dict in info.legalBase:
                item_element = []
                for item in legal_dict["Items"]:
                    # print("legalName: {legalName}".format(legalName=item["legalName"]))
                    item_element.append(item["legalName"])
                legal[legal_dict["legalRuleName"]] = item_element

            result_dict["docId"] = doc_id
            # result_dict["score"] = self.stand_score(score, h_score, l_score)
            result_dict["score"] = score
            result_dict["element"] = keyword_list
            result_dict["title"] = rec_title
            result_dict["rela"] = rela
            result_dict["legal"] = legal
            result_list.append(result_dict)
        return result_list

    def model_id_2_doc_id(self, model_id):
        doc_id = Result.objects(model_id=str(model_id)).first().doc_id
        return doc_id

    def doc_id_2_rec_title_text(self, doc_id):
        info = ModelDoc.objects(docId=doc_id).first()
        if info:
            rec_title = info.doc_name
            rec_text = info.docContent
        else:
            rec_title = None
            rec_text = None
        return rec_title, rec_text

    def stand_score(self, score, h_score, l_score):
        score = (score-l_score-0.3)/(h_score-l_score-0.3)-0.1
        # round(((score-0.01)**10)*10, 1)
        return score


if __name__ == "__main__":
    a = Recommend()
    a.recommend("1018e1d14ffe643573bc45345fed4e4f")
    # gen_result_dict([(19017, 1.0), (3090, 1.0), (734, 1.0), (9503, 1.0), (8101, 1.0), (8152, 1.0), (10361, 0.9999999403953552),\
    #  (214, 0.9999999403953552), (1659, 0.9999999403953552), (1128, 0.9999999403953552)])
