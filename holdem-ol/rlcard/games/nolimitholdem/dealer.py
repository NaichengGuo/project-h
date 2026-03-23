from core.game.game_base import GameType
from rlcard.utils.utils import init_standard_deck, init_short_deck


class NolimitholdemDealer(object):
    def __init__(self, np_random, game_type: GameType):
        self.np_random = np_random
        if game_type == GameType.HOLDEM:
            self.deck = init_standard_deck()
        else:
            self.deck = init_short_deck()
        self.shuffle()

    def shuffle(self):
        self.np_random.shuffle(self.deck)

    def deal_card(self):
        """
        Deal one card from the deck

        Returns:
            (Card): The drawn card from the deck
        """
        return self.deck.pop()
