from enum import Enum

import numpy as np
from copy import deepcopy

from core.coder.state import ActionInfo, State, PlayerInfo
from core.game.game_base import GameType
from rlcard.games.nolimitholdem.dealer import NolimitholdemDealer as Dealer
from rlcard.games.nolimitholdem.player import NolimitholdemPlayer as Player
from rlcard.games.nolimitholdem.judger import NolimitholdemJudger as Judger
from rlcard.games.nolimitholdem.round import NolimitholdemRound as Round
from core.game.action import Action, rl_action_encode_to_comm
from rlcard.games.nolimitholdem.player import PlayerStatus
from rlcard.utils import seeding
from core.game.action import SB, BB, DB, ANTE


class Stage(Enum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END_HIDDEN = 4
    SHOWDOWN = 5


class NolimitholdemGame(object):
    action_history: list[ActionInfo]
    stage: Stage
    pot: int

    def __init__(self, config=None):
        """Initialize the class no limit holdem Game"""

        if config is None:
            config = {}
            # holdem
            # {
            #     'game_type': 'holdem',
            #     'num_players': 2,
            #     'ante': 0,
            #     'straddle_enabled': False,
            #     'small_blind': 1,
            #     'init_chips': [400, 400],
            #     'seed': None,
            # }
            # short
            # {
            #     'game_type': 'short',
            #     'num_players': 2,
            #     'ante': 1,
            #     'init_chips': [100, 100],
            #     'dealer_double_ante': False,
            #     'seed': None,
            # }

        game_name = config.get('game_type', "holdem")
        if game_name == "holdem":
            self.game_type = GameType.HOLDEM
        elif game_name == "short":
            self.game_type = GameType.SHORT
        else:
            raise ValueError(f'Unrecognized game type: {game_name}')

        self.num_players = config.get('num_players', 2)
        self.seed = config.get('seed', None)
        self.num_actions = len(Action)

        if self.game_type == GameType.HOLDEM:
            self.ante = config.get('ante', 0)
            self.init_chips = config.get('init_chips', [400] * self.num_players)
            self.straddle_enabled = config.get('straddle_enabled', False)
            self.small_blind = config.get('small_blind', 1)
            self.big_blind = 2 * self.small_blind
        else:
            # short deck
            self.ante = config.get('ante', 1)
            self.init_chips = config.get('init_chips', [self.ante * 100] * self.num_players)
            # 庄位强制2倍前注
            self.dealer_double_ante = config.get('dealer_double_ante', False)
            # 短牌没有大小盲的概念，这里为了某些地方处理便利，设置为ante的值
            self.small_blind = self.ante
            self.big_blind = self.ante

        if len(self.init_chips) != self.num_players:
            raise ValueError('Length of init_chips should be equal to num_players')

        self.np_random, _ = seeding.np_random(self.seed)

        # config players

        # If None, the dealer will be randomly chosen
        self.dealer_id = None
        self.all_hand_cards = None

    def reset_dealer_id(self):
        self.dealer_id = self.np_random.randint(0, self.num_players)

    def _reset_game(self):
        """
        Initialize the game of not limit holdem

        This version supports two-player no limit texas holdem

        Returns: None
        """
        # if self.dealer_id is None:
        #     self.dealer_id = self.np_random.randint(0, self.num_players)

        self.reset_dealer_id()
        self.action_history = []

        self._init_dealer()

        # Initialize players to play the game
        self.players = [Player(i, self.init_chips[i], self.np_random) for i in range(self.num_players)]

        # Initialize a judger class which will decide who wins in the end
        self.judger = Judger(self.np_random)

        # Deal cards to each  player to prepare for the first round
        for i in range(2 * self.num_players):
            self.players[i % self.num_players].hand.append(self.dealer.deal_card())

        self.all_hand_cards = [[c.get_index() for c in self.players[i].hand] for i in range(self.num_players)]

        # Initialize public cards
        self.public_cards = []
        self.stage = Stage.PREFLOP

        # Initialize a bidding round, in the first round, the big blind and the small blind needs to
        # be passed to the round for processing.
        self.round = Round(self.num_players, dealer=self.dealer, np_random=self.np_random)
        self._init_force_bet()
        self.round.start_new_round(game_pointer=self.game_pointer, raised=[p.in_chips for p in self.players])

        # Count the round. There are 4 rounds in each game.
        self.round_counter = 0

    def _init_force_bet(self):
        if self.game_type == GameType.HOLDEM:
            # 处理前注
            if self.ante != 0:
                for i in range(self.num_players):
                    self._force_bet(self.players[i], chips=self.ante, action_type=ANTE)

            # Big blind and small blind
            s = (self.dealer_id + 1) % self.num_players
            b = (self.dealer_id + 2) % self.num_players
            self._force_bet(self.players[s], chips=self.small_blind, action_type=SB)
            self._force_bet(self.players[b], chips=self.big_blind, action_type=BB)

            # 处理straddle
            if self.num_players > 2 and self.straddle_enabled:
                straddle_id = (self.dealer_id + 3) % self.num_players
                self._force_bet(self.players[straddle_id], chips=self.big_blind * 2, action_type=DB)

            # The player next to the big blind plays the first
            self.game_pointer = (b + 1) % self.num_players
        else:
            for i in range(self.num_players):
                if i == self.dealer_id and self.dealer_double_ante:
                    self._force_bet(self.players[i], chips=2*self.ante, action_type=ANTE)
                else:
                    self._force_bet(self.players[i], chips=self.ante, action_type=ANTE)

            self.game_pointer = (self.dealer_id + 1) % self.num_players

    def _init_dealer(self):
        # Initialize a dealer that can deal cards
        self.dealer = Dealer(self.np_random, self.game_type)

    def _reset_round_first_player(self):
        if self.game_type == GameType.HOLDEM:
            # 2人局的时候，从FLOP轮开始由大盲注先下注（PREFLOP轮由小盲注先下注)，到了这里，说明最少是FLOP轮了
            if self.num_players == 2:
                self.game_pointer = (self.dealer_id + 2) % self.num_players
            else:
                self.game_pointer = (self.dealer_id + 1) % self.num_players
        else:
            self.game_pointer = (self.dealer_id + 1) % self.num_players

    def _force_bet(self, player: Player, chips, action_type):
        real_bet = player.bet(chips=chips, voluntary=False)
        self.round.add_pot(real_bet)
        action = ActionInfo(
            player_id=player.get_player_id(),
            stage=self.stage.value,
            action=rl_action_encode_to_comm(action_type),
            num=real_bet,
            after_remain_chips=player.remained_chips,
            after_pot=self.round.pot,
            rl_raw_action=action_type,
        )
        self._record_action(action)

    def reset_game(self):
        """
        Initialize the game of not limit holdem

        This version supports two-player no limit texas holdem

        Returns:
            (tuple): Tuple containing:

                (dict): The first state of the game
                (int): Current player's id
        """
        self._reset_game()
        state = self.get_state(self.game_pointer)
        return state, self.game_pointer

    def get_legal_actions(self):
        """
        Return the legal actions for current player

        Returns:
            (list): A list of legal actions
        """
        if self.is_over():
            return []
        return self.round.get_nolimit_legal_actions(players=self.players)

    def is_over(self):
        """
        Check if the game is over

        Returns:
            (boolean): True if the game is over
        """
        alive_players = [1 if p.status in (PlayerStatus.ALIVE, PlayerStatus.ALLIN) else 0 for p in self.players]
        # If only one player is alive, the game is over.
        if sum(alive_players) == 1:
            return True

        # If all rounds are finished
        if self.round_counter >= 4:
            return True
        return False

    def process_step(self, action):
        """
        Get the next state

        Args:

        Returns: None
        """

        # 这里不再判断合法值，在处理action的时候，把不合法的值转为对应的合法的值
        # if action not in self.get_legal_actions():
        #     print(action, self.get_legal_actions())
        #     print(self.get_state(self.game_pointer))
        #     raise Exception('Action not allowed')

        if isinstance(action, int):
            action = Action(action)

        # Then we proceed to the next round
        self.game_pointer, action_info = self.round.proceed_round(self.players, action, self.stage.value)
        self._record_action(action_info)

        # 如果已经结束，不再进行后续的round处理
        if self.is_over():
            return

        players_in_bypass = [1 if player.status in (PlayerStatus.FOLDED, PlayerStatus.ALLIN) else 0 for player in
                             self.players]
        if self.num_players - sum(players_in_bypass) == 1:
            last_player = players_in_bypass.index(0)
            if self.round.raised[last_player] >= max(self.round.raised):
                # If the last player has put enough chips, he is also bypassed
                players_in_bypass[last_player] = 1

        # If a round is over, we deal more public cards
        if self.round.is_over() or len(self.players) == np.sum(players_in_bypass):
            # Game pointer goes to the first player not in bypass after the dealer, if there is one
            self._reset_round_first_player()

            if sum(players_in_bypass) < self.num_players:
                while players_in_bypass[self.game_pointer]:
                    self.game_pointer = (self.game_pointer + 1) % self.num_players

            # For the first round, we deal 3 cards
            if self.round_counter == 0:
                self.stage = Stage.FLOP
                self.public_cards.append(self.dealer.deal_card())
                self.public_cards.append(self.dealer.deal_card())
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1
            # For the following rounds, we deal only 1 card
            if self.round_counter == 1:
                self.stage = Stage.TURN
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1
            if self.round_counter == 2:
                self.stage = Stage.RIVER
                self.public_cards.append(self.dealer.deal_card())
                if len(self.players) == np.sum(players_in_bypass):
                    self.round_counter += 1

            self.round_counter += 1
            self.round.start_new_round(self.game_pointer)

    def step(self, action):
        """
        Get the next state

        Args:
            action (str): a specific action. (call, raise, fold, or check)

        Returns:
            (tuple): Tuple containing:

                (dict): next player's state
                (int): next player id
        """
        self.process_step(action)
        state = self.get_state(self.game_pointer)
        return state, self.game_pointer

    def get_state(self, player_id):
        players = [
            PlayerInfo(
                id=p.get_player_id(),
                chips_remain=p.remained_chips,
                chips_to_desk=p.in_chips
            )
            for p in self.players
        ]
        cur_player = self.players[player_id]
        hand_cards = [
            c.get_index()
            for c in cur_player.hand
        ]
        public_cards = [
            c.get_index()
            for c in self.public_cards
        ]

        legal_actions = [
            int(a.value)
            for a in self.get_legal_actions()
        ]

        state = State(
            game_type=self.game_type,
            players=players,
            my_id=player_id,
            small_blind=self.small_blind,
            ante=self.ante,
            my_hand_cards=hand_cards,
            public_cards=public_cards,
            actions=self.action_history[:],
            legal_actions=legal_actions,
            dealer_id=self.dealer_id,
        )

        return state

    def get_num_players(self):
        """
        Return the number of players in no limit texas holdem

        Returns:
            (int): The number of players in the game
        """
        return self.num_players

    def get_payoffs(self):
        """
        Return the payoffs of the game

        Returns:
            (list): Each entry corresponds to the payoff of one player
        """
        hands = [p.hand + self.public_cards if p.status in (PlayerStatus.ALIVE, PlayerStatus.ALLIN) else None for p in
                 self.players]
        chips_payoffs = self.judger.judge_game(self.players, hands, game_type=self.game_type)
        return chips_payoffs

    @staticmethod
    def get_num_actions():
        """
        Return the number of applicable actions

        Returns:
            (int): The number of actions. There are 6 actions (call, raise_half_pot, raise_pot, all_in, check and fold)
        """
        return len(Action)

    def _record_action(self, action_info: ActionInfo):
        self.action_history.append(action_info)

    def get_action_history(self):
        return self.action_history
