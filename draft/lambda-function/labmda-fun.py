import json
import base64
import hmac
import hashlib
import random
import redis
import time
import logging
import os
# 推荐使用 logging 模块（会自动包含时间戳、日志级别等）
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ====== Redis 配置 ======
REDIS_HOST = os.environ['REDIS_HOST']
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
SECRET_KEY = os.environ['SECRET_KEY'].encode()
CARD_INDEX_LOWER = 1
CARD_INDEX_UPPER = 31
ALL_CARDS = [
    0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,
    0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2A,0x2B,0x2C,0x2D,
    0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,
    0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,
]

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            socket_connect_timeout=2,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            ssl=True
        )
    return _redis_client

# --- Helper: Parse and validate QueryData once ---
def parse_query_data(body):
    input_data = body.get('QueryData')
    if input_data is None:
        raise ValueError("Missing 'QueryData' in request body")
    if isinstance(input_data, str):
        input_data = json.loads(input_data)  # Let it raise JSONDecodeError if invalid
    if not isinstance(input_data, dict):
        raise ValueError("QueryData must be an object (dict)")
    return input_data

def get_redis_card_combs(key:str):
    r = get_redis_client()
    raw = r.get(key)
    data = json.loads(raw)
    data = random.choice(data)
    return data

def get_user_score(keys):
    vals = []
    r = get_redis_client()
    for key in keys:
        val=r.get(key)
        if val:
            val=float(val)
        else:
            val=0.0
        vals.append(val)
    return vals


def get_redis_score(users, gametype):
    if not users:
        return {}

    # Build Redis keys using nPlayerId
    redis_key_list = [f'{gametype}_{u["nPlayerId"]}' for u in users]
    
    try:
        # Fetch scores in order (parallel or batched)
        raw_scores = get_user_score(redis_key_list)  # e.g., [1000.0, 0.0, 500.0]
    except Exception as e:
        logger.warning(f"Failed to fetch scores from Redis: {e}")
        raw_scores = [0.0] * len(users)

    # Zip nPlayerId with corresponding score
    score_map = {}
    for u, score in zip(users, raw_scores):
        score_map[u["nPlayerId"]] = float(score) if score is not None else 0.0

    return score_map

# determin card intervention
# 干预发牌逻辑1: 仅针对部分测试玩家生效 + 真人&机器人必须同时出现 + 真人差牌机器人好牌 + 测试比例可调
def intervention_target_id_test (users, gametype, target_player_ids, allowed_gametypes, random_number=1.0, test_ratio=0):
    if gametype not in allowed_gametypes or random_number > test_ratio: # 可改为 0.5 
        return False, 0

    user_player_ids = {u["nPlayerId"] for u in users}
    has_target = bool(user_player_ids & target_player_ids)
    has_human = any(u["bRobot"] == 0 for u in users)
    has_bot = any(u["bRobot"] == 1 for u in users)

    if has_target and has_human and has_bot:
        # logger.info(f"Intervention enabled: has_target={has_target}")
        return True, 1
    return False, 0


# 干预发牌逻辑2: 仅针对部分目标玩家生效(有无机器人都生效) + 目标玩家拿disadvcard + 测试比例可调
def intervention_target_id_punish (users, gametype, target_player_ids, allowed_gametypes, random_number=1.0, test_ratio=1.0):
    if gametype not in allowed_gametypes or random_number > test_ratio:
        return False, 0
    
    user_player_ids = {u["nPlayerId"] for u in users}
    has_target = bool(user_player_ids & target_player_ids)
    
    if has_target:
        # logger.info(f"Intervention enabled: has_target={has_target}")
        return True, 2
    return False, 0

# 干预发牌逻辑3：对积分最高的人发劣势牌，积分最低的人发优势牌，不考虑机器人与否
def intervention_score_rank (users, gametype, target_player_ids, allowed_gametypes, random_number=1.0, test_ratio=1.0):
    if gametype not in allowed_gametypes or random_number > test_ratio :
        return False, 0 , None, None
    
    # user_player_ids = {u["nPlayerId"] for u in users}
    # has_target = bool(user_player_ids & target_player_ids)
    # if not has_target:
    #     return False, 0, None, None

    # 在redis里找到历史积分
    redis_score_map=get_redis_score(users, gametype)

    if not redis_score_map or len(redis_score_map) < 2:
        logger.warning("Not enough users for score-based intervention.")
        return False, 0, None, None

    # 判断是否所有分数都相同
    if min(scores) == max(scores):
        # 所有分数相同：随机选择两个不同的用户
        adv_id, disadv_id = random.sample(user_ids, 2)
        logger.info(f"All scores equal ({scores[0]}). Randomly assigned: highest={adv_id}, lowest={disadv_id}")
    else:
        # 正常情况：按分数选最高和最低
        adv_id = max(redis_score_map, key=redis_score_map.get)
        disadv_id = min(redis_score_map, key=redis_score_map.get)
        # 防御性检查：理论上不会相等，但保险起见
        if adv_id == disadv_id:
            # 极端情况（如只剩1个有效用户），回退到随机选两个
            if len(user_ids) >= 2:
                adv_id, disadv_id = random.sample(user_ids, 2)
            else:
                return False, 0, None, None

    logger.info(f"Score Map: {redis_score_map}, Highest: {adv_id}, Lowest: {disadv_id}")
    return True, 3, adv_id, disadv_id

    # highest_user_id = max(redis_score_map, key=redis_score_map.get)
    # lowest_user_id = min(redis_score_map, key=redis_score_map.get)
    # logger.info(f"Score Map: {redis_score_map}, Highest: {highest_user_id}, Lowest: {lowest_user_id}")
    # return True, 3, highest_user_id, lowest_user_id

