import random
import time

from core.game.compare import calculate_win_rate
from core.winrate.dup_card import dup_all_cards

def test_calculate_win_rate():
    # random select a number from 0,3,4,5

    t1 = time.time()
    for i in range(1000):
        cs_size = random.choice([0, 3, 4, 5])
        player1_hand = random.sample(dup_all_cards, 2)
        remaining_cards = [c for c in dup_all_cards if c not in player1_hand]
        community_cards = random.sample(remaining_cards, cs_size)
        _ = calculate_win_rate(player1_hand, community_cards, 1000)
    t2 = time.time()
    print(f"Time: {t2-t1}, average:{(t2-t1)/1000}")


def test_calculate_win_rate_rpc():
    """WinRateCli.init()
    t1 = time.time()
    for i in range(1000):
        cs_size = random.choice([0, 3, 4, 5])
        player1_hand = random.sample(dup_all_cards, 2)
        remaining_cards = [c for c in dup_all_cards if c not in player1_hand]
        community_cards = random.sample(remaining_cards, cs_size)
        _ = WinRateCli.cards_str_win_rate(player1_hand + community_cards)
    t2 = time.time()
    print(f"Time: {t2-t1}, average:{(t2-t1)/1000}")"""
    pass


if __name__ == "__main__":    
    test_calculate_win_rate()
    #test_calculate_win_rate_rpc()
