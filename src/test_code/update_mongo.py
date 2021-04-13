import pymongo


client = pymongo.MongoClient("mongodb://192.168.106.170:27017/")
file_db = client["fileDB"]
rec_db = client["recommend"]

listRec = file_db["listRec"]
model_doc = rec_db["model_doc"]
result = rec_db["result"]
# model_doc.delete_many({"pledge": "无"})

# for info in model_doc.find({"docId": "fd693d87-ed64-4734-837f-1a944fea3479"}, {"docId": 1}):
#     docId = info['docId']
#     for doc_content in listRec.find({"docId": docId}, {"docContent": 1}):
#         docContent = doc_content['docContent']
#         model_doc.update_one({"docId": docId}, {"$set": {"docContent": docContent}})


# for info in model_doc.find({}, {"docId": 1}):
#     docId = info['docId']
#     # model_doc.update_one({"docId": docId}, {"$unset": {"mortgage": 1, "pledge": 1, "delay_pay": 1,
#     #                                                    "daily_rate": 1, "monthly_rate": 1, "annual_rate": 1,
#     #                                                     "appeal_amount": 1, "affirm_amount": 1, "judge_amount": 1}})
#     model_doc.update_one({"docId": docId}, {"$unset": {"appeal_amount": 1, "affirm_amount": 1, "judge_amount": 1}})


# result.remove({})
