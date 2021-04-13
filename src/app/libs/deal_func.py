from NER_IDCNN_CRF.ner_api import NerApi
import re
from app.libs.common import get_config_dict

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


def db_conf(type='DATABASE_COMMON'):
    db_dict = get_config_dict()[type]
    db_config = {'host': db_dict["host"], 'port': int(db_dict["port"]), "db": db_dict["db"], "alias": "default"}
    return db_config


def get_lda_path(type='LDA_COMMON'):
    lda_path = get_config_dict()[type]
    return lda_path
