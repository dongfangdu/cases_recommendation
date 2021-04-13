# -*- coding:utf8 -*-

from flask import Flask
from flask_uploads import configure_uploads, patch_request_class
from flask_cors import CORS
from app.configure import config_dict
from app.libs.common import get_config_dict, get_project_dir, get_app_dir
from app.libs.deal_func import db_conf
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from app.model.base_db import db
from app.scripts.docs.upload_set import text
from app.configure import Config
import os
import yaml
import codecs
from flasgger import Swagger


def register_swagger(weba):
    # swagger配置拼装
    swagger_config = {
        "headers": [],
        "openapi": "3.0.2",
        "uiversion": 3,
        "components": {
            "securitySchemes": {"basicAuth": {"type": "http", "scheme": "basic"}},
        },
        "servers": [
            {
                "url": "https://192.168.100.210/api/v1",
                "description": "Production server (uses live data)",
            },
        ],
        "specs": [
            {
                "endpoint": "swagger",
                "route": "/swagger.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            },
        ],
        "title": "类案推送系统",
        "version": "0.1",
        "termsOfService": "",
        "static_url_path": "/characteristics/static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        "description": "类案推送系统HTTP协议的接口文档",
    }

    component_schemas_yml = os.path.join(get_app_dir(), "schemas.yml")
    # TODO 容易报错
    with codecs.open(component_schemas_yml, "r", encoding="utf-8") as f:
        component_schemas_dict = yaml.safe_load(f.read())
    swagger_config["components"]["schemas"] = component_schemas_dict

    swag = Swagger(config=swagger_config)
    swag.init_app(weba)


def create_log(app, logging_cfg):
    if logging_cfg:
        if logging_cfg[0] != '/':
            logging_cfg = os.path.abspath(os.path.join(get_project_dir(), logging_cfg))
    if not logging_cfg or not os.path.exists(logging_cfg):
        # raise IOError(u'日志配置文件不存在：{}'.format(logging_cfg_arg))
        logging_cfg = app.config['LOGGING_CONFIG_PATH']
        logging_cfg = os.path.abspath(os.path.join(app.root_path, '{}'.format(logging_cfg)))
    with codecs.open(logging_cfg, 'r', encoding='utf-8') as f:
        logging_cfg_dict = yaml.safe_load(f.read())
        handlers = logging_cfg_dict.get('handlers')
        if handlers:
            for handle_k, handler in handlers.items():
                if not handler.get('filename'):
                    continue
                log_filename = os.path.basename(handler['filename'])
                log_dir = os.path.dirname(handler['filename'])
                if log_dir[0] != '/':
                    log_dir = os.path.join(get_project_dir(), log_dir)
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                logging_cfg_dict['handlers'][handle_k]['filename'] = os.path.join(log_dir, log_filename)
        # print logging_cfg_dict
    logging.config.dictConfig(logging_cfg_dict)


def create_app(config_name, logging_cfg=None):
    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    create_log(app, logging_cfg)
    configure_uploads(app, text)
    uploads_file_size = Config.UPLOADS_FILE_SIZE
    patch_request_class(app, uploads_file_size)

    CORS(app, supports_credentials=True)

    db_config = db_conf()
    app.config['MONGODB_SETTINGS'] = db_config
    db.init_app(app)

    # 注册蓝图
    from app.api.docs import doc_bp
    app.register_blueprint(doc_bp)

    from app.api.recommend import rec
    app.register_blueprint(rec)

    from app.api.es import ind
    app.register_blueprint(ind)

    from app.api.elements_extract import ele_ext
    app.register_blueprint(ele_ext)

    register_swagger(app)
    return app
