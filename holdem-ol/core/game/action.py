from enum import Enum
import numpy as np

SB = -1
BB = -2
DB = -3
ANTE = -4

comm_action_str = {
    -1: "sb",
    -2: "bb",
    -3: "db",
    -4: "ante",
    0: "fold",
    1: "check/call",
    2: "raise",
    3: "all_in"
}


def to_comm_action_str(action):
    return comm_action_str.get(action, "unknown")


class CommStateAction(Enum):
    Fold = 0
    CheckCall = 1
    Raise = 2
    AllIn = 3


class Action(Enum):
    FOLD = 0
    CHECK_CALL = 1
    RAISE_HALF_POT = 2
    RAISE_3_4_POT = 3
    RAISE_POT = 4
    RAISE_3_2_POT = 5
    RAISE_DOUBLE_POT = 6
    ALL_IN = 7


class ActionEffect(object):
    Fold = 0
    Init = 1
    Check_Call = 2
    Raise = 3

    @staticmethod
    def convert_user_action(action_value: int):
        if action_value == Action.FOLD.value:
            return ActionEffect.Fold
        elif action_value == Action.CHECK_CALL.value:
            return ActionEffect.Check_Call
        else:
            return ActionEffect.Raise


class RawAction(object):
    Fold = Action.FOLD
    CheckCall = Action.CHECK_CALL
    RaiseHalfPot = Action.RAISE_HALF_POT
    RaisePot = Action.RAISE_POT
    AllIn = Action.ALL_IN
    Sb = 16
    Bb = 17


def calc_raise_value(pot, action):
    if not isinstance(action, Action):
        raise ValueError(f"action must be an instance of Action, but got {action}")

    if action == Action.RAISE_HALF_POT:
        return int(pot / 2)
    elif action == Action.RAISE_3_4_POT:
        return int(pot * 3 / 4)
    elif action == Action.RAISE_POT:
        return pot
    elif action == Action.RAISE_3_2_POT:
        return int(pot * 3 / 2)
    elif action == Action.RAISE_DOUBLE_POT:
        return pot * 2
    else:
        return 0


def rl_action_to_comm(action: Action, diff, remain_chips, virtual_pot):
    if not isinstance(action, Action):
        raise ValueError(f"action must be an instance of Action, but got {action}")

    if action == Action.FOLD:
        return 0, 0
    if action == Action.CHECK_CALL:
        if diff > remain_chips:
            return 1, remain_chips
        return 1, diff
    if action == Action.ALL_IN:
        return 3, remain_chips
    raise_value = calc_raise_value(virtual_pot, action)
    return 2, raise_value + diff


def comm_action_to_rl(action, num, pot):
    if action == 0:
        return Action.FOLD
    if action == 1:
        return Action.CHECK_CALL
    if action == 3:
        return Action.ALL_IN

    pot_3_4 = int(pot * 3 / 4)
    pot_3_2 = int(pot * 3 / 2)
    pot_2 = int(pot * 2)

    if num < pot_3_4:
        return Action.RAISE_HALF_POT
    if num < pot:
        return Action.RAISE_3_4_POT
    if num < pot_3_2:
        return Action.RAISE_POT
    if num < pot_2:
        return Action.RAISE_3_2_POT

    return Action.RAISE_DOUBLE_POT


def to_stage(public_cards_count):
    if public_cards_count == 0:
        return 0
    if public_cards_count == 3:
        return 1
    if public_cards_count == 4:
        return 2

    return 3


def rl_action_encode_to_comm(action: int):
    if action <= 1:
        return action

    if action == Action.ALL_IN.value:
        return 3

    return 2


class PlayerAction(object):
    """
    Player's action
    """

    def __init__(self,
                 stage: int,
                 player_id: int,
                 action: int,
                 delta_chips: float,
                 after_chips: float,
                 pot_chips: float = 0.0,
                 ):
        self.stage = stage
        self.player_id = player_id
        self.action = action
        self.delta_chips = delta_chips
        self.after_chips = after_chips
        self.pot_chips = pot_chips

    def as_np_array_float32(self):
        return np.array([
            self.stage,
            self.player_id,
            self.action,
            self.delta_chips,
            self.after_chips],
            dtype=np.float32)

    def to_dict(self):
        return {
            'stage': self.stage,
            'player_id': self.player_id,
            'action': self.action,
            'delta_chips': self.delta_chips,
            'after_chips': self.after_chips
        }

    def __str__(self):
        return 'stage: {}, player_id: {}, action: {}, delta_chips: {}, after_chips: {}'.format(
            self.stage, self.player_id, self.action, self.delta_chips, self.after_chips)

    def as_np_array_float32_v2(self):
        return np.array([
            self.stage,
            self.player_id,
            self.action,
            self.delta_chips,
            self.after_chips,
            self.pot_chips],
            dtype=np.float32)

    def to_dict_v2(self):
        return {
            'stage': self.stage,
            'player_id': self.player_id,
            'action': self.action,
            'delta_chips': self.delta_chips,
            'after_chips': self.after_chips,
            'pot_chips': self.pot_chips
        }


if __name__ == '__main__':
    actions = list(Action)
    for a in actions:
        print(f"{a}: {rl_action_encode_to_comm(a.value)}")

    for a in [SB, BB, DB, ANTE]:
        print(f"{a}: {rl_action_encode_to_comm(a)}")
