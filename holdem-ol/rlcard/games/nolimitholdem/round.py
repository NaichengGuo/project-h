# -*- coding: utf-8 -*-
"""Implement no limit texas holdem Round class"""

from core.coder.state import ActionInfo
from rlcard.games.nolimitholdem.player import NolimitholdemPlayer
from rlcard.games.nolimitholdem.player import PlayerStatus
from core.game.action import Action, calc_raise_value, rl_action_encode_to_comm


def print_type():
    full_actions = list(Action)
    print(f"{type(full_actions)}")
    return full_actions


class NolimitholdemRound:
    """Round can call functions from other classes to keep the game running"""

    def __init__(self, num_players, dealer, np_random):
        """
        Initialize the round class

        Args:
            num_players (int): The number of players
            init_raise_amount (int): The min raise amount when every round starts
        """
        self.np_random = np_random
        self.game_pointer = None
        self.num_players = num_players
        self.pot = 0

        self.dealer = dealer

        # Count the number without raise
        # If every player agree to not raise, the round is over
        self.not_raise_num = 0

        # Count players that are not playing anymore (folded or all-in)
        self.not_playing_num = 0

        # Raised amount for each player
        self.raised = [0 for _ in range(self.num_players)]

    def start_new_round(self, game_pointer, raised=None):
        """
        Start a new bidding round

        Args:
            game_pointer (int): The game_pointer that indicates the next player
            raised (list): Initialize the chips for each player

        Note: For the first round of the game, we need to setup the big/small blind
        """
        self.game_pointer = game_pointer
        self.not_raise_num = 0
        if raised:
            self.raised = raised
        else:
            self.raised = [0 for _ in range(self.num_players)]

    def process_raise(self, player: NolimitholdemPlayer, action: Action, stage):
        if action == Action.ALL_IN:
            raised = player.remained_chips
        else:
            diff = max(self.raised) - self.raised[self.game_pointer]
            pot = self.pot + diff
            raised = calc_raise_value(pot, action)
            raised += diff
        if raised > player.remained_chips:
            raised = player.remained_chips

        real_bet = player.bet(chips=raised)
        self.raised[self.game_pointer] = real_bet + self.raised[self.game_pointer]
        self.not_raise_num = 1
        return real_bet

    def proceed_round(self, players: list[NolimitholdemPlayer], action: Action, stage) -> (int, ActionInfo):
        """
        Call functions from other classes to keep one round running

        Args:
            players (list): The list of players that play the game
            action (str/int): An legal action taken by the player
            stage (int): The stage of the game

        Returns:
            (int): The game_pointer that indicates the next player
        """
        player = players[self.game_pointer]

        diff = max(self.raised) - self.raised[self.game_pointer]
        if int(action.value) > int(Action.CHECK_CALL.value) and player.remained_chips <= diff:
            action = Action.CHECK_CALL

        real_bet = 0
        if action == Action.CHECK_CALL:
            real_bet = player.bet(chips=diff)
            self.raised[self.game_pointer] = self.raised[self.game_pointer] + real_bet
            self.not_raise_num += 1

        elif action == Action.FOLD:
            player.status = PlayerStatus.FOLDED
        else:
            real_bet = self.process_raise(player, action, stage)

        if player.remained_chips < 0:
            raise Exception("Player in negative stake")

        if player.remained_chips == 0 and player.status != PlayerStatus.FOLDED:
            player.status = PlayerStatus.ALLIN

        if player.status == PlayerStatus.ALLIN:
            self.not_playing_num += 1
            self.not_raise_num -= 1  # Because already counted in not_playing_num
        if player.status == PlayerStatus.FOLDED:
            self.not_playing_num += 1

        self.game_pointer = (self.game_pointer + 1) % self.num_players

        # Skip the folded && ALLIN players
        # iter_count 用于防止死循环
        iter_count = 0
        while iter_count <= self.num_players and (players[self.game_pointer].status == PlayerStatus.FOLDED or players[self.game_pointer].status == PlayerStatus.ALLIN):
            iter_count += 1
            self.game_pointer = (self.game_pointer + 1) % self.num_players

        self.add_pot(real_bet)
        action_info = ActionInfo(
            player_id=player.player_id,
            stage=stage,
            action=rl_action_encode_to_comm(action.value),
            num=real_bet,
            after_remain_chips=player.remained_chips,
            after_pot=self.pot,
            rl_raw_action=action.value,
        )

        return self.game_pointer, action_info

    def get_nolimit_legal_actions(self, players: list[NolimitholdemPlayer]):
        """
        Obtain the legal actions for the current player

        Args:
            players (list): The players in the game

        Returns:
           (list):  A list of legal actions
        """

        full_actions = [Action.FOLD, Action.CHECK_CALL]

        # The player can always check or call
        player = players[self.game_pointer]

        diff = max(self.raised) - self.raised[self.game_pointer]
        if player.remained_chips <= diff:
            return full_actions

        # 目前最小的raise动作是 half pot ，而 pot 是按补齐了diff筹码来算的，因而raise动作都是合法的（如果下注额超过了自己的剩余筹码，自动转为ALL_IN）
        # 这里不用判断是否满足最小的raise额度，因为目前最小的raise值为 half pot，永远都会大于最小的合法raise
        self.feed_valid_raise_action(diff, player.remained_chips, full_actions)

        return full_actions

    def feed_valid_raise_action(self, diff, remained_chips, full_actions):
        pot = self.pot + diff
        remained_chips -= diff
        raise_values = [int(pot / 2), int(pot * 3 / 4), pot, int(pot * 3 / 2), pot * 2, remained_chips]
        for i, value in enumerate(raise_values):
            full_actions.append(Action(i + Action.RAISE_HALF_POT.value))
            if remained_chips <= value:
                break

    def is_over(self):
        """
        Check whether the round is over

        Returns:
            (boolean): True if the current round is over
        """
        if self.not_raise_num + self.not_playing_num >= self.num_players:
            return True
        return False

    def add_pot(self, chips):
        self.pot += chips
