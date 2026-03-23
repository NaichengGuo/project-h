import os
import grpc
import numpy as np

import core.winrate.winrate_pb2 as api_pb2
import core.winrate.winrate_pb2_grpc as api_pb2_grpc

from cachetools import LRUCache
from core.game.card import CardCode


class SrvCardV2(object):
    card_str_seqs = [
        "SA", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "ST", "SJ", "SQ", "SK",
        "HA", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "HT", "HJ", "HQ", "HK",
        "DA", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "DT", "DJ", "DQ", "DK",
        "CA", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "CT", "CJ", "CQ", "CK",
    ]
    card_str_values = CardCode.card_str_encodings

    srv_cards_str_seqs = [
        "S2", "H2", "D2", "C2",
        "S3", "H3", "D3", "C3",
        "S4", "H4", "D4", "C4",
        "S5", "H5", "D5", "C5",
        "S6", "H6", "D6", "C6",
        "S7", "H7", "D7", "C7",
        "S8", "H8", "D8", "C8",
        "S9", "H9", "D9", "C9",
        "ST", "HT", "DT", "CT",
        "SJ", "HJ", "DJ", "CJ",
        "SQ", "HQ", "DQ", "CQ",
        "SK", "HK", "DK", "CK",
        "SA", "HA", "DA", "CA",
    ]
    srv_cards_str_values = {
        "S2": 0, "H2": 1, "D2": 2, "C2": 3,
        "S3": 4, "H3": 5, "D3": 6, "C3": 7,
        "S4": 8, "H4": 9, "D4": 10, "C4": 11,
        "S5": 12, "H5": 13, "D5": 14, "C5": 15,
        "S6": 16, "H6": 17, "D6": 18, "C6": 19,
        "S7": 20, "H7": 21, "D7": 22, "C7": 23,
        "S8": 24, "H8": 25, "D8": 26, "C8": 27,
        "S9": 28, "H9": 29, "D9": 30, "C9": 31,
        "ST": 32, "HT": 33, "DT": 34, "CT": 35,
        "SJ": 36, "HJ": 37, "DJ": 38, "CJ": 39,
        "SQ": 40, "HQ": 41, "DQ": 42, "CQ": 43,
        "SK": 44, "HK": 45, "DK": 46, "CK": 47,
        "SA": 48, "HA": 49, "DA": 50, "CA": 51,
    }

    @staticmethod
    def card_value_listoflist_to_bytes_list(cards_list: list[list[int]]) -> list[bytes]:
        return [SrvCardV2.card_values_to_srv_bytes(cards=c) for c in cards_list]

    @staticmethod
    def card_str_listoflist_to_bytes_list(cards_list: list[list[str]]) -> list[bytes]:
        return [SrvCardV2.card_str_list_to_bytes(cards=c) for c in cards_list]

    @staticmethod
    def card_str_list_to_bytes(cards: list[str]) -> bytes:
        """convert card string list to []uint8"""
        cs = [SrvCardV2.card_str_values[card] for card in cards]
        return SrvCardV2.card_values_to_srv_bytes(cards=cs)

    @staticmethod
    def card_values_to_srv_bytes(cards: list[int]) -> bytes:
        """
        Convert a list of card values to a list of server values.
        If only hand cards here, the result should be sorted.
        """
        size = len(cards)
        xs = [SrvCardV2._card_value_to_srv_value(card) for card in cards]
        if size == 2:
            return bytes(sorted(xs))
        return bytes(xs)

    @staticmethod
    def _card_value_to_srv_value(card: int) -> int:
        return SrvCardV2.srv_cards_str_values[SrvCardV2.card_str_seqs[card]]