def assign_preset_cards(users,target_player_ids, adv_card, dis_adv_card, cards, disadv_playerid, adv_playerid):
    """
    分配预设牌，返回 (hand_cards, new_index, assigned_player_ids)
    """
    hand_cards = []
    assigned = set()
    index = 0

    # Step 1: 找目标玩家
    disadv_target_user = None
    adv_target_user = None
    for user in users:
        if user["nPlayerId"]==disadv_playerid:
            disadv_target_user = user
        if user["nPlayerId"]==adv_playerid:
            adv_target_user=user
        # break

    # Step2: 给disadv_playerid发 dis_adv_card
    if disadv_target_user and dis_adv_card:
        hand_cards.append({
            "seat": disadv_target_user["seat"],
            "cards": [dis_adv_card[0], dis_adv_card[1]],
            "nPlayerId": disadv_playerid,
            "presetType": 1 #劣势牌
        })
        assigned.add(disadv_target_user["nPlayerId"])
        dis_adv_card = []    

    # Step3: 给adv_playerid发 adv_card
    if adv_target_user and adv_card:
        hand_cards.append({
            "seat": adv_target_user["seat"],
            "cards": [adv_card[0], adv_card[1]],
            "nPlayerId": adv_playerid,
            "presetType": 2 #优势牌
        })
        assigned.add(adv_target_user["nPlayerId"])
        adv_card = []    

    # Step 4: 其他用户发普通牌
    for user in users:
        if user["nPlayerId"] not in assigned:
            card = [cards[index], cards[index + 1]]
            index += 2
            hand_cards.append({
                "seat": user["seat"],
                "cards": card,
                "nPlayerId": user["nPlayerId"],
                "presetType": 0 #无干预
            })
    
    return hand_cards, index, assigned

# def assign_preset_cards(users,target_player_ids, adv_card, dis_adv_card, cards):
#     """
#     分配预设牌，返回 (hand_cards, new_index, assigned_player_ids)
#     """
#     hand_cards = []
#     assigned = set()
#     index = 0
    
#     # Step 1: 找目标玩家（第一个匹配的）
#     target_user = None
#     for user in users:
#         if user["nPlayerId"] in target_player_ids:
#             target_user = user
#             break
    
#     # Step 2: 给目标玩家发 dis_adv_card
#     if target_user and dis_adv_card:
#         hand_cards.append({
#             "seat": target_user["seat"],
#             "cards": [dis_adv_card[0], dis_adv_card[1]],
#             "nPlayerId": target_user["nPlayerId"]
#         })
#         assigned.add(target_user["nPlayerId"])
#         dis_adv_card = []
    
#     # Step 3: 发 adv_card（优先机器人，其次其他真人）
#     if adv_card:
#         # 优先机器人
#         bot_candidates = [u for u in users if u["bRobot"] == 1 and u["nPlayerId"] not in assigned]
#         if bot_candidates:
#             chosen = random.choice(bot_candidates)
#         else:
#             # 兜底：其他真人
#             human_candidates = [u for u in users if u["bRobot"] == 0 and u["nPlayerId"] not in assigned]
#             chosen = random.choice(human_candidates) if human_candidates else None
        
#         if chosen:
#             hand_cards.append({
#                 "seat": chosen["seat"],
#                 "cards": [adv_card[0], adv_card[1]],
#                 "nPlayerId": chosen["nPlayerId"]
#             })
#             assigned.add(chosen["nPlayerId"])
#             adv_card = []
    
#     # Step 4: 其他用户发普通牌
#     for user in users:
#         if user["nPlayerId"] not in assigned:
#             card = [cards[index], cards[index + 1]]
#             index += 2
#             hand_cards.append({
#                 "seat": user["seat"],
#                 "cards": card,
#                 "nPlayerId": user["nPlayerId"]
#             })
    
