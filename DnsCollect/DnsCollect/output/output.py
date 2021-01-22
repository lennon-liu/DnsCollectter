import argparse
import hashlib
import json
import os
import sys
import time

from DnsCollect.classargs import subclass_of
from DnsCollect.es.elastic import Elastic
from DnsCollect.income import Incoming,InputFile
from DnsCollect.outcome import Outgoing,OutputFile

class DnsOutPut():
    def __init__(self,es_host,incoming,dindex):
        self.mappath = ["response","request","tls_log","handshake_log","server_certificates","certificate","parsed","extensions","subject_alt_name","dns_names"]
        self.es_host = es_host
        self.incoming = incoming
        self.index = dindex
        print "index: -->",self.index

    def assetPut(self):
        try:
            print "start out"
            self.es = Elastic(self.es_host)
            for line in self.incoming:
                if line[0] == "{":
                    self.take(line)
                else:
                    print "not match-->", line
        except Exception as e:
            print str(e)
            pass
        self.cleanup()

    def take(self, line):
        try:
            temp = json.loads(line)
            ip = temp.get("ip", "")
            o=temp.get("data", "")
            for key in self.mappath:
                o=o.get(key,{})
            if type(o) == type([]):
                domain = o
            else:
                domain = []
            for result in domain:
                data={
                    "ip":ip,
                    "value":ip,
                    "name":result,
                    "type":"a",
                    "user":"local"
                }
                doc = {"_type": "dns", "_index": self.index, "_source":data}
                self.es.take(doc)
        except Exception as e:
            print str(e)
            pass

    def cleanup(self):
        self.es.cleanup()


def tappscan_assetput():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--EsHost")
    parser.add_argument('-d', '--dindex')

    parser.add_argument('-i', '--input-file', default=sys.stdin,
                        type=argparse.FileType('rb'))
    parser.add_argument('-o', '--output-file', default=sys.stdout,
                        type=argparse.FileType('wb'))
    parser.add_argument('-O', '--outgoing', type=subclass_of(Outgoing),
                        default=OutputFile)
    parser.add_argument('-I', '--incoming', type=subclass_of(Incoming),
                        default=InputFile)

    arg = parser.parse_args()
    if not arg:
        os._exit(1)
    incoming = arg.incoming(arg.input_file)
    ap = DnsOutPut(arg.EsHost,incoming,arg.dindex)
    ap.assetPut()


if __name__ == "__main__":
    tappscan_assetput()
