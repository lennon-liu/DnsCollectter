import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class Elastic():
    def __init__(self,hosts):
        self.client = Elasticsearch(hosts, timeout=1000)
        self.records = []

    def push(self):
        if len(self.records) > 0:
            try:
                bulk(self.client, self.records)
            except Exception as e:
                logging.error(str(e))
                pass
            self.records = []

    def take(self, obj):
        self.records.append(obj)
        if len(self.records) >= 5:
            self.push()

    def cleanup(self):
        self.push()

    def delete(self, index):
        try:
            self.client.indices.delete(index)
        except Exception as e:
            logging.error(str(e))


if __name__ == "__main__":
    print "es tools"