#     return hand_cards, index, assigned


def assign_regular_cards(users, cards):
    """分配普通牌"""
    hand_cards = []
    index = 0
    for user in users:
        card = [cards[index], cards[index + 1]]
        index += 2
        hand_cards.append({
            "seat": user["seat"],
            "cards": card,
            "nPlayerId": user["nPlayerId"]
        })
    return hand_cards, index


def deal_cards(input_data):
    logger.info(f"deal_cards-logging info {input_data}")
    
    # 初始化完整牌堆
    cards = ALL_CARDS[:]
    random.shuffle(cards)
    users = input_data.get("users", [])
    random.shuffle(users)  
    gametype = input_data.get("gameType")
    
    # 干预配置
    allowed_gametypes = [450]
    test_ratio = 0 #  0表示关闭 1表示全量
    target_player_ids = {144365,144891}
    random_number = random.random()

    # redis_key_list = [f'{gametype}_{u}' for u in users]
    # score_list = [0 for _ in users]
    # try:
    #     score_list = get_user_score(redis_key_list) #[1000,None,None]
    # except Exception as e:
    #     logger.warning(f"Failed to get score list: {e}")


    # 判断是否需要干预
    use_preset, invention_type, disadv_playerid, adv_playerid = intervention_score_rank(users, gametype, target_player_ids, allowed_gametypes, random_number, test_ratio)
    
    adv_card = []
    dis_adv_card = []
    board_cards = []
    
    if use_preset:
        # 加载预设牌
        card_index = random.randint(CARD_INDEX_LOWER, CARD_INDEX_UPPER)
        redis_card_key = f"indexkey_{card_index}"
        redis_card_val = get_redis_card_combs(redis_card_key)
        adv_card = redis_card_val['my_card']
        dis_adv_card = redis_card_val['opponent_card']
        board_cards = redis_card_val['board_cards']

        # 从牌堆中移除预设牌
        for card in adv_card + dis_adv_card + board_cards:
            if card in cards:
                cards.remove(card)
        # 分配预设牌
        hand_cards, index, assigned = assign_preset_cards(users,target_player_ids, adv_card, dis_adv_card, cards, disadv_playerid, adv_playerid )
        common_cards = board_cards
        logger.info(f"Loaded preset cards: adv={adv_card}, disadv_playerid={disadv_playerid}, dis_adv={dis_adv_card},adv_playerid={adv_playerid},adv_card={adv_card}, board={board_cards}")
    else:
        # 非干预：全部随机
        hand_cards, index = assign_regular_cards(users, cards)
        common_cards = cards[index:index + 5]
    
    return {
        "bEffect": 1,
        "handCards": hand_cards,
        "commonCards": common_cards,
        "bPreset": use_preset,
        "inventionType": invention_type
    }

# --- Encode result with HMAC ---
def encode_result(data):
    data_string = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    hmac_digest = hmac.new(
        key=SECRET_KEY,
        msg=data_string.encode('utf-8'),
        digestmod=hashlib.sha1
    ).digest()
    dig64 = base64.b64encode(hmac_digest).decode('utf-8')
    return data_string, dig64

def flatten_game_data(input_data, card_data):
    common_cards = card_data.get("commonCards", [])
    hand_cards_map = {
        hc["nPlayerId"]: hc["cards"] 
        for hc in card_data.get("handCards", [])
    }
    preset_type_map = {
        hc["nPlayerId"]: hc.get("presetType")
        for hc in card_data.get("handCards", [])
    }

    b_preset = card_data.get("bPreset", False)
    invention_type = card_data.get("inventionType", 0)

    gametype = input_data.get("gameType")
    users = input_data.get("users", [])

     # 获取redis积分
    history_score_map = {}
    if gametype is not None and users:
        try:
            history_score_map = get_redis_score(users, gametype)
        except Exception as e:
            logger.warning(f"Failed to fetch history scores in flatten_game_data: {e}")
            history_score_map = {u["nPlayerId"]: 0.0 for u in users}

    result = []
    for user in input_data.get("users", []):
        nPlayerId = user["nPlayerId"]
        row = {
            "szToken": input_data["szToken"],
            "nround": input_data["round"],
            "gametype": input_data["gameType"],
            "smallblind": input_data["smallblind"],
            "nplayerid": nPlayerId,
            "seat": user["seat"],
            "score": user["score"],
            "brobot": user["bRobot"],
            "cards": hand_cards_map.get(nPlayerId, []),
            "commoncards": common_cards,
            "bPreset": b_preset,
            "inventionType":invention_type,
            "presetType": preset_type_map.get(nPlayerId),
            "redisScore": history_score_map.get(nPlayerId, 0.0)
        }
        result.append(row)
    return result

