
import os
import redis
import pickle as pkl


class RedisHandler:
    __REDIS_HOSTNAME=os.environ.get("REDIS_HOSTNAME")
    __REDIS_HOSTPORT=os.environ.get("REDIS_HOSTPORT")
    def __init__(self, host="localhost", port=6379, db=0):
        host= self.__REDIS_HOSTNAME if self.__REDIS_HOSTNAME !=None else host
        port= int(self.__REDIS_HOSTPORT) if self.__REDIS_HOSTPORT !=None else port
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=False)

    def close_connection(self):
        """
        Close the Redis connection
        """
        self.redis.close()

    def set_value(self, key, value):
        self.redis.set(key, pkl.dumps(value))

    def get_value(self, key):
        return pkl.loads(self.redis.get(key))

    def set_dict(self, key, value: dict):
        self.redis.hset(key, mapping={k: pkl.dumps(v) for k, v in value.items()})

    def get_dict(self, key):
        raw = self.redis.hgetall(key)
        return {k.decode(): pkl.loads(v) for k, v in raw.items()}

    def push_to_list(self, key, value):
        self.redis.rpush(key, pkl.dumps(value))

    def read_from_list(self, key):
        raw = self.redis.lrange(key, 0, -1)
        return [pkl.loads(items) for items in raw]

    def pop_from_list(self, key):
        value = self.redis.lpop(key)
        return pkl.loads(value) if value else None

    def publish(self, channel, message):
        self.redis.publish(channel, pkl.dumps(message))

    def subscribe(self, channel):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def del_key(self, key):
        self.redis.delete(key)

    def clear(self):
        self.redis.flushdb()