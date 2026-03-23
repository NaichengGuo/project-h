import json
import requests

# 方式一：如果通过 API Gateway URL 调用
def call_via_api_gateway():
    url = "https://sptadsyzvugpstxq5t5mfc54yq0aifuh.lambda-url.ap-southeast-1.on.aws/"  # 替换为实际 URL
    
    # 构造业务数据 QueryData
    query_data = {
        "gameType": 450,
        "round": 1,
        "smallblind": 10,
        "szToken": "test_token_123",
        "users": [
            {"nPlayerId": 1001, "seat": 0, "score": 1000, "bRobot": 0}, # 0=真人
            {"nPlayerId": 1002, "seat": 1, "score": 1000, "bRobot": 1}  # 1=机器人
        ]
    }
    
    # 构造完整的请求 Body
    payload = {
        "Cmd": "QueryAISingleData",  # 必须是 QueryAISingleData 或 cacheService
        "QueryData": query_data
    }
    
    # 设置 Header
    # 注意：Lambda 代码 (L521-524) 强制要求 Content-Type 和 Content-Hmac
    headers = {
        "Content-Type": "application/json",
        "Content-Hmac": "dummy_signature"  # 代码仅检查 Key 是否存在，未校验具体签名值
    }
    
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(response.json())
call_via_api_gateway()