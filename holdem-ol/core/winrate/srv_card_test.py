import itertools
import grpc
import random

import core.winrate.winrate_pb2 as api_pb2
import core.winrate.winrate_pb2_grpc as api_pb2_grpc
from core.game.game_base import GameType

from core.winrate.srv_card import (
    SrvCard,
    SrvCardV2,
    WinRateCli
)

from core.game.compare import compare_hands,calculate_win_rate
from core.winrate.dup_card import dup_all_cards


def compare_hands_v2(_cs1, _cs2):
    _r = compare_hands([_cs1, _cs2], GameType.HOLDEM)
    return _r[0]


def calculate_c7_win_rate(cs):
    remain_desk = [card for card in dup_all_cards if card not in cs]
    wins = 0
    other_css = list(itertools.combinations(remain_desk, 2))
    for other_cs in other_css:
        other_cs = list(other_cs)
        p2_cards = other_cs + cs[2:]
        winner = compare_hands([cs, p2_cards], GameType.HOLDEM)
        if winner[0] == 1:
            wins += 1
    return wins / len(other_css)


def test_compare_hands_v2():
    cs1 = ['CA', 'CQ', 'CT', 'S4', 'SQ', 'ST', 'HT']
    cs2 = ['C3', 'C4', 'CT', 'S4', 'SQ', 'ST', 'HT']
    r = compare_hands_v2(cs1, cs2)
    print(f'compare result: {r} cs1:{cs1}, cs2;{cs2}')
    r = compare_hands_v2(cs2, cs1)
    print(f'reverse compare result: {r} cs1:{cs2}, cs2;{cs1}')


def test_card_value_to_srv_value():
    SrvCard.initialize()
    for i in range(52):
        print(f"{i}: {SrvCard._card_value_to_srv_value(i)}")


def test_cards_to_srv_values(strs: list[str]):
    SrvCard.initialize()
    cards = [SrvCard.cards_str_value[card] for card in strs]
    for c in cards:
        print(f"{c}: {SrvCard._card_value_to_srv_value(c)}")


"""
    test_cards_to_srv_values(['S2', 'H2', 'D2', 'C2'])
    test_cards_to_srv_values(['S3', 'H3', 'D3', 'C3'])
    test_cards_to_srv_values(['S4', 'H4', 'D4', 'C4'])
    test_cards_to_srv_values(['S5', 'H5', 'D5', 'C5'])
    test_cards_to_srv_values(['S6', 'H6', 'D6', 'C6'])
    test_cards_to_srv_values(['S7', 'H7', 'D7', 'C7'])
    test_cards_to_srv_values(['S8', 'H8', 'D8', 'C8'])
    test_cards_to_srv_values(['S9', 'H9', 'D9', 'C9'])
    test_cards_to_srv_values(['ST', 'HT', 'DT', 'CT'])
    test_cards_to_srv_values(['SJ', 'HJ', 'DJ', 'CJ'])
    test_cards_to_srv_values(['SQ', 'HQ', 'DQ', 'CQ'])
    test_cards_to_srv_values(['SK', 'HK', 'DK', 'CK'])
    test_cards_to_srv_values(['SA', 'HA', 'DA', 'CA'])
"""


def test_cards_value():
    cards = ['SA', 'HA', 'DA', 'CA']
    SrvCard.initialize()
    print(SrvCard.card_str_list_to_num_list(cards))


def test_cards_win_rate(cards: list[str]):
    SrvCard.initialize()
    channel = grpc.insecure_channel("localhost:8989")
    stub = api_pb2_grpc.WinRateServiceStub(channel)
    cs = SrvCard.card_str_list_to_bytes(cards=cards)
    request = api_pb2.RateRequest(packets=cs)
    response = stub.GetRate(request)
    print(response)


def test_cards_win_rate_by_cls(cards: list[str]):
    WinRateCli.initialize()
    print(WinRateCli.win_rate(cards))
    WinRateCli.set_srv_card_mod(SrvCardV2)
    print(WinRateCli.win_rate(cards))
    r = calculate_win_rate(cards, cards[2:], 1000)
    print(f'Random sampe win rate: {r}')


