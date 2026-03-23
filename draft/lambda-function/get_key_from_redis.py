import json
import requests

# 模拟 API Gateway URL (替换为实际 URL)
API_URL = "https://sptadsyzvugpstxq5t5mfc54yq0aifuh.lambda-url.ap-southeast-1.on.aws/"

# 通用请求发送函数
def send_redis_request(action, key=None, value=None, ttl=None):
    # 构造 QueryData
    query_data = {
        "action": action
    }
    if key is not None:
        query_data["key"] = key
    if value is not None:
        query_data["value"] = value
    if ttl is not None:
        query_data["ttl"] = ttl

    # 构造完整 Body
    payload = {
        "Cmd": "cacheService",
        "QueryData": query_data
    }

    # 构造 Headers (Lambda 强制要求)
    headers = {
        "Content-Type": "application/json",
        "Content-Hmac": "test_signature"
    }

    print(f"\n--- Testing Action: {action} ---")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # 实际发送请求 (取消注释以运行)
    try:
        resp = requests.post(API_URL, json=payload, headers=headers)
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

# 2. GET: 获取缓存
send_redis_request(action="get", key="450_136565")