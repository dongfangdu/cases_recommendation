import logging
import os
from app.libs.common import get_project_dir


class Config:

    HOST = "192.168.108.197"
    PORT = 5894

    SAVE_NEW_DOC = True #是否保存上传文档
    MODEL_PAGE_MAX_DOCS = 50 #模型页面篇数
    NEW_PAGE_MAX_DOCS = 10 #上传文档页面篇数
    UPLOADS_FILE_SIZE = 1024*1024 #上传文件大小限制
    JSON_AS_ASCII = False

    # 日志配置
    LOGGING_CONFIG_PATH = './logging.yaml'

    # 上次文件路径
    UPLOADS_DEFAULT_DEST = os.path.join(get_project_dir(), "../upload_doc")


class DevelopmentConfig(Config):
    """ 用于开发模式的配置信息 """
    # 开启调试模式
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    """ 用于生产模式的配置信息 """
    LOG_LEVEL = logging.WARNING


config_dict = {
    'develop': DevelopmentConfig,
    'product': ProductionConfig,
}
