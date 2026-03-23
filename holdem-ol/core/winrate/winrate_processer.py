import pickle
import os
from tqdm import tqdm
import bisect
import struct

RANKS = '23456789TJQKA'
SUITS = 'SHDC'
CARD_STR_TO_UINT8 = {f"{s}{r}": i for i, (r, s) in enumerate((r, s) for r in RANKS for s in SUITS)}
LOWER_CARD_STR_TO_UINT8 = {f"{r}{s.lower()}": i for i, (r, s) in enumerate((r, s) for r in RANKS for s in SUITS)}

class WinRateProcessor():
    def __init__(self):
        self.preflop_path = f"/Users/q/Downloads/rates/holdem/board0/no-board-rates.bytes"
        self.bytes_path_template= '/Users/q/Downloads/rates/holdem/board_xxx/'
        self.pkl_path_template='/Users/q/Downloads/workspace/board_xxx.pkl'
        self.board={}
        self.board[0]=self.init_board0()
        self.board[3]=self.init_board(3)
        self.board[4]=self.init_board(4)
        self.board[5]=self.init_board(5)

    def load_bytes_file(self,filepath):
        arr = []
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(8)
                if not chunk or len(chunk) < 8:
                    break
                val = struct.unpack(">Q", chunk)[0]
                arr.append(val)
        return arr

    def init_board0(self,n_board=0):
        file_path = self.preflop_path
        arr=self.load_bytes_file(file_path)
        pkl_path=self.pkl_path_template.replace('_xxx',str(n_board))
        with open(pkl_path, 'wb') as file:
            pickle.dump(arr, file, protocol=pickle.HIGHEST_PROTOCOL)  # Use the highest available protocol
        return arr

    def read_borad_from_bytes(self,n_board):
        memo={}
        path_template=self.bytes_path_template.replace('_xxx',str(n_board))
        for root, dirs, files in tqdm(os.walk(path_template)):
            for file in tqdm(files):
                # 获取文件的绝对路径
                file_path = os.path.join(root, file)
                hold_card_array=sorted(file[:5].replace(' ',',').split(','),key=lambda card: LOWER_CARD_STR_TO_UINT8[card])#获取手牌
                file_path = f"/Users/q/Downloads/rates/holdem/board{n_board}/{' '.join(hold_card_array)}.bytes"
                memo[','.join(hold_card_array)]=self.load_bytes_file(file_path)
        with open(f'board{n_board}.pkl', 'wb') as file:
            pickle.dump(memo, file, protocol=pickle.HIGHEST_PROTOCOL)  # Use the highest available protocol

    def cardstrs_to_uint8s(self,cardstrs):
    # 输入如 ['2c', '3c']，返回 [uint8, uint8]
        return [CARD_STR_TO_UINT8[c] for c in cardstrs]

    def init_board(self,n_board):
        memo={}
        pkl_path=self.pkl_path_template.replace('_xxx',str(n_board))
        if os.path.exists(pkl_path):
              with open(pkl_path, 'rb') as file:  # 打开文件，模式为二进制读取 ('rb')
                memo=pickle.load(file)
        else:
            self.read_borad_from_bytes(n_board)
            print("load board from bytes...")
        return memo

    def binary_search(self,arr, target_cards):
        target = self.encode_cards(target_cards)
        mask = ~0x3FFFFF
        target_masked = target & mask
        # 创建一个用于比较的masked数组
        masked_arr = [num & mask for num in arr]
        # 使用bisect查找位置
        index = bisect.bisect_left(masked_arr, target_masked)
        if index < len(arr) and (arr[index] & mask) == target_masked:
            return self.decode_uint64(arr[index], len(target_cards))
        return None, 0.0

    def binary_search(self,arr, target_cards):
        target = self.encode_cards(target_cards)
        mask = ~0x3FFFFF
        target_masked = target & mask
        # 创建一个用于比较的masked数组
        #print(type(arr))
        masked_arr = [num & mask for num in arr]
        # 使用bisect查找位置
        index = bisect.bisect_left(masked_arr, target_masked)
        if index < len(arr) and (arr[index] & mask) == target_masked:
            return self.decode_uint64(arr[index], len(target_cards))
        return None, 0.0

    def encode_cards(self,cards):
        # Go: encoded |= uint64(c) << (58 - 6*i)
        encoded = 0
        for i, c in enumerate(cards):
            encoded |= int(c) << (58 - 6 * i)
        return encoded

    def decode_uint64(self,val, num_cards):
        cards = []
        for i in range(num_cards):
            c = (val >> (58 - 6 * i)) & 0x3F
            cards.append(c)
        rate = val & 0x3FFFFF
        return cards, rate / 1000000

    def calculate_heuristic_win_prob(self,cards):
        hand_input, board_input = cards[:2], cards[2:]
        hand_input=sorted(hand_input,key=lambda card: CARD_STR_TO_UINT8[card])
        sorted_cards = sorted(board_input, key=lambda card: CARD_STR_TO_UINT8[card])
        n_card=len(board_input)
        if n_card in [3, 4, 5]:
            hand_input=[i[1]+i[0].lower() for i in hand_input]
            hand_input_str=','.join(hand_input)
            if n_card in [3,4,5]:
                path_template=self.bytes_path_template.replace('_xxx',str(n_card))
                file_path = f"{path_template}/{' '.join(hand_input)}.bytes"
                arr=self.load_bytes_file(file_path)
            else:
                arr = self.board[n_card][hand_input_str]
            find_cards = self.cardstrs_to_uint8s(sorted_cards)
        elif n_card == 0 : #preflop
            arr = self.board[n_card]
            find_cards = self.cardstrs_to_uint8s(hand_input)
        else:
            raise ValueError(f"illegal nums of card:{n_card}")
        cards, rate = self.binary_search(arr, find_cards)
        return rate