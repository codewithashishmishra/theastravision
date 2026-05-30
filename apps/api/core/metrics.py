"""Request metrics aggregation in Redis (error rate, latency)."""

import json
from datetime import timedelta

import redis
from django.conf import settings
from django.utils import timezone


def _redis_client():
    url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
    return redis.from_url(url, decode_responses=True)


def _bucket_key(dt=None):
    dt = dt or timezone.now()
    return dt.strftime("platform:metrics:%Y%m%d%H%M")


def record_request(*, path, method, status_code, duration_ms):
    if not getattr(settings, "METRICS_ENABLED", True):
        return
    try:
        client = _redis_client()
        key = _bucket_key()
        pipe = client.pipeline()
        pipe.hincrby(key, "requests", 1)
        pipe.hincrbyfloat(key, "latency_sum", float(duration_ms))
        pipe.hincrby(key, "latency_count", 1)
        pipe.hincrby(key, f"status_{status_code}", 1)
        if status_code >= 400:
            pipe.hincrby(key, "errors", 1)
        ttl = int(getattr(settings, "METRICS_RETENTION_HOURS", 72)) * 3600
        pipe.expire(key, ttl)
        slow_key = "platform:metrics:slow_endpoints"
        pipe.zadd(slow_key, {f"{method}:{path}": duration_ms})
        pipe.zremrangebyrank(slow_key, 0, -51)
        pipe.expire(slow_key, ttl)
        pipe.execute()
    except redis.RedisError:
        pass


def _read_bucket(key):
    try:
        client = _redis_client()
        raw = client.hgetall(key)
    except redis.RedisError:
        return None
    if not raw:
        return None
    return {
        "requests": int(raw.get("requests", 0)),
        "errors": int(raw.get("errors", 0)),
        "latency_sum": float(raw.get("latency_sum", 0)),
        "latency_count": int(raw.get("latency_count", 0)),
        "by_status": {k.replace("status_", ""): int(v) for k, v in raw.items() if k.startswith("status_")},
    }


def _percentile(values, pct):
    if not values:
        return 0
    values = sorted(values)
    idx = int(len(values) * pct / 100)
    idx = min(idx, len(values) - 1)
    return round(values[idx], 2)


def get_summary_metrics(minutes=60):
    now = timezone.now()
    buckets = []
    latencies = []
    total_requests = 0
    total_errors = 0
    by_status = {}

    keys = [_bucket_key(now - timedelta(minutes=i)) for i in range(minutes)]
    try:
        client = _redis_client()
        pipe = client.pipeline()
        for key in keys:
            pipe.hgetall(key)
        raw_buckets = pipe.execute()
    except redis.RedisError:
        raw_buckets = [None] * len(keys)

    for i, bucket in enumerate(raw_buckets):
        if not bucket:
            continue
        dt = now - timedelta(minutes=i)
        bucket = {
            "requests": int(bucket.get("requests", 0)),
            "errors": int(bucket.get("errors", 0)),
            "latency_sum": float(bucket.get("latency_sum", 0)),
            "latency_count": int(bucket.get("latency_count", 0)),
            "by_status": {k.replace("status_", ""): int(v) for k, v in bucket.items() if k.startswith("status_")},
        }
        total_requests += bucket["requests"]
        total_errors += bucket["errors"]
        if bucket["latency_count"]:
            avg = bucket["latency_sum"] / bucket["latency_count"]
            latencies.extend([avg] * bucket["latency_count"])
        for code, count in bucket["by_status"].items():
            by_status[code] = by_status.get(code, 0) + count
        buckets.append(
            {
                "time": dt.isoformat(),
                "requests": bucket["requests"],
                "errors": bucket["errors"],
                "latency_avg": round(bucket["latency_sum"] / bucket["latency_count"], 2)
                if bucket["latency_count"]
                else 0,
            }
        )

    error_rate = round((total_errors / total_requests) * 100, 2) if total_requests else 0
    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate_percent": error_rate,
        "p50_latency_ms": _percentile(latencies, 50),
        "p95_latency_ms": _percentile(latencies, 95),
        "by_status": by_status,
        "timeseries": list(reversed(buckets)),
    }


def get_time_series(range_key="1h"):
    ranges = {"1h": 60, "24h": 24 * 60, "7d": 7 * 24 * 60}
    minutes = ranges.get(range_key, 60)
    step = 1 if minutes <= 120 else max(1, minutes // 120)
    now = timezone.now()
    series = []

    all_keys = []
    for i in range(0, minutes, step):
        dt = now - timedelta(minutes=i)
        for j in range(step):
            k = _bucket_key(dt - timedelta(minutes=j))
            all_keys.append(k)

    bucket_map = {}
    try:
        client = _redis_client()
        pipe = client.pipeline()
        for k in all_keys:
            pipe.hgetall(k)
        results = pipe.execute()
        for k, raw in zip(all_keys, results):
            if raw:
                bucket_map[k] = {
                    "requests": int(raw.get("requests", 0)),
                    "errors": int(raw.get("errors", 0)),
                    "latency_sum": float(raw.get("latency_sum", 0)),
                    "latency_count": int(raw.get("latency_count", 0)),
                }
    except redis.RedisError:
        pass

    for i in range(0, minutes, step):
        dt = now - timedelta(minutes=i)
        agg_requests = 0
        agg_errors = 0
        agg_latency_sum = 0.0
        agg_latency_count = 0
        for j in range(step):
            key = _bucket_key(dt - timedelta(minutes=j))
            bucket = bucket_map.get(key)
            if not bucket:
                continue
            agg_requests += bucket["requests"]
            agg_errors += bucket["errors"]
            agg_latency_sum += bucket["latency_sum"]
            agg_latency_count += bucket["latency_count"]
        series.append(
            {
                "time": dt.isoformat(),
                "requests": agg_requests,
                "errors": agg_errors,
                "error_rate": round((agg_errors / agg_requests) * 100, 2) if agg_requests else 0,
                "latency_avg": round(agg_latency_sum / agg_latency_count, 2) if agg_latency_count else 0,
            }
        )
    return list(reversed(series))


def get_slow_endpoints(limit=10):
    try:
        client = _redis_client()
        items = client.zrevrange("platform:metrics:slow_endpoints", 0, limit - 1, withscores=True)
        return [{"endpoint": k, "duration_ms": round(v, 2)} for k, v in items]
    except redis.RedisError:
        return []
