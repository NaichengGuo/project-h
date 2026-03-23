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

# ====== 游戏配置 ======
class GameConfig:
    # 牌局索引范围
    CARD_INDEX_LOWER = int(os.environ.get('CARD_INDEX_LOWER', 1))
    CARD_INDEX_UPPER = int(os.environ.get('CARD_INDEX_UPPER', 183840))
    
    # 允许干预的游戏类型
    ALLOWED_GAMETYPES = [450, 420]
    
    # 干预比例配置
    INTERVENTION_TEST_RATIO = float(os.environ.get('INTERVENTION_TEST_RATIO', 0.05)) # 积分干预比例
    SUSPECT_SUPPRESSION_RATIO = float(os.environ.get('SUSPECT_SUPPRESSION_RATIO', 0.05)) # 作弊打压比例
    
    # Redis 连接配置
    REDIS_CONNECT_TIMEOUT = 2
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_HEALTH_CHECK_INTERVAL = 30

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
            socket_connect_timeout=GameConfig.REDIS_CONNECT_TIMEOUT,
            socket_timeout=GameConfig.REDIS_SOCKET_TIMEOUT,
            retry_on_timeout=True,
            health_check_interval=GameConfig.REDIS_HEALTH_CHECK_INTERVAL,
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

def get_redis_card(key:str):
    r = get_redis_client()
    raw = r.get(key)
    #logger.info(f"test_raw:{raw}")
    return json.loads(raw)

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


def get_shuffled_deck(exclude_cards=None):
    """
    高效洗牌函数
    :param exclude_cards: 需要排除的牌列表
    :return: 洗好的牌堆
    """
    if exclude_cards:
        exclude_set = set(exclude_cards)
        deck = [c for c in ALL_CARDS if c not in exclude_set]
    else:
        deck = list(ALL_CARDS) # Copy
    
    random.shuffle(deck)
    return deck


# 干预发牌逻辑3：对积分最高的人发劣势牌，积分最低的人发优势牌，不考虑机器人与否
def intervention_score_rank (users, gametype, allowed_gametypes, random_number=1.0, test_ratio=1.0):
    if gametype not in allowed_gametypes or random_number > test_ratio :
        return False, None, None, {}

    # 在redis里找到历史积分
    redis_score_map=get_redis_score(users, gametype)
    logger.info(f"hist redis score map:{redis_score_map}")

    if not redis_score_map or len(redis_score_map) < 2:
        logger.warning("Not enough users for score-based intervention.")
        return False, None, None, redis_score_map
    
    scores = list(redis_score_map.values())
    user_ids = list(redis_score_map.keys())

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
                return False, None, None, redis_score_map

    logger.info(f"Score Map: {redis_score_map}, Highest: {adv_id}, Lowest: {disadv_id}")
    return True, adv_id, disadv_id, redis_score_map

# 干预发牌逻辑4：新用户奖励
# 逻辑：exists new_user:{}。若存在则该key则不奖励，不存在则奖励，奖励后set key
def intervention_new_user(users, gametype, allowed_gametypes):
    if gametype not in allowed_gametypes:
        return False, None, None

    r = get_redis_client()
    new_users = []
    all_pids = []

    for user in users:
        pid = user["nPlayerId"]
        all_pids.append(pid)
        key = f"new_user:{pid}"
        raw = r.get(key)
        if raw:
            try:
                val = float(raw)
            except Exception:
                val = 0.0
            if val > 0:
                new_users.append(pid)
            
    if not new_users:
        return False, None, None
        
    # Randomly pick one new user to reward
    target_new_user = random.choice(new_users)
    
    # Pick a disadvantage target
    possible_disadv_users = [p for p in all_pids if p != target_new_user]
    target_disadv_user = random.choice(possible_disadv_users) if possible_disadv_users else None

    try:
        key = f"new_user:{target_new_user}"
        raw = r.get(key)
        if raw:
            try:
                val = int(float(raw))
            except Exception:
                val = 0
            val -= 1
            if val > 0:
                r.set(key, val)
            else:
                r.delete(key)
        logger.info(f"New User Reward Triggered for {target_new_user}. Counter decremented.")
    except Exception as e:
        logger.error(f"Failed to update new_user key: {e}")

    # Return: True, Disadv=target_disadv_user, Adv=target_new_user
    return True, target_disadv_user, target_new_user

