import os, json, time, redis

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

def _key(ns, *parts): return f"ct:{ns}:" + ":".join(parts)

def get_json(ns, *parts):
    v = _redis.get(_key(ns, *parts))
    return json.loads(v) if v else None

def set_json(ns, value, ttl, *parts):
    _redis.setex(_key(ns, *parts), ttl, json.dumps(value))

def now_iso():
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"
