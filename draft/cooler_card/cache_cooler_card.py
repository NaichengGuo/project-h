# %%
import pandas as pd

# %%
usecols = ['winner','opponent_1','opponent_2','community_cards','winner_card_type']
df_high = pd.read_csv('cooler_database_high.csv', usecols=usecols, dtype='string')

# %%
df_normal = pd.read_csv('cooler_database_normal.csv', usecols=usecols, dtype='string')

# %%
df=pd.concat([df_high,df_normal])


# %%
# df

# %%
# 方 梅 红 黑
arr=[
    0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,
    0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2A,0x2B,0x2C,0x2D,
    0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,
    0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,
]

# %%
# 定义点数映射（低4位）
rank_map = {
    0x1: 'A',
    0x2: '2',
    0x3: '3',
    0x4: '4',
    0x5: '5',
    0x6: '6',
    0x7: '7',
    0x8: '8',
    0x9: '9',
    0xA: 'T',   # 或用 '10'，但通常德州扑克等用 'T' 表示 10
    0xB: 'J',
    0xC: 'Q',
    0xD: 'K'
}

# 花色映射（高4位）
suit_map = {
    0x1: 'd',  # 方块 Diamonds
    0x2: 'c',  # 梅花 Clubs
    0x3: 'h',  # 红桃 Hearts
    0x4: 's'   # 黑桃 Spades
}

# 构建完整映射
ALL_CARDS_HEX = {
    0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,
    0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2A,0x2B,0x2C,0x2D,
    0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,
    0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4A,0x4B,0x4C,0x4D,
}

card_id_to_str = {}
str_to_card_id ={}
for card in ALL_CARDS_HEX:
    suit = (card >> 4) & 0xF   # 高4位
    rank = card & 0xF          # 低4位
    if suit in suit_map and rank in rank_map:
        card_str = rank_map[rank] + suit_map[suit]
        card_id_to_str[card] = card_str
        str_to_card_id[card_str] = card


# %%

# %%
def map_card_str_to_ids(card_str):
    parts = card_str.split(',')
    return ','.join(str(str_to_card_id[p]) for p in parts)


# %%

# %%


# %%
for col in ['winner', 'opponent_1', 'opponent_2', 'community_cards']:
    df[f'mapped_{col}'] = df[col].apply(map_card_str_to_ids)

# %%
df

# %%
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

API_URL = "https://sptadsyzvugpstxq5t5mfc54yq0aifuh.lambda-url.ap-southeast-1.on.aws/"

def send_redis_request(session, action, key=None, value=None, ttl=None, debug=False):
    query_data = {"action": action}
    if key is not None:
        query_data["key"] = key
    if value is not None:
        query_data["value"] = value
    if ttl is not None:
        query_data["ttl"] = ttl
    payload = {"Cmd": "cacheService", "QueryData": query_data}
    headers = {"Content-Type": "application/json", "Content-Hmac": "test_signature"}
    try:
        resp = session.post(API_URL, json=payload, headers=headers, timeout=10)
        if debug:
            print(f"Response: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Request failed: {e}")
        return False

# %%
def process_row(session, i, r):
    try:
        my_card = [int(x) for x in r['mapped_winner'].split(',')]
        opponent_card = [int(x) for x in r['mapped_opponent_1'].split(',')]
        opponent_card_1 = [int(x) for x in r['mapped_opponent_2'].split(',')]
        board_cards = [int(x) for x in r['mapped_community_cards'].split(',')]
    except Exception:
        return

    check_set = set(my_card) | set(opponent_card) | set(opponent_card_1) | set(board_cards)
    
    # Check if the combined set has 11 unique cards
    if len(check_set) != 11:
        print(f'indexkey_{i} len(check_set) != 11')
        return
        
    # Check if all cards are valid
    if not check_set.issubset(ALL_CARDS_HEX):
        return

    send_redis_request(session, action="set", key=f'indexkey_{i}', value=({
        'my_card': my_card,
        'opponent_card': opponent_card,
        'opponent_card_1': opponent_card_1,
        'board_cards': board_cards,
    }), ttl=-1)
    
    send_redis_request(session, action="set", key=f'indexkey_detail_{i}', value=({
        'my_card': my_card,
        'opponent_card': opponent_card,
        'opponent_card_1': opponent_card_1,
        'board_cards': board_cards,
        'my_card_org': r['winner'].split(','),
        'opponent_1_org': r['opponent_1'].split(','),
        'opponent_2_org': r['opponent_2'].split(','),
        'winner_card_type': r['winner_card_type'],
    }), ttl=-1)

# %%
with requests.Session() as session:
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = []
        for ind, row in df.iterrows():
            futures.append(ex.submit(process_row, session, ind, row))
        for _ in tqdm(as_completed(futures), total=len(futures)):
            pass

# %%
# send_redis_request(action="get", key=indexkey, value=json.dumps(dict_row), ttl=-1,debug=True)

# %%


# %%



