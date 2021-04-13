# -*- coding: utf-8 -*-

import logging
from app.api.es import ind
from flask import request, json
from app.libs.response_code import RESCODE
from flasgger.utils import swag_from
from app.scripts.es.full_text_index import full_index, execute_index, keyword_index


@ind.route('/full-doc-index', methods=['POST'])
@swag_from("spec_docs/full_doc_index.yml", methods=["POST"])
def full_doc_index():
    try:
        data = json.loads(request.get_data())
        element_list = data['element_list']
        sort_element = data['sort_element']
        sort_sc = data['sort_sc']
        docId_list = full_index(element_list, sort_element, sort_sc)
        logging.info("全文检索成功")
        errcode = RESCODE.FULL_TEXT_INDEX_OK
        return json.dumps({"docId_list": docId_list, "errcode": errcode})
    except:
        errcode = RESCODE.FULL_TEXT_INDEX_ERROR
        logging.error("全文检索失败")
        return json.dumps({"docId_list": None, "errcode": errcode})


@ind.route('/execute-doc-index', methods=['POST'])
@swag_from("spec_docs/execute_doc_index.yml", methods=["POST"])
def execute_doc_index():
    # try:
    data = json.loads(request.get_data())
    element_dict = data['element_dict']
    sort_element = data['sort_element']
    sort_sc = data['sort_sc']
    docId_list = execute_index(element_dict, sort_element, sort_sc)
    logging.info("精确检索成功")
    errcode = RESCODE.EXECUTE_INDEX_OK
    return json.dumps({"docId_list": docId_list, "errcode": errcode})
    # except:
    #     errcode = RESCODE.EXECUTE_INDEX_ERROR
    #     logging.error("精确检索失败")
    #     return json.dumps({"docId_list": None, "errcode": errcode})


@ind.route('/keyword-doc-index', methods=['POST'])
@swag_from("spec_docs/keyword_doc_index.yml", methods=["POST"])
def keyword_doc_index():
    try:
        data = json.loads(request.get_data())
        element_list = data['element_list']
        weight_list = data['weight_list']
        docId_list = keyword_index(element_list, weight_list)
        logging.info("关键词检索成功")
        errcode = RESCODE.FULL_TEXT_INDEX_OK
        return json.dumps({"docId_list": docId_list, "errcode": errcode})
    except:
        errcode = RESCODE.FULL_TEXT_INDEX_ERROR
        logging.error("关键词检索失败")
        return json.dumps({"docId_list": None, "errcode": errcode})
