# -*- coding:utf8 -*-

from app import create_app
from app.libs.common import get_config_dict
import json
from app.libs.es import es_conn

app = create_app("develop")

es_db = get_config_dict()["DATABASE_ES"]
index = es_db['index']
httpHeaders = {'Content-Type': 'application/json'}
conn = es_conn()


def mappings():
    data_dict = {
        "mappings": {
            "properties": {
                "docContent": {"type": "text"},
                "docId": {"type": "text"},
                "doc_name": {"type": "text"},
                "legalBase": {
                    "properties": {
                        "Items": {
                            "properties": {
                                "legalContent": {"type": "text"},
                                "legalName": {"type": "text"}
                                      }
                                },
                        "legalRuleName": {"type": "text"},
                            }
                        },
                "relaInfo_appellor": {"type": "text"},
                "relaInfo_caseType": {"type": "keyword"},
                "relaInfo_court": {"type": "keyword"},
                "relaInfo_docType": {"type": "keyword"},
                "relaInfo_processType": {"type": "keyword"},
                "relaInfo_reason": {"type": "keyword"},
                "relaInfo_trialDate": {"type": "date", "format": "yyyy-MM-dd"},
                "relaInfo_trialRound": {"type": "keyword"},
                "schema_version": {"type": "text"},
                "mortgage": {
                    "properties": {
                        "goods": {"type": "keyword"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                },
                "pledge": {
                    "properties": {
                        "goods": {"type": "keyword"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                },
                "delay_pay": {
                    "properties": {
                        "amount": {"type": "float"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                },
                "daily_rate": {
                    "properties": {
                        "rate": {"type": "text"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                },
                "monthly_rate": {
                    "properties": {
                        "rate": {"type": "text"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                },
                "annual_rate": {
                    "properties": {
                        "rate": {"type": "text"},
                        "info": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "text"},
                                "location": {
                                    "properties": {
                                        "clause_idx": {"type": "integer"},
                                        "start": {"type": "integer"},
                                        "end": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    body = json.dumps(data_dict)
    url = '/%s' % index
    conn.request(method='PUT', url=url, body=body, headers=httpHeaders)
    response = conn.getresponse()
    res = json.loads(response.read())
    print(res)


if __name__ == "__main__":
    mappings()
