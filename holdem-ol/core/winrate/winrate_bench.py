import random

from core.utils import CollectionUtil
from core.winrate.dup_card import dup_all_cards


class TestWinRate(object):
    all_card_strs = dup_all_cards.copy()
    all_cards = [i for i in range(52)]

    @staticmethod
    def random_gen_cards_str():
        return TestWinRate._random_gen(TestWinRate.all_card_strs)
    
    @staticmethod
    def random_gen_cards():
        return TestWinRate._random_gen(TestWinRate.all_cards)
    
    @staticmethod
    def compare_win_rate(fn1: callable, fn2: callable, cs: list[str]):
        r1, r2 = fn1(cs), fn2(cs)
        diff = abs(r1-r2)
        if diff > 0.03:
            print(f'cs: {cs} abs diff: {abs(r1-r2)} r1: {r1}, r2: {r2}')
        # else:
        #    print(f'abs diff: {abs(r1-r2)}')
    
    @staticmethod
    def _random_gen(all_cards: list) -> list:
        cs_size = random.choice([0, 3, 4, 5])
        player1_hand = random.sample(all_cards, 2)
        # remaining cards is all cards sub player1_hand
        remaining_cards = CollectionUtil.sub(all_cards, player1_hand)
        if cs_size == 0:
            return player1_hand
        community_cards = random.sample(remaining_cards, cs_size)
        return player1_hand + community_cards

