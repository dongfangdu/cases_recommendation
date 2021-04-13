import os
import re
import json
from collections import defaultdict
from app.libs.es import rec_new_doc


def gen_inversed_idx(idx_dict):
    inv_idx = defaultdict(list)
    for k, v in idx_dict.items():
        inv_idx[v].append(k)
    return inv_idx


def align_paraSent(table, docId):
    for doc in table.find({'docId': docId}, no_cursor_timeout=True):
        paraSentIndex = []
        sentParaIndex = doc['sentParaIndex']
        inv_idx = gen_inversed_idx(sentParaIndex)

        for para, sents in inv_idx.items():
            paraSentIndex.append(sents)

        table.update_one({"docId": docId}, {"$set": {'paraSentIndex': paraSentIndex}})


def align_paraClause(table, docId):
    for doc in table.find({'docId': docId}, no_cursor_timeout=True):
        paraClauseIndex = []
        sentClauseIndex = []
        paraSentIndex = doc['paraSentIndex']
        clauseSentIndex = doc['clauseSentIndex']

        inv_idx  = gen_inversed_idx(clauseSentIndex)
        for sent, clauses in inv_idx.items():
            sentClauseIndex.append(clauses)

        for sentList in paraSentIndex:
            paraClause = []
            for clauseList in sentList:
                paraClause += sentClauseIndex[int(clauseList)]
            paraClauseIndex.append(paraClause)
        # print(docInfo.docId)
        # print(sentClauseIndex)
        # print(paraSentIndex)
        # print(paraClauseIndex)
        table.update_one({"docId": docId}, {"$set": {'paraClauseIndex': paraClauseIndex}})


if __name__ == '__main__':
    new_doc = rec_new_doc()
    align_paraSent(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9")
    align_paraClause(new_doc, "b892cfcea63d46c17e7aec48dbcbbed9")

