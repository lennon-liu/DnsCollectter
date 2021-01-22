import argparse
import datetime
import json
import os
from random import randint
from apscheduler.schedulers.background import BackgroundScheduler
import time
from apscheduler.jobstores.mongodb import MongoDBJobStore
from pymongo import MongoClient
from apscheduler.executors.pool import ThreadPoolExecutor
from DnsCollect.redis_tools.redisqueue import RedisQueue
from DnsCollect.scanner import MyScanner
from mongo_tools.conn import MongoManager

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    filename='Dns_schedule.log',
    filemode='w')


def new(conf):
    if type(conf) != type({}):
        return None
    ips = conf.get("ips", [])
    ports = conf.get("ports", [])
    rate = conf.get("rate", [])
    iface = conf.get("iface", "eth0")
    tmpexclude = conf.get("tmpexclude", [])
    source_port = conf.get("source_port", 0)
    es= conf.get("es", "")
    if not es :
        return None
    if type(ips) != type([]) or len(ips) < 1:
        return None
    if len(ports) < 1:
        ports = ["80", "81", "82", "83", "84", "88", "443", "444", "880", "1025", "1177", "1234", "1311", "1471",
                 "1991", "2080", "2082", "2083", "2086", "2087", "2375", "2376", "2480", "3000", "3128", "3541",
                 "3542", "3689", "3749", "3780", "4000", "4022", "4040", "4064", "4369", "4443", "4567", "4848",
                 "5357", "5560", "5678", "5985", "5986", "5986", "6664", "7071", "7288", "7474", "7547", "7548",
                 "7779", "8001", "8008", "8009", "8010", "8060", "8069", "8080", "8081", "8086", "8088", "8089",
                 "8090", "8098", "8100", "8112", "8139", "8161", "8200", "8334", "8377", "8378", "8443", "8800",
                 "8834", "8880", "8888", "8889", "9000", "9010", "9080", "9191", "9443", "9595", "9944", "9981",
                 "10001", "10243", "13579", "16010", "16992", "16993", "23424", "25105", "28017", "32400", "49152",
                 "49153", "50070", "51106", "55553"]
    if not rate:
        rate = 3000
    if not iface:
        iface = "eth0"
    if type(ips) != type([]) and len(tmpexclude) < 1:
        tmpexclude = []
    if not source_port or source_port == 0:
        source_port = 62000 + randint(0, 9)
    conf = {
        "ips": ips,
        "ports": ports,
        "tmpexclude": tmpexclude,
        "rate": rate,
        "iface": iface,
        "source_port": source_port,
        "es":es
    }
    myscan = MyScanner(conf)
    return myscan


def runjobs(taskid, host, port):
    client2 = MongoClient(host, port)
    mongomanager = MongoManager(client2)
    search = mongomanager.dbFindFirst({"_id": taskid})
    if not search:
        logging.info(taskid + "search conf failed")
        return
    try:
        logging.info(taskid+"search conf success")
        conf = search.get("conf", {})
        scan_conf= conf.get("scan_conf",{})
        taskname = conf.get("taskname", "")
        scan_conf["taskid"] = taskid
        scan_conf["taskname"] = taskname
        myjob = new(scan_conf)
        if not myjob:
            logging.info(taskid+"create job failed")
            return
        logging.info(taskid+"create job success")
        myjob.sscan()
        nowconf = search
        nowconf["last_time"] = time.time()
        nowconf["times"] = int(nowconf.get("times",0))+1
        nowconf["process"]=1
        if not mongomanager.update({"_id": taskid},nowconf):
            logging.info(taskid + "update task info failed")
            return
        logging.info(taskid + "update task info success")
    except:
        nowconf = search
        nowconf["last_time"] = time.time()
        nowconf["times"] = int(nowconf.get("times", 0)) + 1
        nowconf["process"] = -1
        mongomanager.update({"_id": taskid}, nowconf)


class Schedule():
    def __init__(self, host, port):
        self.host =host
        self.port = port
        self.client = MongoClient(self.host, self.port)
        self.sched = BackgroundScheduler()
        self.jobstore = MongoDBJobStore(collection='scanner', database='dns_scanner', client=self.client)
        self.sched.add_jobstore(self.jobstore)
        self.sched.add_executor(ThreadPoolExecutor(10))
        self.mongomanager = MongoManager(self.client)

        self.sched.start()
        self.joblist = []

        self.redisquere = RedisQueue("dns_scanner")
        logging.info("Schedule init success")
        print "init success"

    def rm_all_task(self):
        self.jobstore.remove_all_jobs()

    def rm_task(self, id):
        if id in self.joblist:
            self.jobstore.remove_job(id)

    def run(self):
        while True:
            try:
                cfgstr = self.redisquere.popmsg()
                if not cfgstr or not str(cfgstr).startswith("{"):
                    time.sleep(10)
                    continue
                logging.info(cfgstr)
                conf = json.loads(cfgstr)
                taskname = conf.get("taskname", "")
                taskid = conf.get("taskid", "")
                interval = conf.get("interval", {})
                seconds = interval.get("seconds", 0)
                minutes = interval.get("minutes", 0)
                hours = interval.get("hours", 0)
                days = interval.get("days", 0)
                weeks = interval.get("weeks", 0)

                if weeks + days + hours + hours + minutes + seconds < 1:
                    logging.error(taskname + "-->>interval error")
                    time.sleep(10)
                    continue
                logging.info(taskname + " add job")
                taskinfo = {
                    "taskname": taskname,
                    "_id": taskid,
                    "conf": conf,
                    "create_time": time.time(),
                    "times":0,
                    "process":0
                }
                if not self.mongomanager.insert(taskinfo):
                    logging.error(taskname + "-->>in mongo error")
                    time.sleep(10)
                    continue
                logging.info(taskname + "-->>in mongo success")
                job = self.sched.add_job(runjobs, "interval", seconds=seconds, minutes=minutes, hours=hours, days=days,
                                         weeks=weeks, next_run_time=datetime.datetime.now(),args=[taskid,self.host, self.port])
                self.joblist.append(job)
                time.sleep(70)
            except Exception, e:
                logging.error(str(e))


def start_schedule(host, port):
    s = Schedule(host=host, port=port)
    s.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--host")
    parser.add_argument("-p", "--port")
    argv = parser.parse_args()
    host = argv.host
    port = argv.port
    if not host or not port:
        os._exit(0)
    port = int(port)
    start_schedule(host=host, port=port)


if __name__ == "__main__":
    main()