class WinRateCli(object):
    # 从环境变量读取
    rpc_uri = os.getenv("WIN_RATE_RPC_URI")
    if rpc_uri is None:
        rpc_uri = "localhost:8989"
    channel = grpc.insecure_channel(rpc_uri)
    stub = api_pb2_grpc.WinRateServiceStub(channel)
    srv_card_mod = SrvCardV2

    @staticmethod
    def win_rate(cards: list[str]) -> float:
        cs = WinRateCli.srv_card_mod.card_str_list_to_bytes(cards=cards)
        request = api_pb2.RateRequest(packets=cs)
        response = WinRateCli.stub.GetRate(request)
        return response.rate

    @staticmethod
    def short_deck_win_rate(cards: list[str]) -> float:
        cs = WinRateCli.srv_card_mod.card_str_list_to_bytes(cards=cards)
        request = api_pb2.RateRequest(packets=cs)
        response = WinRateCli.stub.ShortGetRate(request)
        return response.rate

    @staticmethod
    def batch_win_rate(cards_list: list[list[str]]) -> list[float]:
        cs = WinRateCli.srv_card_mod.card_str_listoflist_to_bytes_list(cards_list)
        req = api_pb2.BatchRateRequest(packets=cs)
        resp = WinRateCli.stub.BatchGetRate(req)
        return [r for r in resp.rates]

    @staticmethod
    def win_rate_by_card_values(cards: list[int]) -> float:
        cs = WinRateCli.srv_card_mod.card_values_to_srv_bytes(cards=cards)
        request = api_pb2.RateRequest(packets=cs)
        response = WinRateCli.stub.GetRate(request)
        return response.rate

    @staticmethod
    def batch_win_rate_by_card_values(cards_list: list[list[int]]) -> list[float]:
        cs = WinRateCli.srv_card_mod.card_value_listoflist_to_bytes_list(cards_list)
        req = api_pb2.BatchRateRequest(packets=cs)
        resp = WinRateCli.stub.BatchGetRate(req)
        return [r for r in resp.rates]


class WinRateDocker(object):
    def __init__(self, size: int = 20000):
        self.cache = LRUCache(size)
        self.two_cards_cache = {}
        # WinRateCli.set_srv_card_mod(SrvCardV2)
        self.init_2_cards_win_rate()

    def win_rate(self, cards: list[int]) -> float:
        key = tuple(cards)
        if key in self.cache:
            return self.cache[key]
        rate = WinRateCli.win_rate_by_card_values(cards)
        self.cache[key] = rate
        return rate

    def win_rate_by_str(self, cards: list[str]) -> float:
        cs = CardCode.to_values(cards) # str -> int
        return self.win_rate(cs)

    def win_rate_by_two_str(self, cards: list[str]) -> float:
        cs = sorted(cards)
        key = tuple(cs)
        if key in self.two_cards_cache:
            return self.two_cards_cache[key]
        raise ValueError(f"Key not found: {key}")

    def batch_win_rate(self, cards_list: list[list[int]]) -> list[float]:
        keys = [tuple(cards) for cards in cards_list]
        rates = []
        miss = False
        for i, key in enumerate(keys):
            if key in self.cache:
                rates.append(self.cache[key])
            else:
                miss = True
                break
        if miss:
            rates = WinRateCli.batch_win_rate_by_card_values(cards_list)
            for i, key in enumerate(keys):
                self.cache[key] = rates[i]
        return rates

    def init_2_cards_win_rate(self):
        all_2_cs = gen_two_cards_combinations() #C(n,2)
        all_cs = [CardCode.to_values(cs) for cs in all_2_cs]
        rates = WinRateCli.batch_win_rate_by_card_values(all_cs)
        size = len(all_2_cs)
        r_size = len(rates)
        if size != r_size:
            raise ValueError(f"Size not match: {size} != {r_size}")
        for i in range(size):
            self.two_cards_cache[tuple(all_2_cs[i])] = rates[i]


class ShortWinRateDocker(object):
    def __init__(self, size: int = 20000):
        self.cache = LRUCache(size)

    def win_rate_by_str(self, cards: list[str]) -> float:
        ns = sorted(cards)
        key = "".join(ns)
        if key in self.cache:
            return self.cache[key]
        rate = WinRateCli.short_deck_win_rate(ns)
        self.cache[key] = rate
        return rate

    def win_rate_by_two_str(self, cards: list[str]) -> float:
        return self.win_rate_by_str(cards)


def gen_two_cards_combinations():
    # generate all two cards combinations
    cards = [x for x in CardCode.card_str_encodings]
    sorted_cards = sorted(cards)
    n = len(sorted_cards)
    cs = []
    # generate C(n,2) combinations, user iter tool package
    for i in range(n):
        for j in range(i + 1, n):
            cs.append([sorted_cards[i], sorted_cards[j]])
    return cs
