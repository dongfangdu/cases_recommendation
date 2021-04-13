# -*- coding: utf-8 -*-

import jieba
import os
import heapq
import pickle
import json
from gensim import corpora, models, similarities


def __set_corpus(self):
    if not os.path.exists('corpus.pkl'):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open('corpus.pkl', 'rb') as f:
        self.corp = pickle.load(f)


def __vectorize(self):
    self.__set_corpus()
    tfidf = models.TfidfModel(self.corp)
    lda = models.LdaModel(self.corp, num_topics=5)
    lsi = models.LdaModel(self.corp)
    self.tfidf_vect = [tfidf[item] for item in self.corp]
    self.lda_vect = [lda[item] for item in self.corp]
    self.lsi_vect = [lsi[item] for item in self.corp]


def get_sim(self):
    with open('doc.json', 'r', encoding='gbk') as f:
        doc = json.load(f)
    self.dictionary = corpora.Dictionary.load_from_text('dictionary.txt')
    for doc_item in doc:
        sim = []
        for item in [self.tfidf_vect, self.lsi_vect, self.lda_vect]:
            index = similarities.SparseMatrixSimilarity(item, num_features=len(self.dictionary.keys()))
            sim.append(index[item[doc_item['id'] - 1]])
        sim = np.array(sim)
        sim_vec = np.mean(sim, axis=0)
        most_sim_doc_id = heapq.nlargest(11, range(len(sim_vec)), sim_vec.take)
        doc_item['sim'] = most_sim_doc_id
        print(doc_item['name'], '已计算', most_sim_doc_id)

    with open('doc.json', 'w', encoding='gbk') as f:
        f.truncate()
        json.dump(doc, f)
    print('----------计算相似文档结束！---------')


h = [3,5,6,7,10]
heapq.nlargest(3,range(len(h)),h.__getitem__)
# 这个list的内建方法取出index的值，但是不能像ndarray对象一样传入数组
# 没有使用数据库，将推荐结果统一写入到了josn文件中。