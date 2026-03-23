import argparse
import math
import os
import threading
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import requests


thread_local = threading.local()


def get_session(pool_maxsize: int) -> requests.Session:
    s = getattr(thread_local, "session", None)
    if s is None:
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_maxsize, pool_maxsize=pool_maxsize, max_retries=0
        )
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        thread_local.session = s
    return s


def build_payload(i: int, token: str):
    query_data = {
        "gameType": 450,
        "round": 1,
        "smallblind": 10,
        "szToken": token,
        "users": [
            {"nPlayerId": 1001 + (i % 1000000), "seat": 0, "score": 1000, "bRobot": 0},
            {"nPlayerId": 2001 + (i % 1000000), "seat": 1, "score": 1000, "bRobot": 1},
        ],
    }
    return {"Cmd": "QueryAISingleData", "QueryData": query_data}


def percentile(sorted_values, p: float):
    if not sorted_values:
        return None
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return d0 + d1


def request_once(
    i: int,
    url: str,
    headers: dict,
    timeout_s: float,
    pool_maxsize: int,
    token: str,
    success_key: str ,
    success_value: str ,
):
    session = get_session(pool_maxsize=pool_maxsize)
    payload = build_payload(i=i, token=token)
    t0 = time.perf_counter()
    try:
        r = session.post(url, json=payload, headers=headers, timeout=timeout_s)
        rt = time.perf_counter() - t0
        ok = r.status_code == 200
        err = None
        status = r.status_code

        if ok and success_key is not None:
            try:
                data = r.json()
                actual = data.get(success_key) if isinstance(data, dict) else None
                if success_value is None:
                    ok = bool(actual)
                else:
                    ok = str(actual) == success_value
                if not ok:
                    err = f"bad_{success_key}:{actual}"
            except Exception as e:
                ok = False
                err = f"json_error:{type(e).__name__}"
        elif not ok:
            err = f"status:{status}"

        return ok, rt, err, status
    except Exception as e:
        rt = time.perf_counter() - t0
        return False, rt, f"exception:{type(e).__name__}", None


def run_load_test(
    *,
    url: str,
    total_requests: int,
    concurrency: int,
    timeout_s: float,
    warmup: int,
    pool_maxsize: int,
    token: str,
    success_key: str ,
    success_value: str ,
):
    headers = {"Content-Type": "application/json", "Content-Hmac": "dummy_signature"}

    for i in range(max(0, warmup)):
        request_once(
            i=i,
            url=url,
            headers=headers,
            timeout_s=timeout_s,
            pool_maxsize=pool_maxsize,
            token=token,
            success_key=success_key,
            success_value=success_value,
        )

    latencies = []
    ok_count = 0
    err_counter = Counter()
    status_counter = Counter()

    started_at = time.perf_counter()
    in_flight = set()
    next_i = 0

    def submit(ex, i: int):
        return ex.submit(
            request_once,
            i,
            url,
            headers,
            timeout_s,
            pool_maxsize,
            token,
            success_key,
            success_value,
        )

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        while next_i < total_requests or in_flight:
            while next_i < total_requests and len(in_flight) < concurrency * 2:
                in_flight.add(submit(ex, next_i))
                next_i += 1

            done, in_flight = wait(in_flight, return_when=FIRST_COMPLETED)
            for fut in done:
                ok, rt, err, status = fut.result()
                latencies.append(rt)
                if ok:
                    ok_count += 1
                else:
                    if err:
                        err_counter[err] += 1
                if status is not None:
                    status_counter[status] += 1

    elapsed = time.perf_counter() - started_at
    latencies_sorted = sorted(latencies)
    total = len(latencies_sorted)
    fail = total - ok_count

    p50 = percentile(latencies_sorted, 50)
    p90 = percentile(latencies_sorted, 90)
    p99 = percentile(latencies_sorted, 99)

    return {
        "url": url,
        "total": total,
        "ok": ok_count,
        "fail": fail,
        "elapsed_s": elapsed,
        "rps": (total / elapsed) if elapsed > 0 else None,
        "latency_s": {
            "p50": p50,
            "p90": p90,
            "p99": p99,
        },
        "status": dict(status_counter),
        "top_errors": err_counter.most_common(10),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--url",
        default=os.environ.get(
            "LOADTEST_URL",
            "https://sptadsyzvugpstxq5t5mfc54yq0aifuh.lambda-url.ap-southeast-1.on.aws/",
        ),
    )
    p.add_argument("--total", type=int, default=int(os.environ.get("LOADTEST_TOTAL", "50000")))
    p.add_argument(
        "--concurrency",
        type=int,
        default=int(os.environ.get("LOADTEST_CONCURRENCY", "20")),
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("LOADTEST_TIMEOUT", "3.0")),
    )
    p.add_argument("--warmup", type=int, default=int(os.environ.get("LOADTEST_WARMUP", "20")))
    p.add_argument(
        "--pool",
        type=int,
        default=int(os.environ.get("LOADTEST_POOL", "256")),
    )
    p.add_argument(
        "--token",
        default=os.environ.get("LOADTEST_TOKEN", "test_token_123"),
    )
    p.add_argument(
        "--success-key",
        default=os.environ.get("LOADTEST_SUCCESS_KEY", "Res"),
    )
    p.add_argument(
        "--success-value",
        default=os.environ.get("LOADTEST_SUCCESS_VALUE", "1"),
    )
    args = p.parse_args()

    success_key = args.success_key if args.success_key else None
    success_value = args.success_value if args.success_value else None

    result = run_load_test(
        url=args.url,
        total_requests=args.total,
        concurrency=args.concurrency,
        timeout_s=args.timeout,
        warmup=args.warmup,
        pool_maxsize=args.pool,
        token=args.token,
        success_key=success_key,
        success_value=success_value,
    )

    print("URL:", result["url"])
    print("Total:", result["total"], "OK:", result["ok"], "Fail:", result["fail"])
    print(
        "Elapsed(s):",
        round(result["elapsed_s"], 3),
        "RPS:",
        round(result["rps"], 2) if result["rps"] is not None else None,
    )
    print(
        "Latency(s) p50/p90/p99:",
        round(result["latency_s"]["p50"], 4) if result["latency_s"]["p50"] else None,
        round(result["latency_s"]["p90"], 4) if result["latency_s"]["p90"] else None,
        round(result["latency_s"]["p99"], 4) if result["latency_s"]["p99"] else None,
    )
    print("Status:", result["status"])
    print("Top errors:", result["top_errors"])


if __name__ == "__main__":
    main()

