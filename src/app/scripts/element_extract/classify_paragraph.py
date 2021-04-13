import os
import re
import json
from pprint import pprint
from app.model.base_db import ModelDoc, NewDoc
from app.libs.es import rec_model_doc, rec_new_doc
from mongoengine import *
from app.scripts.element_extract.extract_elements import elefrom_para, extract_plaintiff, \
                                extract_defendant, extract_agent, extract_plaintiffClaim,\
                                extract_courtDeem, extract_courtFact, extract_defendantArgue, \
                                extract_courtJudgment


def classfy(table, docId):
    #################### all elements update
    elemParaIndex = {}
    cur = table.find({'docId': docId})
    # doc = NewDoc.objects(docId=docId).first()
    for doc in cur:
        if doc['schema_version'] != "2.0":
            trialRound = doc['relaInfo_docCont'][3]['value'][0]
            paraClauseIndex = doc['paraClauseIndex']
            clauseList = doc['clauseList']
            paraHeaderList = doc['paraHeaderList']

            elemParaIndex['plaintiff'] = extract_plaintiff(paraHeaderList)
            elemParaIndex['defendant'] = extract_defendant(paraHeaderList)
            elemParaIndex['agent'] = extract_agent(paraHeaderList)
            elemParaIndex['plaintiffClaim'] = extract_plaintiffClaim(paraClauseIndex, clauseList)
            elemParaIndex['defendantArgue'] = extract_defendantArgue(paraClauseIndex, clauseList)
            elemParaIndex['courtFact'] = extract_courtFact(paraClauseIndex, clauseList, trialRound)
            elemParaIndex['courtDeem'] = extract_courtDeem(paraClauseIndex, clauseList)
            elemParaIndex['courtJudgment'] = extract_courtJudgment(paraClauseIndex, clauseList, docId)
            # pprint(elemParaIndex)
            table.update_one({"docId": docId}, {"$set": {'elemParaIndex': elemParaIndex}})
        else:
            pass


if __name__ == '__main__':
    new_doc = rec_new_doc()
    classfy("b892cfcea63d46c17e7aec48dbcbbed9")


