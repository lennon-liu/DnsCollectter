import logging
import time

import redis


class RedisQueue():
    MAX_RETRIES = 5
    BATCH_SIZE = 1

    def __init__(self, queue):
        host = '127.0.0.1'
        port = 6379

        self.queue = queue
        try:
            self.redis = redis.Redis(host=host, port=port, db=0,
                                     socket_connect_timeout=10)
        except redis.ConnectionError as e:
            msg = "could not connect to redis: %s" % str(e)
            logging.error(msg)
            print(msg)
        # batching
        self.queued = 0
        self.retries = 0
        self.records = []

    def pushmsg(self, obj):
        try:
            p = self.redis.pipeline()
            p.rpush(self.queue, obj)
            p.execute()
        except redis.ConnectionError as e:
            msg = "redis connection error: %s" % str(e)
            print(msg)
            self.redis = None

    def popmsg(self):
        record = None
        try:
            record = self.redis.lpop(self.queue)
        except redis.ConnectionError as e:
            msg = "redis connection error: %s" % str(e)
            print(msg)
            self.redis = None
        return record

    def push(self, noretry=False):
        try:
            p = self.redis.pipeline()
            for r in self.records:
                p.rpush(self.queue, r)
            p.execute()
            self.queued = 0
            self.records = []
            self.retries = 0
        except redis.ConnectionError as e:
            time.sleep(1.0)
            self.retries += 1
            if self.retries > self.MAX_RETRIES or noretry:
                msg = "redis connection error: %s" % str(e)
                print(msg)
                self.redis = None

    def cleanup(self):
        return self.push(noretry=True)

    def take(self, obj):
        self.records.append(obj)
        self.push()


if __name__ == "__main__":
    RedisQueue("eee")
