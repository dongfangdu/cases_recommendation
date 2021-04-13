from app.api.elements_extract import ele_ext
from flask import request, json
import logging
from app.libs.response_code import RESCODE
from app.model.base_db import NewDoc
from flasgger.utils import swag_from
from app.libs.es import rec_new_doc
from app.scripts.element_extract.tatol_elements_extract import tat_ele_ext


@ele_ext.route('/elements_extract', methods=['POST'])
@swag_from("spec_docs/elements_extract.yml", methods=["POST"])
def element_extract():
    data = json.loads(request.get_data())
    doc_id = data['docId']
    try:
        new_doc = rec_new_doc()
        tat_ele_ext(new_doc, doc_id)
        newdoc_status = RESCODE.EXTRACTING_OK
        NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
        logging.info("上传文档要素提取成功")
        return json.dumps({'errcode': newdoc_status})
    except:
        newdoc_status = RESCODE.EXTRACTING_ERROR
        NewDoc.objects(docId=doc_id).update(newdoc_status=newdoc_status)
        logging.error("上传文档要素提取失败")
        return json.dumps({'errcode': newdoc_status})
