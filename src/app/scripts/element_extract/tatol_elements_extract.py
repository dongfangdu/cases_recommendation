from app.libs.es import rec_model_doc, rec_new_doc
from app.scripts.element_extract.label_db import data_clean
from app.scripts.element_extract.relaInfo_extract import ext_relainfo
from app.scripts.element_extract.classify_paragraph import classfy
from app.scripts.element_extract.litigant_detail import gen_lit_det
from app.scripts.element_extract.loan_element_extract import update_amount, update_delay_pay, update_mortgage_pledge, update_rate_insert
from app.scripts.element_extract.alignment import align_paraSent, align_paraClause


def tat_ele_ext(table, docId):
    data_clean(table, docId)
    align_paraSent(table, docId)
    align_paraClause(table, docId)
    ext_relainfo(table, docId)
    classfy(table, docId)
    gen_lit_det(table, docId)
    update_mortgage_pledge().main(table, docId, {'mortgage': '抵押', 'pledge': '质押'})
    update_amount().main(table, docId, {'appeal_amount': '诉请金额', 'affirm_amount': '认定金额', 'judge_amount': '判决金额'})
    update_rate_insert().main(table, docId, {'daily_rate': '日利率', 'monthly_rate': '月利率', 'annual_rate': '年利率'})
    update_delay_pay().main(table, docId, {'delay_pay': '滞纳金'})


def update_model_doc_elements():
    model_doc = rec_model_doc()
    loper = 0
    for info in model_doc.find({}, no_cursor_timeout=True):
        docId = info['docId']
        tat_ele_ext(model_doc, docId)
        loper += 1
        if loper % 1000 == 0:
            print(loper)


if __name__ == "__main__":
    # update_model_doc_elements()
    doc_id = "46e20c5d2b16163e2f9ace4102cbe931"
    new_doc = rec_new_doc()
    tat_ele_ext(new_doc, doc_id)