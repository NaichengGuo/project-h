import numpy as np
from collections import OrderedDict
import os
RANKS = '23456789TJQKA'
SUITS = 'SHDC'

CARD_STR_TO_UINT8 = {
    f"{s}{r}": i
    for i, (r, s) in enumerate((r, s) for r in RANKS for s in SUITS)
}
CARD_STR_TO_UINT8.update({k.lower(): v for k, v in CARD_STR_TO_UINT8.items()})

class WinRateProcessorNP_LRU:
    def __init__(self,board_file_path='./',max_cache_items=10000*10,use_lru=False):
        self.bytes_path_template = os.path.join(board_file_path,'rates/holdem/board_xxx/')
        arr = np.fromfile(os.path.join(board_file_path,'rates/holdem/board0/no-board-rates.bytes'), dtype='>u8')   # big-endian uint64
        arr = arr.byteswap().view(arr.dtype.newbyteorder())
        self.board0= arr
        #self.mask = np.uint64(~0x3FFFFF)
        self.mask = np.uint64(0xFFFFFFFFFFFFFFFF) ^ np.uint64(0x3FFFFF)
        self.board0_mask = arr & self.mask
        # LRU 缓存结构：key=(n_cards, hand_key)，val=(arr, masked_arr)
        self.cache = OrderedDict()
        self.max_cache_items = max_cache_items
        self.use_lru=use_lru

    def _make_cache_key(self, n_cards, hand_key):
        return (n_cards, hand_key)

    def _add_to_cache(self, key, value):
        """添加到 LRU 缓存，如果超过容量淘汰最旧的"""
        if key in self.cache:
            # 已存在则提到最前面
            self.cache.move_to_end(key, last=False)
            return

        # 新插入
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)

        # 超出容量限制 -> 淘汰末尾
        if len(self.cache) > self.max_cache_items:
            old_key, old_val = self.cache.popitem(last=True)
            # 帮助释放 numpy 数组内存
            del old_val

    def load_and_cache(self, n_cards, hand_key):
        if self.use_lru:
            key = self._make_cache_key(n_cards, hand_key)
            if key in self.cache:
                self.cache.move_to_end(key, last=False)  # 提到前面
                return self.cache[key]

        path_template = self.bytes_path_template.replace('_xxx', str(n_cards))
        file_path = os.path.join(path_template,f"{hand_key}.bytes")#f"{path_template}/{hand_key}.bytes"

        arr = np.fromfile(file_path, dtype='>u8')   # big-endian uint64
        arr = arr.byteswap().view(arr.dtype.newbyteorder())
        masked_arr = arr & self.mask
        if self.use_lru:
            self._add_to_cache(key, (arr, masked_arr))
        return arr, masked_arr

    @staticmethod
    def cardstrs_to_uint8s(cards):
        return np.array([CARD_STR_TO_UINT8[c] for c in cards], dtype=np.uint8)

    def encode_cards(self, cards_uint8):
        encoded = np.uint64(0)
        for i, c in enumerate(cards_uint8):
            encoded |= np.uint64(int(c)) << np.uint64(58 - 6 * i)
        return encoded

    @staticmethod
    def decode_uint64(val, num_cards):
        val = int(val)  # 转 Python int
        cards = [(val >> (58 - 6 * i)) & 0x3F for i in range(num_cards)]
        rate = (val & 0x3FFFFF) / 1_000_000
        return cards, rate

    def binary_search(self, arr, masked_arr, target_cards_uint8):
        target = self.encode_cards(target_cards_uint8)
        target_masked = target & self.mask
        idx = np.searchsorted(masked_arr, target_masked, side='left')
        if idx < len(arr) and (arr[idx] & self.mask) == target_masked:
            return self.decode_uint64(arr[idx], len(target_cards_uint8))
        return None, 0.0

    def get_winrate(self, hand_input, board_input):
        n_cards = len(board_input)
        assert n_cards in (0, 3, 4, 5)
        if n_cards in (3,4,5):
            hand_sorted = sorted(hand_input, key=lambda c: CARD_STR_TO_UINT8[c])
            hand_key_cards = [c[1] + c[0].lower() for c in hand_sorted]
            hand_key = ' '.join(hand_key_cards)
            arr, masked_arr = self.load_and_cache(n_cards, hand_key)
            board_uint8 = self.cardstrs_to_uint8s(sorted(board_input, key=lambda c: CARD_STR_TO_UINT8[c]))
        else: #n_cards==0
            arr=self.board0
            masked_arr=self.board0_mask
            hand_sorted = sorted(hand_input, key=lambda c: CARD_STR_TO_UINT8[c])
            hand_key_cards = [c[1] + c[0].lower() for c in hand_sorted]
            hand_key = ' '.join(hand_key_cards)
            board_uint8 = self.cardstrs_to_uint8s(sorted(hand_input, key=lambda c: CARD_STR_TO_UINT8[c]))
        _, rate = self.binary_search(arr, masked_arr, board_uint8)
        return rate