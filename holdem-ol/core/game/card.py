class CardCode(object):
    card_str_encodings = {
        "SA": 0, "S2": 1, "S3": 2, "S4": 3, "S5": 4, "S6": 5, "S7": 6,
        "S8": 7, "S9": 8, "ST": 9, "SJ": 10, "SQ": 11, "SK": 12,

        "HA": 13, "H2": 14, "H3": 15, "H4": 16, "H5": 17, "H6": 18, "H7": 19,
        "H8": 20, "H9": 21, "HT": 22, "HJ": 23, "HQ": 24, "HK": 25,

        "DA": 26, "D2": 27, "D3": 28, "D4": 29, "D5": 30, "D6": 31, "D7": 32,
        "D8": 33, "D9": 34, "DT": 35, "DJ": 36, "DQ": 37, "DK": 38,

        "CA": 39, "C2": 40, "C3": 41, "C4": 42, "C5": 43, "C6": 44, "C7": 45,
        "C8": 46, "C9": 47, "CT": 48, "CJ": 49, "CQ": 50, "CK": 51,
    }

    card_num_encodings = {0: 'SA', 1: 'S2', 2: 'S3', 3: 'S4', 4: 'S5', 5: 'S6', 6: 'S7', 7: 'S8', 8: 'S9', 9: 'ST',
                          10: 'SJ', 11: 'SQ', 12: 'SK', 13: 'HA', 14: 'H2', 15: 'H3', 16: 'H4', 17: 'H5', 18: 'H6',
                          19: 'H7', 20: 'H8', 21: 'H9', 22: 'HT', 23: 'HJ', 24: 'HQ', 25: 'HK', 26: 'DA', 27: 'D2',
                          28: 'D3', 29: 'D4', 30: 'D5', 31: 'D6', 32: 'D7', 33: 'D8', 34: 'D9', 35: 'DT', 36: 'DJ',
                          37: 'DQ', 38: 'DK', 39: 'CA', 40: 'C2', 41: 'C3', 42: 'C4', 43: 'C5', 44: 'C6', 45: 'C7',
                          46: 'C8', 47: 'C9', 48: 'CT', 49: 'CJ', 50: 'CQ', 51: 'CK'}

    rl_map_cmm = {'SA': 'As', 'S2': '2s', 'S3': '3s', 'S4': '4s', 'S5': '5s', 'S6': '6s', 'S7': '7s', 'S8': '8s', 'S9': '9s', 'ST': 'Ts', 'SJ': 'Js', 'SQ': 'Qs', 'SK': 'Ks', 'HA': 'Ah', 'H2': '2h', 'H3': '3h', 'H4': '4h', 'H5': '5h', 'H6': '6h', 'H7': '7h', 'H8': '8h', 'H9': '9h', 'HT': 'Th', 'HJ': 'Jh', 'HQ': 'Qh', 'HK': 'Kh', 'DA': 'Ad', 'D2': '2d', 'D3': '3d', 'D4': '4d', 'D5': '5d', 'D6': '6d', 'D7': '7d', 'D8': '8d', 'D9': '9d', 'DT': 'Td', 'DJ': 'Jd', 'DQ': 'Qd', 'DK': 'Kd', 'CA': 'Ac', 'C2': '2c', 'C3': '3c', 'C4': '4c', 'C5': '5c', 'C6': '6c', 'C7': '7c', 'C8': '8c', 'C9': '9c', 'CT': 'Tc', 'CJ': 'Jc', 'CQ': 'Qc', 'CK': 'Kc'}
    cmm_map_rl = {'As': 'SA', '2s': 'S2', '3s': 'S3', '4s': 'S4', '5s': 'S5', '6s': 'S6', '7s': 'S7', '8s': 'S8', '9s': 'S9', 'Ts': 'ST', 'Js': 'SJ', 'Qs': 'SQ', 'Ks': 'SK', 'Ah': 'HA', '2h': 'H2', '3h': 'H3', '4h': 'H4', '5h': 'H5', '6h': 'H6', '7h': 'H7', '8h': 'H8', '9h': 'H9', 'Th': 'HT', 'Jh': 'HJ', 'Qh': 'HQ', 'Kh': 'HK', 'Ad': 'DA', '2d': 'D2', '3d': 'D3', '4d': 'D4', '5d': 'D5', '6d': 'D6', '7d': 'D7', '8d': 'D8', '9d': 'D9', 'Td': 'DT', 'Jd': 'DJ', 'Qd': 'DQ', 'Kd': 'DK', 'Ac': 'CA', '2c': 'C2', '3c': 'C3', '4c': 'C4', '5c': 'C5', '6c': 'C6', '7c': 'C7', '8c': 'C8', '9c': 'C9', 'Tc': 'CT', 'Jc': 'CJ', 'Qc': 'CQ', 'Kc': 'CK'}
    all_card_strs = ['SA', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'ST', 'SJ', 'SQ', 'SK', 'HA', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'HT', 'HJ', 'HQ', 'HK', 'DA', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'DT', 'DJ', 'DQ', 'DK', 'CA', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'CT', 'CJ', 'CQ', 'CK']
    rl_suit = ['S', 'H', 'D', 'C']

    @staticmethod
    def cmm_to_rl_strs(cmm_cards):
        if len(cmm_cards) > 0 and CardCode.is_rl_card(cmm_cards[0]):
            return cmm_cards
        return [CardCode.cmm_map_rl[card] for card in cmm_cards]

    @staticmethod
    def rl_to_cmm_strs(rl_cards):
        return [CardCode.rl_map_cmm[card] for card in rl_cards]

    @staticmethod
    def to_values(cards):
        return [CardCode.card_str_encodings[card] for card in cards]

    @staticmethod
    def to_strs(values):
        return [CardCode.card_num_encodings[value] for value in values]

    @staticmethod
    def is_rl_card(card):
        return card[0] in CardCode.rl_suit


if __name__ == "__main__":
    a = CardCode()
    a.rl_suit = ["haha"]
    b = CardCode()
    b.rl_suit = ['h1']
    c = CardCode()

    print(a.rl_suit)
    print(b.rl_suit)
    print(c.rl_suit)
    print(CardCode.rl_suit)