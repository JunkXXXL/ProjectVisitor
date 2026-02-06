from elasticsearch import Elasticsearch
import yaml
from datetime import datetime, timezone


class ElasticConnector:
    def __init__(self):
        with open("config.yml", 'r') as fl:
            config = yaml.safe_load(fl)
            hosts = r"http://" + config["BD"]["elastic"]["host"] + config["BD"]["elastic"]["port"]
            basic_auth = ['user', config["BD"]["elastic"]["password"]]
        self.es = Elasticsearch(hosts=[hosts], basic_auth=basic_auth)

    def _get_schema(self):
        return   {"content_ltks": "",
                  "content_sm_ltks": "",
                  "content_with_weight": "",
                  "create_time": datetime.now(tz=timezone.utc),
                  "doc_id": "",
                  "docnm_kwd": "",
                  "img_id": "",
                  "page_num_int": "",
                  "position_int": "",
                  "q_1536_vec": "",
                  "title_sm_tks": "",
                  "title_tks": "",
                  "top_int": "",
                  "kb_id": "",
                  "_index": "",
                  "_id": "",
                  "_ignored": "-",
                  "_score": 1}
