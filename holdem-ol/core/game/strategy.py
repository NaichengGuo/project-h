from core.game.action import Action
from core.coder.predict import PredictInput

strategy_data = {
    '0': [
        [0.37, 0.7, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT]
    ],
    '3': [
        [0.35, 0.75, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT]
    ],
    '4': [
        [0.35, 0.75, 0.85, 0.9, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT, Action.RAISE_DOUBLE_POT, Action.ALL_IN]
    ],
    '5': [
        [0.35, 0.75, 0.85, 0.9, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT, Action.RAISE_DOUBLE_POT, Action.ALL_IN]
    ],
}


def decide_action(win_rate, public_card_count, legal_actions):
    sd = strategy_data[str(public_card_count)]
    action = Action.FOLD
    for i in range(len(sd[0]) - 1):
        if sd[0][i] <= win_rate < sd[0][i + 1]:
            action = sd[1][i]
            break
    if action in legal_actions:
        return action, action
    else:
        if action == Action.RAISE_POT:
            if Action.RAISE_HALF_POT in legal_actions:
                return action, Action.RAISE_HALF_POT
            elif Action.CHECK_CALL in legal_actions:
                return action, Action.CHECK_CALL
            else:
                return action, Action.FOLD

        return action, Action.FOLD


def calc_legal_actions(state : PredictInput):

    pot = 0
    remain_chip = 0
    for p in state.players:
        pot += p.chips_to_desk
        if p.id == state.my_id:
            remain_chip = p.chips_remain

    last_raise = 0
    for a in reversed(state.actions):
        if a.action == 4 or a.action == 5:
            last_raise = a.num
            break

    legal_actions = [Action.FOLD, Action.CHECK_CALL]
    if remain_chip <= last_raise:
        return legal_actions

    half_pot = pot / 2

    if remain_chip >= half_pot:
        legal_actions.append(Action.RAISE_HALF_POT)

    if remain_chip >= pot:
        legal_actions.append(Action.RAISE_POT)

    legal_actions.append(Action.ALL_IN)

    return legal_actions
