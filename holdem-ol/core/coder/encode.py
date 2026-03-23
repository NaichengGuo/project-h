from core.coder.state import ActionInfo, PlayerInfo, State
from core.game.action import Action, calc_raise_value, rl_action_to_comm, PlayerAction, ActionEffect, comm_action_to_rl
from core.game.action import SB, BB, DB, ANTE
from core.game.card import CardCode

sb_action_to_comm_action = {
    "f": 0,
    "k": 1,
    "c": 1,
    "b": 2,
    "sb": SB,
    "bb": BB,
}

def sb_state_to_comm_state(sb_state) -> State:
    """
    actions sample : [(sb_pos, -1, "sb", 50), (bb_pos, -1, "bb", 100)]
    :param sb_state:
    :return:
    """
    actions = sb_state["actions"]
    my_pos = sb_state["my_pos"]
    pot = 0
    total_chip = sb_state["total_chip"]
    remain_chips = [total_chip, total_chip]
    chips_to_desk = [0, 0]
    sb_pos = actions[0][0]
    comm_actions = []
    for a in actions:
        diff = abs(chips_to_desk[0] - chips_to_desk[1])
        op_pos = a[0]
        stage = a[1]
        sb_action = a[2]
        num = a[3]

        if stage < 0:
            stage = 0
        action_type = sb_action_to_comm_action[sb_action]
        if action_type == 2 and remain_chips[op_pos] <= num:
            action_type = 3

        if action_type > 1:
            rl_action = comm_action_to_rl(action_type, num-diff, pot + diff)
            rl_action = rl_action.value
        else:
            rl_action = action_type

        pot = pot + a[3]
        remain_chips[op_pos] = remain_chips[op_pos] - num
        chips_to_desk[op_pos] = chips_to_desk[op_pos] + num

        comm_actions.append(
            ActionInfo(
                player_id=int(op_pos),
                stage=int(stage),
                action=int(action_type),
                num=int(num),
                after_remain_chips=int(remain_chips[op_pos]),
                after_pot=int(pot),
                rl_raw_action=rl_action
            )
        )

    dealer_id = (sb_pos + 1) % 2

    players = [
        PlayerInfo(
            id=0,
            chips_remain=remain_chips[0],
            chips_to_desk=chips_to_desk[0]
        ),
        PlayerInfo(
            id=1,
            chips_remain=remain_chips[1],
            chips_to_desk=chips_to_desk[1]
        )
    ]

    hole_cards = CardCode.cmm_to_rl_strs(sb_state["hole_cards"])
    board = CardCode.cmm_to_rl_strs(sb_state["board"])

    state = State(
        players=players,
        my_id=my_pos,
        dealer_id=dealer_id,
        small_blind=50,
        ante=0,
        my_hand_cards=hole_cards,
        public_cards=board,
        actions=comm_actions,
    )

    return state


def sb_state_to_tmp_state(sb_state):
    action_info = sb_state["action_info"]
    actions = sb_state["actions"]
    my_pos = sb_state["my_pos"]
    pot = 0
    total_chip = 20000
    remain_chip = total_chip
    last_bet_size = action_info["last_bet_size"]
    for a in actions:
        pot = pot + a[3]
        if a[0] == my_pos:
            remain_chip = remain_chip - a[3]

    min_bet = last_bet_size
    if min_bet < 100:
        min_bet = 100

    state = {}
    state["hand"] = sb_state["hole_cards"]
    state["public_cards"] = sb_state["board"]
    state["total_chip"] = sb_state["total_chip"]
    state["street_last_bet_to"] = action_info["street_last_bet_to"]
    state["pot"] = pot
    state["remain_chip"] = remain_chip
    state["last_bet_size"] = last_bet_size
    state["min_bet"] = min_bet
    state["small_blind"] = 50

    return state


def rl_action_to_sb_action(action, tmp_state):
    # 当前轮次的最大下注额
    street_last_bet_to = tmp_state["street_last_bet_to"]
    # 当前轮次的diff
    last_bet_diff = tmp_state["last_bet_size"]
    min_bet = tmp_state["min_bet"]
    pot = tmp_state["pot"]
    remain_chip = tmp_state["remain_chip"]

    virtual_pot = pot + last_bet_diff

    if action == Action.FOLD:
        if last_bet_diff > 0:
            return "f"
        else:
            action = Action.CHECK_CALL

    if action == Action.CHECK_CALL:
        if last_bet_diff > 0:
            return "c"
        else:
            return "k"
    elif action == Action.ALL_IN:
        bet_diff = remain_chip
    else:
        bet_diff = calc_raise_value(virtual_pot, action) + last_bet_diff

    if bet_diff < min_bet:
        bet_diff = min_bet
    if bet_diff > remain_chip:
        bet_diff = remain_chip

    # 自己当前轮次上次的下注额
    my_cur_round_last_bet = street_last_bet_to - last_bet_diff
    max_bet = remain_chip + my_cur_round_last_bet
    bet_size = my_cur_round_last_bet + bet_diff
    if bet_size > max_bet:
        bet_size = max_bet
    if bet_size == street_last_bet_to:
        return "c"

    # 最后这个bxxx里面的值是本轮次下注的筹码总和
    return "b" + str(bet_size)