# --- Shuffle logic ---

def get_shuffle_result(body):
    input_data = parse_query_data(body)
    card_data = deal_cards(input_data)
    res={
        "Res": 1,
        "ResData": card_data,
        "Msg": "Success"
    }
    logger.info(f"output-res-info {res}")
    
     # output data processing
    try:
        flattened_rows = flatten_game_data(input_data, card_data)
        for row in flattened_rows:
            logger.info(f"FLATTENED_GAME_DATA: {json.dumps(row, separators=(',', ':'))}")
    except Exception as e:
        logger.warning(f"Failed to flatten game data: {e}")
    return res

# --- Cache service logic (minimal try/except) ---
def cache_service_logic(body):
    r = get_redis_client()
    input_data = parse_query_data(body)

    if 'action' not in input_data or 'key' not in input_data:
        raise ValueError("cacheService must contain 'action' and 'key'")

    action = input_data['action']
    key = str(input_data['key'])
    value = input_data.get('value')
    ttl = input_data.get('ttl', 0)

    if action == 'set':
        if ttl and ttl > 0:
            r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        else:
            r.set(key, json.dumps(value, ensure_ascii=False))
        return {"Res": 1, "ResData": f"Key '{key}' set successfully", "Msg": "Success"}

    elif action == 'get':
        raw = r.get(key)
        if raw is None:
            return {"Res": 0, "ResData": None, "Msg": f"Key '{key}' not found or expired"}
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            data = raw.decode('utf-8') if isinstance(raw, bytes) else raw
        return {"Res": 1, "ResData": data, "Msg": "Success"}

    elif action == 'delete':
        count = r.delete(key)
        return {"Res": 1, "ResData": f"Deleted {count} key(s): {key}", "Msg": "Success"}

    elif action in ('exists', 'contains'):
        exists = r.exists(key)
        return {"Res": 1, "ResData": bool(exists), "Msg": "Success"}

    elif action == 'ttl':
        t = r.ttl(key)
        if t == -2:
            return {"Res": 0, "ResData": 0, "Msg": f"Key '{key}' does not exist"}
        elif t == -1:
            return {"Res": 1, "ResData": -1, "Msg": "Success"}
        else:
            return {"Res": 1, "ResData": t, "Msg": "Success"}

    elif action == 'expire':
        if ttl <= 0:
            raise ValueError("Expire action requires positive 'ttl'")
        success = r.expire(key, ttl)
        if success:
            return {"Res": 1, "ResData": f"Key '{key}' expiration updated", "Msg": "Success"}
        else:
            return {"Res": 0, "ResData": None, "Msg": f"Key '{key}' not found"}

    elif action == 'flushall':
        r.flushdb()
        return {"Res": 1, "ResData": "Cache flushed", "Msg": "Success"}

    elif action == 'len':
        try:
            info = r.info('keyspace')
            db_key = f"db{REDIS_DB}"
            keys_count = int(info[db_key].split(',')[0].split('=')[1]) if db_key in info else 0
        except Exception:
            keys_count = -1
        return {"Res": 1, "ResData": keys_count, "Msg": "Success"}

    elif action == 'stop':
        return {"Res": 1, "ResData": "Redis does not require manual stop", "Msg": "Success"}

    else:
        raise ValueError(f"Unsupported action: {action}")

# --- Main Lambda handler (single error boundary) ---
def lambda_handler(event, context):
    try:
        t1=time.time()
        headers = (event.get('headers') or {})
        headers_lower = {k.lower(): v for k, v in headers.items()}
        if 'content-type' not in headers_lower or headers_lower['content-type'].split(';')[0].strip() != 'application/json':
            raise ValueError("Content-Type must be application/json")
        if 'content-hmac' not in headers_lower:
            raise ValueError("Missing Content-Hmac header")

        body = json.loads(event['body']) if event.get('body') else {}

        if body.get('Cmd') == 'QueryAISingleData':
            res = get_shuffle_result(body)
        elif body.get('Cmd') == 'cacheService':
            res = cache_service_logic(body)
        else:
            raise ValueError("Invalid Cmd or missing QueryData")
        t2=time.time()
        res['Delta']=(t2-t1)
        output, dig64 = encode_result(res)
        return {
            'statusCode': 200,
            'body': output,
            'headers': {
                'Content-Type': 'application/json',
                'Content-Hmac': dig64
            }
        }

    except Exception as e:
        # Centralized error response
        error_msg = f"Error: {str(e)}"
        res = {"Res": 0, "ResData": {}, "Msg": error_msg}
        output, dig64 = encode_result(res)
        return {
            'statusCode': 400,
            'body': output,
            'headers': {
                'Content-Type': 'application/json',
                'Content-Hmac': dig64
            }
        }