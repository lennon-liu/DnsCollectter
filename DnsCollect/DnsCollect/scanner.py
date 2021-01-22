import datetime
import json
import logging
import os
import subprocess
import time
import uuid

from iptools import netblock

class MyScanner():

    def __init__(self,cfg):
        self.cfg = cfg
        self.taskid = self.cfg.get("taskid","")
        self.taskname = self.cfg.get("taskname", "")
        self.ips = cfg.get("ips",[])
        self.es =  cfg.get("es","127.0.0.1")
        self.tmpip = "%s_ip.tmp" % (uuid.uuid4())
        self.ports = cfg.get("ports",["443","8443"])
        self.iface = cfg.get("iface","eth0")
        self.index = cfg.get("index","ip2domain")
        self.source_port = cfg.get("source_port",60000)
        self.tmpexclude = cfg.get("tmpexclude",[])
        self.tmpexcludefile = "%s_ex_ip.tmp" % (uuid.uuid4())
        self.rate = cfg.get("rate","3000")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S',
            filename='Dns_scanner.log',
              filemode='w')
        logging.info(str(self.taskid)+"scanner -->>init")

    def re_taskid(self):
        return str(self.taskid)

    def taskname(self):
        return self.taskname


    def call_subprocess(self, commands):
        # ls | grep t |grep e
        ps = []
        for i in range(len(commands)):
            subp = None
            if len(commands) == 1:
                subp = subprocess.Popen(commands[i])
            elif i == 0:
                subp = subprocess.Popen(commands[i], stdout=subprocess.PIPE)
            elif i == len(commands) - 1:
                subp = subprocess.Popen(commands[i], stdin=ps[-1].stdout)
            else:
                subp = subprocess.Popen(commands[i], stdin=ps[-1].stdout, stdout=subprocess.PIPE)
            if subp:
                ps.append(subp)
                logging.info(subp)
        for i in range(len(ps)):
            if (i != len(commands) - 1):
                logging.info(self.re_taskid()+"-->ps[%d].stdout.close()", i)
                ps[i].stdout.close()
        while True:
            cmp_task = []
            for i in range(len(ps)):
                if i in cmp_task:
                    continue
                status = ps[i].poll()
                if status != None:
                    try:
                        logging.info(self.re_taskid()+"-->running")
                        pass
                    except Exception as e:
                        logging.info(self.re_taskid()+"-->"+str(e))
                        pass
                    cmp_task.append(i)
            if len(cmp_task) == len(ps):
                logging.info(self.re_taskid()+"--> call success")
                break
            time.sleep(2)


    def parse_dnsanswer(self, line, outfp,ipranges):
        data = json.loads(line)
        iscname = False
        stat = data.get("status")
        domain = data.get("name")
        if stat == "NOERROR":
            for answer in data.get("data", {}).get("answers", []):
                if answer["type"] == "A":
                    outfp.write("%s,%s\n" % (answer["answer"], domain))
                    ipranges.addoddcidr(answer["answer"])
                    if iscname:
                        break
                elif answer["type"] == "CNAME" and domain == answer["name"]:
                    iscname = True


    def dns_parser(self, infile, outfp,ipranges):
        tmpoutput = "%s_output.tmp" % (uuid.uuid4())
        cmd = ["tdns", "a", "--timeout=25", "--threads=100", "--input-file=%s" % infile, "--output-file=%s" % tmpoutput]
        print cmd
        # do dns parser
        self.call_subprocess([cmd])
        # testing is a
        fdns = open(tmpoutput, "rb")
        for l in fdns:
            text = l.rstrip().lstrip()
            if text == "":
                continue
            else:
                self.parse_dnsanswer(text, outfp,ipranges)
        fdns.close()
        # delete temp file
        os.remove(tmpoutput)

    def sscan(self):
        logging.info(self.re_taskid()+"start")
        ipranges = netblock.IPRanges()
        ex_ipranges= netblock.IPRanges()
        for line in self.ips:
            try:
                ipranges.addoddcidr(line)
            except:
                pass
        for line in self.tmpexclude:
            line = line.strip(self.tmpexclude)
            try:
                ipranges.addoddcidr(line)
            except:
                pass
        with open(self.tmpip, "wb") as fip:
            for ips in ipranges.tocidr():
                fip.write("%s\n" % ips)

        with open(self.tmpexcludefile, "wb") as ex_fip:
            for ips in ex_ipranges.tocidr():
                ex_fip.write("%s\n" % ips)

        port = ",".join(self.ports)
        logging.info("port scanner start")
        command = ["masscan", "--excludefile=%s" % (self.tmpexcludefile),
                   "--source-port=%d"%self.source_port,
                   "-i", self.iface,
                   "--rate=%d" % self.rate,
                   "-p",
                   port,
                   "-iL", self.tmpip]
        dns_output = ["dns_output","-e",self.es,"-i", self.index]
        logging.info(str(self.taskid) + " ".join(command))
        logging.info(str(self.taskid) + " ".join(dns_output))
        self.call_subprocess([command, ["https_re"],dns_output])
        logging.info(self.re_taskid() + "success")




if __name__=="__main__":
    cfg = {
        "ips":["162.241.38.230/24"],
        "ports":["80","81","82","83","84","88","443","444","880","1025","1177","1234","1311","1471","1991","2080","2082","2083","2086","2087","2375","2376","2480","3000","3128","3541","3542","3689","3749","3780","4000","4022","4040","4064","4369","4443","4567","4848","5357","5560","5678","5985","5986","5986","6664","7071","7288","7474","7547","7548","7779","8001","8008","8009","8010","8060","8069","8080","8081","8086","8088","8089","8090","8098","8100","8112","8139","8161","8200","8334","8377","8378","8443","8800","8834","8880","8888","8889","9000","9010","9080","9191","9443","9595","9944","9981","10001","10243","13579","16010","16992","16993","23424","25105","28017","32400","49152","49153","50070","51106","55553"],
        "tmpexclude":[],
        "rate":3000,
        "iface":"ens33",
        "source_port":60000,
        "taskname": "xxxx",
        "taskid": str(uuid.uuid4()),
    }
    print time.time()
    myscanner=MyScanner(cfg)
    myscanner.sscan()
    print time.time()