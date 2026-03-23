from typing import Any

import numpy as np

from core.coder.state import State
from models.dqn.consts import USER_STATICS_INFO_SIZE
from rlcard.games.nolimitholdem.game import Stage


class UserStatic(object):
    def __init__(self,
                 player_num: int,
                 min_us_size: int,
                 max_us_size: int,
                 padding_value: float):
        self.player_num = player_num
        self.min_us_size = min_us_size
        self.max_us_size = max_us_size
        self.padding_value = np.full(USER_STATICS_INFO_SIZE, padding_value, dtype=np.float32)

    def feed_statics_info(self, state: State, dst_np: np.array, idx: int):
        """
        Args:
            state: a State object
            dst_np: a np.array with shape (self.static_info_size,)
            idx: the start index of the static_info in dst_np
        Returns:
            dst_np: a np.array with shape (self.static_info_size,)
        """
        # copy state.player_statics to static_info from idx
        players_histories = state.action_history
        players_nps = [self.player_statics(players_histories[i]) for i in range(self.player_num)]
        cursor = idx
        for i in range(self.player_num):
            dst_np[cursor:cursor + USER_STATICS_INFO_SIZE] = players_nps[i]
            cursor += USER_STATICS_INFO_SIZE
        return dst_np

    def player_statics(self, p_bet_histories: list[list[list[Any]]]):
        """
        Args:
            p_bet_histories: a 3D list, [game, meta/or actions, scalar]
        Returns:
            player_statics: a np.array(14 elements)
        """
        game_size = len(p_bet_histories)
        if game_size < self.min_us_size:
            return self.padding_value.copy()

        bf_bets = np.zeros(game_size)
        f_bets = np.zeros(game_size)
        t_bets = np.zeros(game_size)
        r_bets = np.zeros(game_size)
        payoffs = np.zeros(game_size)
        bf_fold = 0
        f_fold = 0
        t_fold = 0
        r_fold = 0

        for i in range(game_size):
            item_size = len(p_bet_histories[i])
            small_blind = p_bet_histories[i][0][0]
            payoffs[i] = p_bet_histories[i][0][1] / small_blind
            for j in range(1, item_size):
                action = p_bet_histories[i][j]
                stage = action[0]
                action_act = action[1]
                num = action[2]

                if action_act == 0:
                    if stage == Stage.PREFLOP.value:
                        bf_fold += 1
                    elif stage == Stage.FLOP.value:
                        f_fold += 1
                    elif stage == Stage.TURN.value:
                        t_fold += 1
                    elif stage == Stage.RIVER.value:
                        r_fold += 1
                    continue

                if stage == Stage.PREFLOP.value:
                    bf_bets[i] += num / small_blind
                elif stage == Stage.FLOP.value:
                    f_bets[i] += num / small_blind
                elif stage == Stage.TURN.value:
                    t_bets[i] += num / small_blind
                elif stage == Stage.RIVER.value:
                    r_bets[i] += num / small_blind
        return setup_user_statics(bf_bets=bf_bets, f_bets=f_bets, t_bets=t_bets, r_bets=r_bets, payoffs=payoffs,
                                  bf_fold=bf_fold, f_fold=f_fold, t_fold=t_fold, r_fold=r_fold, game_size=game_size)


def setup_user_statics(bf_bets, f_bets, t_bets, r_bets, payoffs, bf_fold, f_fold, t_fold, r_fold, game_size):
    """
    calculate statics, including mean, std of sample, fold rate
    Args:
        bf_bets:
        f_bets:
        t_bets:
        r_bets:
        payoffs:
        bf_fold:
        f_fold:
        t_fold:
        r_fold:
        game_size:
    Returns:
        numpy array with shape (14,)
    """
    v = np.zeros(USER_STATICS_INFO_SIZE, dtype=np.float32)
    v[0] = np.mean(bf_bets)
    v[1] = np.std(bf_bets, ddof=1)
    v[2] = np.mean(f_bets)
    v[3] = np.std(f_bets, ddof=1)
    v[4] = np.mean(t_bets)
    v[5] = np.std(t_bets, ddof=1)
    v[6] = np.mean(r_bets)
    v[7] = np.std(r_bets, ddof=1)
    v[8] = np.mean(payoffs)
    v[9] = np.std(payoffs, ddof=1)
    # fold rate
    v[10] = bf_fold / game_size
    v[11] = f_fold / game_size
    v[12] = t_fold / game_size
    v[13] = r_fold / game_size
    return v
