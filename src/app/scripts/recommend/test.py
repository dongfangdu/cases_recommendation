import codecs
import re
import pickle
import os
import sys
from gensim import corpora, models
from gensim.models import HdpModel
from app.configure import Config
from app.libs.common import get_abs_path
from app.libs.deal_func import clean_doc, clean_ner, get_lda_path
from gensim.similarities import Similarity
import jieba

aggregate_dict = get_abs_path(get_lda_path()['aggregate_dict_path'])
jieba.load_userdict(aggregate_dict)


def test(data_pkl_path, model_path, data_dict_path, test_doc, num_features=400, num_best=20):
    if not os.path.exists(data_pkl_path):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open(data_pkl_path, 'rb') as f:
        corpus = pickle.load(f)
    lda = models.LdaModel.load(model_path)
    dictionary = corpora.Dictionary.load(data_dict_path)
    corpus_lda = [lda[doc] for doc in corpus]
    similarity_lda = Similarity('demo-Similarity-Lda-index', corpus_lda, num_features, num_best)
    # print(similarity_lda)
    #  1.测试数据
    # test_data = ""
    test_data = codecs.open(test_doc, 'r', encoding='utf8').read()
    test_cut_raw = jieba.cut(test_data)
    print('测试数据', test_cut_raw)
    # 2.转换成bow向量 # [(51, 1), (59, 1)]，即在字典的52和60的地方出现重复的字段，这个值可能会变化
    test_corpus = dictionary.doc2bow(test_cut_raw)
    print('测试语料', test_corpus)
    # 3.计算tfidf值  # 根据之前训练生成的model，生成query的TFIDF值，然后进行相似度计算
    # test_corpus_tfidf_3 = tfidf_model[test_corpus_3]
    # print('TFIDF值', test_corpus_tfidf_3) # [(51, 0.7071067811865475), (59, 0.7071067811865475)]
    # 4.计算lda值
    test_corpus_lda = lda[test_corpus]
    print('Lda值', test_corpus_lda)
    print('——————————————lda———————————————')
    print('相似度:', similarity_lda[test_corpus_lda])
    # 另一种计算相似度的方法，结果一样
    # sims = similarity_lda[test_corpus_lda]
    # print(sorted(enumerate(sims)))
    # sims = sorted(enumerate(sims), key=lambda item: -item[1][1])
    # print(sims)


if __name__ == "__main__":
    test("/home/user/linjr/cases_recommendation/data/jiedai/jiedai.pkl",
         "/home/user/linjr/cases_recommendation/lda_model/jiedai_2/jiedai_2.lda",
         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai_dict.txt",
         "/home/user/linjr/cases_recommendation/data/jiedai/jiedai_test.txt",
         num_features=500, num_best=100)
