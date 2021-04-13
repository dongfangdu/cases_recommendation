# -*- coding: utf-8 -*-

import jieba
jieba.load_userdict('../data/aggregate_dict.txt')
import codecs
import re
import pickle
import os
import sys
from gensim import corpora, models
from gensim.models import HdpModel
from gensim.similarities import Similarity
sys.path.append("./NER_IDCNN_CRF")
from app.libs.NER_IDCNN_CRF.ner_api import NerApi

ner = NerApi()


def clean_doc(doc):
    # 汉字的Unicode范围为4e00-9fa5
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    filter_data = re.findall(pattern, doc)
    cleaned_doc = ''.join(filter_data)
    return cleaned_doc


def clean_ner(doc):
    ner_li = ner.get_ner(doc)
    ner_li = set([i["word"] for i in ner_li])
    ner_str = "|".join(ner_li)
    cleaned_doc = re.sub("%s" % ner_str, "", doc)
    return cleaned_doc


def gen_dict_and_pkl_and_mm():
    stopwords = codecs.open('../data/stopwords.txt', 'r', encoding='utf8').readlines()
    stopwords = [w.strip() for w in stopwords]
    # stopwords = set(open('../data/stopwords.txt', encoding='utf8').read().strip('\n').split('\n'))
    corpora_documents = []
    with open(r'../data/jiedai.txt', 'r') as f:
        for line in f.readlines():
            line = line.strip('\r\n')
            line = clean_doc(line)
            line = clean_ner(line)
            item_str = jieba.cut(line)
            corpora_documents.append([w for w in item_str if w not in stopwords])
    dictionary = corpora.Dictionary(corpora_documents)
    dictionary.save('../data/jiedai_dict.txt')
    corpus = [dictionary.doc2bow(text) for text in corpora_documents]
    corpora.MmCorpus.serialize("../data/jiedai.mm", corpus)
    # corpora.MmCorpus.save_corpus("../data/corpus.mm", corpus)
    with open("../data/jiedai.pkl", "wb") as f:
        pickle.dump(corpus, f)


def train_lda_model(is_hdp=True, num_topics=20):
    if not os.path.exists('../data/jiedai.pkl'):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open('../data/jiedai.pkl', 'rb') as f:
        corpus = pickle.load(f)
    dictionary = corpora.Dictionary.load('../data/jiedai_dict.txt')
    if is_hdp:
        hdp = HdpModel(corpus, dictionary)
        hdp.save("../lda_model/jiedai.hdp")
    else:
        lda = models.LdaModel(corpus, id2word=dictionary, num_topics=num_topics)
        lda.save("../lda_model/jiedai_50.lda")


def model_feature():
    # lda = models.LdaModel.load("../lda_model/all_fj.lda")
    # for i in range(10):
    # print(lda.print_topics(24, num_words=20))
    hdp = models.HdpModel.load("../lda_model/all_fj.hdp")
    print(hdp.print_topics(200, num_words=1))
    # print(len(hdp.get_topics()))
    # print(len(hdp.get_topics()[0]))


def test(test_doc):
    if not os.path.exists('../data/jiedai/jiedai.pkl'):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open('../data/jiedai/jiedai.pkl', 'rb') as f:
        corpus = pickle.load(f)
    lda = models.LdaModel.load("../lda_model/jiedai_2/jiedai_2.lda")
    dictionary = corpora.Dictionary.load('../data/jiedai/jiedai_dict.txt')
    corpus_lda = [lda[doc] for doc in corpus]
    similarity_lda = Similarity('demo-Similarity-Lda-index', corpus_lda, num_features=400, num_best=5)
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


def index(index_path):
    if not os.path.exists('../data/jiedai/jiedai.pkl'):
        print('----------未发现语料库，不能计算相似度！---------')
        return
    with open('../data/jiedai/jiedai.pkl', 'rb') as f:
        corpus = pickle.load(f)
    lda = models.LdaModel.load("../lda_model/jiedai_2/jiedai_2.lda")
    dictionary = corpora.Dictionary.load('../data/jiedai/jiedai_dict.txt')
    corpus_lda = [lda[doc] for doc in corpus]
    # similarity_lda = Similarity('demo-Similarity-Lda-index', corpus_lda, num_features=400, num_best=20)
    # print(similarity_lda)
    #  1.测试数据
    # test_data = ""
    test_data = codecs.open("../data/jiedai/jiedai_test.txt", 'r', encoding='utf8').read()
    test_cut_raw = jieba.cut(test_data)
    print('测试数据', test_cut_raw)
    # 2.转换成bow向量 # [(51, 1), (59, 1)]，即在字典的52和60的地方出现重复的字段，这个值可能会变化
    test_corpus = dictionary.doc2bow(test_cut_raw)
    _index = Similarity('demo-Similarity-Lda-index', corpus_lda, num_features=400, num_best=20)
    # _index = Similarity.load(index_path)
    vec_lda = lda[test_corpus]
    sims = _index[vec_lda]
    print(sorted(enumerate(sims)))
    sims = sorted(enumerate(sims), key=lambda item: -item[1][1])
    print(sims)


if __name__ == "__main__":
    # gen_dict_and_pkl_and_mm()
    # train_lda_model(is_hdp=False, num_topics=50)
    # model_feature()
    # test("../data/jiedai/jiedai_test.txt")
    # gen_corpus_mm()
    index('demo-Similarity-Lda-index.0')