def test_card_convert():
    SrvCard.initialize()
    # SrvCard.cards_str_value
    cs = [''] * 52
    for k, v in SrvCard.cards_str_value.items():
        cs[v] = k
    print(cs)
    scs = [0] * 52
    for i in range(52):
        scs[i] = SrvCard._card_value_to_srv_value(i)
    print(scs)

    ccs = [cs[card] for card in scs]
    print(ccs)

    '''vs = [9] * 52
    for i in range(52):
        vs[i] = SrvCard._card_value_to_srv_value(i)
        print(f"{cs[i]}: {cs[vs[i]]}")'''


def test_card_convert_v2():
    p1 = [0] * 52
    p2 = [0] * 52
    for i in range(52):
        p1[i] = SrvCard._card_value_to_srv_value(i)
    for i in range(52):
        p2[i] = SrvCardV2._card_value_to_srv_value(i)
    print(p1)
    print(p2)


def test_hand_cards_rate():
    css = itertools.combinations(dup_all_cards, 2)
    WinRateCli.initialize()
    for cs in css:
        cs = list(cs)
        r1 = calculate_win_rate(cs, [], 100000)
        WinRateCli.set_srv_card_mod(SrvCard)
        r2 = WinRateCli.win_rate(cs)
        WinRateCli.set_srv_card_mod(SrvCardV2)
        r3 = WinRateCli.win_rate(cs)
        if abs(r1 - r2) > 0.03:
            print(f'cs: {cs} abs diff: {abs(r1 - r2)} r1: {r1}, r2: {r2}')
        if abs(r2 - r3) > 0.00001:
            print(f'cs: {cs} abs diff: {abs(r2 - r3)} r2: {r2}, r3: {r3}')


def test_hand_c5_rate():
    WinRateCli.initialize()
    WinRateCli.set_srv_card_mod(SrvCardV2)
    for i in range(1000):
        cs = random.sample(dup_all_cards, 7)

        r1 = WinRateCli.win_rate(cs)
        r2 = calculate_win_rate(cs[:2], cs[2:], 5000)
        r3 = calculate_c7_win_rate(cs)
        if abs(r2 - r3) > 0.03:
            print(f'cs: {cs} sample and cal diff: {abs(r2 - r3)} r2: {r2}, r3: {r3}')
        if abs(r1 - r3) > 0.03:
            print(f'cs: {cs} rpc and cal diff: {abs(r1 - r2)} r1: {r1}, r2: {r2}')


def test_hand_c5_rate_v2():
    for i in range(1000):
        cs = random.sample(dup_all_cards, 7)
        r1 = calculate_win_rate(cs[:2], cs[2:], 5000)
        r2 = calculate_c7_win_rate(cs)
        if abs(r1 - r2) > 0.01:
            print(f'cs: {cs} sample and cal diff: {abs(r1 - r2)} r1: {r1}, r2: {r2}')


def test_hand_c5_rate_v3():
    WinRateCli.initialize()
    WinRateCli.set_srv_card_mod(SrvCardV2)
    count = 0
    for i in range(1000):
        cs = random.sample(dup_all_cards, 7)

        r1 = WinRateCli.win_rate(cs)
        r2 = calculate_c7_win_rate(cs)
        if abs(r1 - r2) > 0.01:
            print(f'cs: {cs} cal diff: {abs(r1 - r2)} r1: {r1}, r3: {r2}')
            count += 1
    print(f'different count: {count}')


if __name__ == "__main__":
    # test_compare_hands_v2()
    # test_cards_win_rate(['S2', 'H2'])
    # test_cards_win_rate_by_cls(['S2', 'H2'])
    # test_card_convert()
    # test_card_convert_v2()
    # test_cards_win_rate_by_cls(['S2', 'H2'])
    # test_hand_cards_rate()
    # test_hand_c5_rate()
    # test_hand_c5_rate_v2()
    test_hand_c5_rate_v3()