# 干预发牌逻辑5：作弊用户打压
# 逻辑：exists suspect_user:{} key，则随机进行打压
def intervention_suspect_user(users, gametype, allowed_gametypes, suppression_ratio):
    if gametype not in allowed_gametypes:
        return False, None, None
        
    r = get_redis_client()
    suspects = []
    non_suspects = []
    for user in users:
        pid = user["nPlayerId"]
        key = f"suspect_user:{pid}"
        raw = r.get(key)
        if raw:
            try:
                val = float(raw)
            except Exception:
                val = 0.0
            if val > 0:
                suspects.append(pid)
            else:
                non_suspects.append(pid)
        else:
            non_suspects.append(pid)
            
    if not suspects:
        return False, None, None
        
    # Only effective if not all are suspect users
    if not non_suspects:
        return False, None, None

    target_suspect = random.choice(suspects)
    
    target_non_suspect = random.choice(non_suspects)
    
    if random.random() > suppression_ratio:
        logger.info(f"Suspect {target_suspect} found but skipped due to ratio.")
        return False, None, None
         
    try:
        key = f"suspect_user:{target_suspect}"
        raw = r.get(key)
        if raw:
            try:
                val = int(float(raw))
            except Exception:
                val = 0
            val -= 1
            if val > 0:
                r.set(key, val)
            else:
                r.delete(key)
        logger.info(f"Suspect Suppression Triggered for {target_suspect}. Adv user: {target_non_suspect}, counter decremented.")
    except Exception as e:
        logger.error(f"Failed to update suspect_user key: {e}")

    # Return: True, Disadv=target_suspect, Adv=target_non_suspect
    return True, target_suspect, target_non_suspect


def assign_preset_cards(users, adv_card, dis_adv_card, cards, disadv_playerid, adv_playerid):
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
    
    users = input_data.get("users", [])
    random.shuffle(users)  
    gametype = input_data.get("gameType")
    
    # 干预配置
    allowed_gametypes = GameConfig.ALLOWED_GAMETYPES
    test_ratio = GameConfig.INTERVENTION_TEST_RATIO
    suspect_suppression_ratio = GameConfig.SUSPECT_SUPPRESSION_RATIO
    random_number = random.random()

    # 判断是否需要干预
    # Priority: Suspect > New User > Score
    # 1. Suspect User Intervention
    intervention_type = 0
    use_preset, disadv_playerid, adv_playerid = intervention_suspect_user(users, gametype, allowed_gametypes, suspect_suppression_ratio)
    if use_preset:
        intervention_type = 'suspect_user'

    cached_scores = {}
    
    if not use_preset:
        # 2. New User Intervention
        use_preset, disadv_playerid, adv_playerid = intervention_new_user(users, gametype, allowed_gametypes)
        if use_preset:
            intervention_type = 'new_user'

    if not use_preset:
        # 3. Score Rank Intervention (Existing)
        use_preset, disadv_playerid, adv_playerid, cached_scores = intervention_score_rank(users, gametype, allowed_gametypes, random_number, test_ratio)
        if use_preset:
            intervention_type = 'score_rank'

    logger.info(f"use_preset {use_preset}")
    
    if gametype==-1:
        use_preset=True
    
    hand_cards = []
    common_cards = []
    
    if use_preset:
        try:
            # 加载预设牌
            card_index = random.randint(GameConfig.CARD_INDEX_LOWER, GameConfig.CARD_INDEX_UPPER)
            redis_card_key = f"indexkey_{card_index}"
            logger.info(f"redis_card_key:{redis_card_key}")
            redis_card_val = get_redis_card(redis_card_key)
            adv_card = redis_card_val['my_card']
            dis_adv_card = redis_card_val['opponent_card']
            board_cards = redis_card_val['board_cards']

            # 优化洗牌逻辑：直接生成排除预设牌后的洗牌结果
            preset_cards = adv_card + dis_adv_card + board_cards
            cards = get_shuffled_deck(exclude_cards=preset_cards)
            
            # 分配预设牌
            hand_cards, index, assigned = assign_preset_cards(users, adv_card, dis_adv_card, cards, disadv_playerid, adv_playerid )
            common_cards = board_cards
            logger.info(f"Loaded preset cards: adv={adv_card}, disadv_playerid={disadv_playerid}, dis_adv={dis_adv_card},adv_playerid={adv_playerid},adv_card={adv_card}, board={board_cards}")
        except Exception as e:
            logger.error(f"Error in preset card distribution: {e}. Falling back to random.")
            use_preset = False
            intervention_type = 0
            # Fallback to random shuffle
            cards = get_shuffled_deck()
            hand_cards, index = assign_regular_cards(users, cards)
            common_cards = cards[index:index + 5]
    else:
        # 非干预：全部随机
        cards = get_shuffled_deck()
        hand_cards, index = assign_regular_cards(users, cards)
        common_cards = cards[index:index + 5]
    
    return {
        "bEffect": 1,
        "handCards": hand_cards,
        "commonCards": common_cards,
        "bPreset": use_preset,
        "inventionType": intervention_type,
        "redisScores": cached_scores
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
        # 尝试从 card_data 中获取缓存的积分
        cached_scores = card_data.get("redisScores")
        if cached_scores and len(cached_scores) > 0:
             history_score_map = cached_scores
        else:
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
