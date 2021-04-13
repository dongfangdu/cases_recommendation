import time
from flask import request, render_template, jsonify, current_app
from app.api.docs import doc_bp
from app.model.base_db import NewDoc, ModelDoc
from app.configure import Config
from app.scripts.docs.get_md5 import get_md5
from app.libs.response_code import *
from app.scripts.docs.upload_set import text
from flasgger.utils import swag_from
import logging


@doc_bp.route('/favicon.ico')
def favicon():
    """返回项目的图标"""
    # send_static_file 找到static文件夹下面的静态文件发送给浏览器显示
    return current_app.send_static_file("favicon.ico")


@doc_bp.route('/', methods=["GET", 'POST'])
@swag_from("spec_docs/upload_file.yml", methods=['POST'])
def upload_file():
    if request.method == "POST":
        try:
            li = []
            stat = {"all": 0, "err": 0, "ok": 0}
            # print(request.files)
            for st in request.files.getlist('text'):
                stat["all"] += 1
                filename = st.filename
                bytes_stream = st.stream.read()
                file_md5 = get_md5(bytes_stream)
                if len(bytes_stream) == 0:
                    current_app.logger.error("%s 文件不可为空" % filename)
                    li.append({
                        "errcode": RESCODE.UPLOAD_ERROR,
                        "docId": file_md5,
                        "errmsg": "%s 文件不可为空" % filename,
                    })
                    stat["err"] += 1
                    continue
                if not text.detect_ext(filename):
                    current_app.logger.error("%s 要求txt格式文件" % filename)
                    li.append({
                        "errcode": RESCODE.UPLOAD_ERROR,
                        "docId": file_md5,
                        "errmsg": "%s 编码有误，请修正后上传" % filename,
                    })
                    stat["err"] += 1
                    continue
                try:
                    docContent = bytes_stream.decode("utf8")
                except:
                    try:
                        docContent = bytes_stream.decode("gbk")
                    except Exception as e:
                        current_app.logger.error(e)
                        li.append({
                            "errcode": RESCODE.UPLOAD_ENCODE_ERROR,
                            "docId": file_md5,
                            "errmsg": "%s 编码有误，请修正后上传" % filename,
                        })
                        stat["err"] += 1
                        continue
                try:
                    try:
                        # logging.info(time.time())
                        NewDoc(docId=file_md5, docContent=docContent, doc_name=filename,
                               newdoc_status=RESCODE.WAITING, recommend_status=RESCODE.WAITING).save()
                        if Config.SAVE_NEW_DOC:
                            st.stream.seek(0, 0)
                            text.save(st)
                        li.append({
                            "errcode": RESCODE.UPLOAD_OK,
                            "docId": file_md5,
                            "errmsg": "%s 上传成功" % filename,
                        })
                        stat["ok"] += 1
                    except Exception as e:
                        if "duplicate" in e.args[0]:
                            current_app.logger.info("%s 已上传过，将更新文件名及上传时间" % filename)
                        else:
                            current_app.logger.error("%s 文件保存失败" % filename)
                        NewDoc.objects(docId=file_md5).update(doc_name=filename, create_at=time.time())
                        li.append({
                            "errcode": RESCODE.UPLOAD_OK,
                            "docId": file_md5,
                            "errmsg": "%s 已上传过相同内容，将更新文件名" % filename,
                        })
                        stat["ok"] += 1
                except Exception as e:
                    current_app.logger.error(e)
                    li.append({
                        "errcode": RESCODE.UPLOAD_ERROR,
                        "docId": file_md5,
                        "errmsg": "%s 上传失败" % filename,
                    })
                    stat["err"] += 1
            return jsonify(data=li, stat=stat, errcode=RESCODE.OK, errmsg="上传成功")
            # return render_template('upload.html', text_li=li)
        except:
            return jsonify(data=[], stat={}, errcode=RESCODE.ERR, errmsg="上传失败")
    elif request.method == "GET":
        return render_template('index.html')


@doc_bp.route('/model-docs-list', methods=["GET"])
@swag_from("spec_docs/model_doc_list.yml", methods=["GET"])
def get_model_doc_list():
    params_dict = request.args
    page = params_dict.get("page", 1)
    per_page = params_dict.get("per_page", Config.MODEL_PAGE_MAX_DOCS)

    if not all([page, per_page]):
        return jsonify(errcode=RESCODE.PARAMERR, errmsg="参数不足", data={})
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RESCODE.TYPEERR, errmsg="数据类型错误", data={})

    try:
        paginate = ModelDoc.objects.paginate(page=page, per_page=per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RESCODE.DBERR, errmsg="查询文书列表数据异常", data={})

    items = paginate.items
    current_page = paginate.page
    # total_page = paginate.pages
    total = ModelDoc.objects.count()
    docs_dict_list = []
    for doc in items if items else []:
        docs_dict_list.append(doc.to_dict_list())

    data = {
        "docsList": docs_dict_list,
        "current_page": current_page,
        "total": total
    }
    return jsonify(errcode=RESCODE.OK, errmsg="查询文书列表数据成功", data=data)


@doc_bp.route('/model/<docId>', methods=["GET"])
@swag_from("spec_docs/model_doc_detail.yml", methods=["GET"])
def get_model_doc_detail(docId):
    model_doc = ModelDoc.objects(docId=docId).first()
    if not model_doc:
        current_app.logger.error("%s 文档不存在" % docId)
        return jsonify(errcode=RESCODE.ERR, errmsg="文档不存在，查询失败", data={})
    data = model_doc.to_dict_detail()
    return jsonify(errcode=RESCODE.OK, errmsg="查询文书详情数据成功", data=data)


@doc_bp.route('/new/<docId>', methods=["GET"])
@swag_from("spec_docs/new_doc_detail.yml", methods=["GET"])
def get_new_doc_detail(docId):
    model_doc = NewDoc.objects(docId=docId).first()
    if not model_doc:
        current_app.logger.error("docId:%s 文档不存在" % docId)
        return jsonify(errcode=RESCODE.ERR, errmsg="文档不存在，查询失败")
    data = model_doc.to_dict_detail()
    return jsonify(errcode=RESCODE.OK, errmsg="查询上传文件详情数据成功", data=data)


@doc_bp.route('/new-docs-list', methods=["GET"])
@swag_from("spec_docs/new_doc_list.yml", methods=["GET"])
def get_new_doc_list():
    params_dict = request.args
    page = params_dict.get("page", 1)
    per_page = params_dict.get("per_page", Config.NEW_PAGE_MAX_DOCS)

    if not all([page, per_page]):
        return jsonify(errcode=RESCODE.PARAMERR, errmsg="参数不足")
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RESCODE.PARAMERR, errmsg="数据类型错误")
    try:
        paginate = NewDoc.objects.paginate(page=page, per_page=per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errcode=RESCODE.DBERR, errmsg="查询上传文件列表数据异常")

    items = paginate.items
    current_page = paginate.page
    # total_page = paginate.pages
    total = NewDoc.objects.count()

    docs_dict_list = []
    for doc in items if items else []:
        docs_dict_list.append(doc.to_dict_list())

    data = {
        "docsList": docs_dict_list,
        "current_page": current_page,
        "total": total
    }
    return jsonify(errcode=RESCODE.OK, errmsg="查询上传文件列表数据成功", data=data)
