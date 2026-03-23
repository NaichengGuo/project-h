from cachetools import LRUCache
from core.game.card import CardCode
from core.winrate.srv_card import WinRateCli


class ShortDeckWinRateDocker(object):
    def __init__(self, size: int = 20000):
        self.cache = LRUCache(size)

    def win_rate_by_str(self, cards: list[str]) -> float:
        key = "".join(cards)
        if key in self.cache:
            return self.cache[key]
        wr = WinRateCli.short_deck_win_rate(cards)
        self.cache[key] = wr
        return wr
