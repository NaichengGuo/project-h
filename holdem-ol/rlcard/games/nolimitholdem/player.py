from enum import Enum
from core.game.action import ActionEffect


class PlayerStatus(Enum):
    ALIVE = 0
    FOLDED = 1
    ALLIN = 2


class NolimitholdemPlayer(object):
    def __init__(self, player_id, init_chips, np_random):
        """
        Initialize a player.

        Args:
            player_id (int): The id of the player
            init_chips (int): The number of chips the player has initially
        """
        self.np_random = np_random
        self.player_id = player_id
        self.hand = []
        self.status = PlayerStatus.ALIVE

        # The chips that this player has put in until now
        self.in_chips = 0

        self.remained_chips = init_chips
        # 是否主动投注过
        self.ever_voluntary_bet = False


    def get_state(self, public_cards, all_chips, legal_actions):
        """
        Encode the state for the player

        Args:
            public_cards (list): A list of public cards that seen by all the players

        Returns:
            (dict): The state of the player
        """
        return {
            'hand': [c.get_index() for c in self.hand],
            'public_cards': [c.get_index() for c in public_cards],
            'all_chips': all_chips,
            'my_chips': self.in_chips,
            'legal_actions': legal_actions
        }

    def bet(self, chips, voluntary=True):
        if voluntary:
            self.ever_voluntary_bet = True
        quantity = chips if chips <= self.remained_chips else self.remained_chips
        self.in_chips += quantity
        self.remained_chips -= quantity
        return quantity


    def get_player_id(self):
        return self.player_id
