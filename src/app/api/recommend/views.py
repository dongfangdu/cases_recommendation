# -*- coding: utf-8 -*-

import logging
from app.api.recommend import rec
from flask import request, json
from app.scripts.recommend.recommend import Recommend
from app.scripts.recommend.recommend_st import Recommend_st
from app.libs.response_code import RESCODE
from app.model.base_db import NewDoc
from concurrent.futures import ThreadPoolExecutor
from flasgger.utils import swag_from
from app.scripts.element_extract.tatol_elements_extract import tat_ele_ext
from app.libs.es import rec_new_doc
from time import time
from app.scripts.recommend.train_lda import gen_data_path, gen_dict_and_pkl_and_mm, train_lda_model_and_lda_faiss_index, gen_data_lda


executor = ThreadPoolExecutor(max_workers=40)


def _recommend(doc_id):
    recommend = Recommend()
    newdoc_status = RESCODE.EXTRACTING
    NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
    # try:
    #     new_doc_keyword_list = recommend.get_new_doc_element(doc_id)
    #     newdoc_status = RESCODE.EXTRACTING_OK
    #     NewDoc.objects(docId=doc_id).update(element=new_doc_keyword_list, newdoc_status=newdoc_status)
    #     logging.info("上传文档要素提取成功")
    # except:
    #     newdoc_status = RESCODE.EXTRACTING_ERROR
    #     NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
    #     logging.error("上传文档要素提取失败")
    try:
        new_doc = rec_new_doc()
        tat_ele_ext(new_doc, doc_id)
        newdoc_status = RESCODE.EXTRACTING_OK
        NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
        logging.info("上传文档要素提取成功")
    except:
        newdoc_status = RESCODE.EXTRACTING_ERROR
        NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
        logging.error("上传文档要素提取失败")
    if newdoc_status == RESCODE.EXTRACTING_OK:
        recommend_status = RESCODE.RECOMMENDING
        NewDoc.objects(docId=doc_id).update(recommend_status=recommend_status)
        try:
            recommend_result = recommend.faiss_recommend(doc_id)
            # recommend_result = recommend.recommend(doc_id)
            recommend_status = RESCODE.RECOMMENDING_OK
            NewDoc.objects(docId=doc_id).update(recommend_status=recommend_status, recommend=recommend_result)
            logging.info("类案推荐成功")
        except:
            recommend_status = RESCODE.RECOMMENDING_ERROR
            NewDoc.objects(docId=doc_id).update(recommend_status=recommend_status)
            logging.error("类案推荐失败")


@rec.route('/recommend', methods=['POST'])
@swag_from("spec_docs/recommend.yml", methods=["POST"])
def recommend():
    try:
        data = json.loads(request.get_data())
        doc_id = data['docId']
        executor.submit(_recommend, doc_id)
        errcode = RESCODE.OK
        return json.dumps({'errcode': errcode})
    except:
        errcode = RESCODE.ERR
        return json.dumps({'errcode': errcode})


def _model_train(stopwords_txt, corpus_txt, dict_txt, corpus_mm, corpus_pkl, model_lda, faiss_index, num_topics, model_pkl):
    gen_dict_and_pkl_and_mm(stopwords_txt, corpus_txt, dict_txt, corpus_mm, corpus_pkl)
    train_lda_model_and_lda_faiss_index(corpus_pkl, dict_txt, model_lda, faiss_index, is_hdp=False,
                                        num_topics=num_topics)
    gen_data_lda(corpus_pkl, model_lda, model_pkl)

@rec.route('/model_train', methods=['POST'])
@swag_from("spec_docs/model_train.yml", methods=["POST"])
def model_train():
    data = json.loads(request.get_data())
    corpus_txt = data['corpus_txt']
    stopwords_txt = data['stopwords_txt']
    dict_txt = data['dict_txt']
    corpus_mm = data['corpus_mm']
    corpus_pkl = data['corpus_pkl']
    model_lda = data['model_lda']
    faiss_index = data['faiss_index']
    num_topics = data['num_topics']
    model_pkl = data['model_pkl']
    try:
        # gen_dict_and_pkl_and_mm(stopwords_txt, corpus_txt, dict_txt, corpus_mm, corpus_pkl)
        # train_lda_model_and_lda_faiss_index(corpus_pkl, dict_txt, model_lda, faiss_index, is_hdp=False, num_topics=num_topics)
        # gen_data_lda(corpus_pkl, model_lda, model_pkl)
        executor.submit(_model_train, stopwords_txt, corpus_txt, dict_txt, corpus_mm, corpus_pkl, model_lda, faiss_index, num_topics, model_pkl)
        errcode = RESCODE.OK
        return json.dumps({'errcode': errcode})
    except:
        errcode = RESCODE.ERR
        return json.dumps({'errcode': errcode})


@rec.route('/recommend_st', methods=['POST'])
@swag_from("spec_docs/recommend_st.yml", methods=["POST"])
def recommend_st():
    try:
        data = json.loads(request.get_data())
        input_data = data['input_data']
        output_data = Recommend_st().faiss_recommend(input_data)
        errcode = RESCODE.OK
        return json.dumps({'output_data': output_data, 'errcode': errcode})
    except:
        errcode = RESCODE.ERR
        return json.dumps({'errcode': errcode})
