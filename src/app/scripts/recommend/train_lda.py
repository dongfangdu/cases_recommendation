# -*- coding: utf-8 -*-

import jieba
import codecs
import re
import pickle
import os
import sys
from gensim import corpora, models
from gensim.models import HdpModel
from app.configure import Config
from gensim.similarities import Similarity
from app.libs.common import get_abs_path
from app.libs.deal_func import clean_doc, clean_ner, get_lda_path
from app.libs.es import rec_model_doc
import pickle
import faiss
import numpy as np


aggregate_dict = get_abs_path(get_lda_path()['aggregate_dict_path'])
jieba.load_userdict(aggregate_dict)


def gen_data_path(data_path):
    data_path_dir = os.path.dirname(data_path)
    if not os.path.exists(data_path_dir):
        os.makedirs(data_path_dir)
    model_doc = rec_model_doc()
    f = open(data_path, 'w')
    with open(data_path, 'a') as f1:
        for info in model_doc.find({}, {"docId": 1, "docContent": 1}, no_cursor_timeout=True):
            docId = info['docId']
            docContent = info['docContent']
            f1.write("%s+%s\r\n" % (docId, docContent))
    f.close()


def gen_dict_and_pkl_and_mm(stopwords_path, data_path, data_dict_sv_path, data_mm_sv_path, data_pkl_sv_path):
    data_path_dir = os.path.dirname(data_path)
    if not os.path.exists(data_path_dir):
        os.makedirs(data_path_dir)
    stopwords = codecs.open(stopwords_path, 'r', encoding='utf8').readlines()
    stopwords = [w.strip() for w in stopwords]
    # stopwords = set(open('../data/stopwords.txt', encoding='utf8').read().strip('\n').split('\n'))
    corpora_documents = []
    with open(data_path, 'r') as f:
        for line in f.readlines():
            line = line.strip('\r\n')
            line = clean_doc(line)
            line = clean_ner(line)
            item_str = jieba.cut(line)
            corpora_documents.append([w for w in item_str if w not in stopwords])
    dictionary = corpora.Dictionary(corpora_documents)
    dictionary.save(data_dict_sv_path)
    corpus = [dictionary.doc2bow(text) for text in corpora_documents]
    corpora.MmCorpus.serialize(data_mm_sv_path, corpus)
    # corpora.MmCorpus.save_corpus("../data/corpus.mm", corpus)
    with open(data_pkl_sv_path, "wb") as f:
        pickle.dump(corpus, f)


def train_lda_model_and_lda_faiss_index(data_pkl_path, data_dict_path, model_sv_path, faiss_index_sv_path, is_hdp=True, num_topics=20):
    model_sv_dir = os.path.dirname(model_sv_path)
    if not os.path.exists(model_sv_dir):
        os.makedirs(model_sv_dir)
    if not os.path.exists(data_pkl_path):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open(data_pkl_path, 'rb') as f:
        corpus = pickle.load(f)
    dictionary = corpora.Dictionary.load(data_dict_path)
    if is_hdp:
        hdp = HdpModel(corpus, dictionary)
        hdp.save(model_sv_path)
        # hdp.save("../lda_model/jiedai.hdp")
    else:
        lda = models.LdaModel(corpus, id2word=dictionary, num_topics=num_topics)
        lda.save(model_sv_path)
        # lda.save("../lda_model/jiedai_2.lda")

    lenth = len(corpus)
    index = faiss.IndexFlatL2(num_topics)
    for sim_cor in range(lenth):
        lda_prob = lda[corpus[sim_cor]]
        # print("="*30)
        # print(len(lda_prob))
        # print(lda_prob)
        if len(lda_prob) == 1:
            index.add(np.array([[lda_prob[0][1], 0]]).astype('float32'))
        else:
            index.add(np.array([[lda_prob[0][1], lda_prob[1][1]]]).astype('float32'))
    faiss.write_index(index, faiss_index_sv_path)


def model_feature(model_path):
    # lda = models.LdaModel.load("../lda_model/all_fj.lda")
    # lda = models.LdaModel.load(model_path)
    # for i in range(10):
    # print(lda.print_topics(24, num_words=20))
    hdp = models.HdpModel.load(model_path)
    print(hdp.print_topics(200, num_words=1))
    # print(len(hdp.get_topics()))
    # print(len(hdp.get_topics()[0]))


def gen_data_lda(pickle_path, model_path, data_lda_save_path):#file_name为写入CSV文件的路径，datas为要写入数据列表
    # data_pickle = get_abs_path(get_lda_path()['pickle_path'])
    # lda_model = get_abs_path(get_lda_path()['model_path'])
    data_pickle = pickle_path
    lda_model = model_path
    lda = models.LdaModel.load(lda_model)
    with open(data_pickle, 'rb') as f:
        corpus = pickle.load(f)
    corpus_lda = [lda[doc] for doc in corpus]
    with open(data_lda_save_path, "wb") as f:
        pickle.dump(corpus_lda, f)


if __name__ == "__main__":
    # gen_data_path("/home/user/linjr/cases_recommendation/data/jiedai/jiedai.txt")
    # gen_dict_and_pkl_and_mm("/home/user/linjr/cases_recommendation/data/stopwords.txt",
    #                         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai.txt",
    #                         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai_dict.txt",
    #                         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai.mm",
    #                         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai.pkl")
    train_lda_model_and_lda_faiss_index(
                    "/home/user/linjr/cases_recommendation/data/jiedai/jiedai.pkl",
                    "/home/user/linjr/cases_recommendation/data/jiedai/jiedai_dict.txt",
                    "/home/user/linjr/cases_recommendation/lda_model/jiedai_2/jiedai_2.lda",
                    "/home/user/linjr/cases_recommendation/lda_model/jiedai_2/jiedai_2_faiss.index",
                    is_hdp=False, num_topics=2)
    gen_data_lda("/home/user/linjr/cases_recommendation/data/jiedai/jiedai.pkl",
                 "/home/user/linjr/cases_recommendation/lda_model/jiedai_2/jiedai_2.lda",
                 "/home/user/linjr/cases_recommendation/lda_model/jiedai_2/jiedai_2_lda.pkl")
