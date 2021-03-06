# -*- coding:utf-8 -*-


class RESCODE:
    OK = "200"
    EXTRACTING = "101"
    EXTRACTING_OK = "201"
    EXTRACTING_ERROR = "401"
    RECOMMENDING = "102"
    RECOMMENDING_OK = "202"
    RECOMMENDING_ERROR = "402"
    ERR = "400"
    PARAMERR = "403"
    TYPEERR = "404"
    DBERR = "405"
    UPLOAD_OK = "203"
    UPLOAD_ENCODE_ERROR = "406"
    UPLOAD_ERROR = "407"
    FULL_TEXT_INDEX_OK = "208"
    FULL_TEXT_INDEX_ERROR = "408"
    EXECUTE_INDEX_OK = '209'
    EXECUTE_INDEX_ERROR = '409'
    WAITING = "1000"


error_map = {
    RESCODE.OK: "成功",
    RESCODE.EXTRACTING: "要素提取中",
    RESCODE.EXTRACTING_OK: "要素提取成功",
    RESCODE.EXTRACTING_ERROR: "要素提取失败",
    RESCODE.RECOMMENDING: "类案推荐中",
    RESCODE.RECOMMENDING_OK: "类案推荐成功",
    RESCODE.RECOMMENDING_ERROR: "类案推荐失败",
    RESCODE.ERR: "失败",
    RESCODE.PARAMERR: "参数不足",
    RESCODE.TYPEERR: "数据类型错误",
    RESCODE.DBERR: "数据库查询失败",
    RESCODE.UPLOAD_OK: "上传成功",
    RESCODE.UPLOAD_ENCODE_ERROR: "上传文件编码错误",
    RESCODE.UPLOAD_ERROR: "上传失败",
    RESCODE.FULL_TEXT_INDEX_OK: "全文检索成功",
    RESCODE.FULL_TEXT_INDEX_ERROR: "全文检索失败",
    RESCODE.EXECUTE_INDEX_OK: "精确检索成功",
    RESCODE.EXECUTE_INDEX_ERROR: "精确检索失败",
    RESCODE.WAITING: "后台处理中",

}

