import argparse
import logging
import sys
import time
import testing.thirdpart.slumbot as slumbot
from core.coder import encode
from core.game.action import Action

shandle = logging.StreamHandler()
shandle.setFormatter(
    logging.Formatter(
        '[%(asctime)s] '
        '%(message)s'))
log = logging.getLogger('vs_slumbot')
log.propagate = False
log.addHandler(shandle)
log.setLevel(logging.INFO)


def play_with_slumbot(agent, token, print_info=True):
    r = slumbot.NewHand(token)
    new_token = r.get('token')
    if new_token:
        token = new_token

    action = r.get('action')
    client_pos = r.get('client_pos')
    old_action = r.get('old_action')
    if old_action == "" and action == "":
        sb_pos = client_pos
    else:
        sb_pos = (client_pos + 1) % 2

    while True:
        action = r.get('action')
        client_pos = r.get('client_pos')
        hole_cards = r.get('hole_cards')
        board = r.get('board')
        winnings = r.get('winnings')

        a = slumbot.ParseAction(action)
        if 'error' in a:
            print('Error parsing action %s: %s' % (action, a['error']))
            sys.exit(-1)

        actions, stage_chip_infos = slumbot.ParseActionV2(sb_pos, action)
        sb_state = {
            "action_info": a,
            "actions": actions,
            "my_pos": client_pos,
            "hole_cards": hole_cards,
            "board": board,
            "total_chip": 20000,
            "stage_chip_infos": stage_chip_infos,
        }

        if winnings is not None:
            bot_hole_cards = r.get('bot_hole_cards')
            sb_state["bot_hole_cards"] = bot_hole_cards
            if print_info:
                print(f"wingings: {winnings}, hole_cards: {hole_cards}, bot_hole_cards: {bot_hole_cards}, board: {board}, action: {action}, sb_pos: {sb_pos}, client_pos: {client_pos}")
            return (token, winnings, sb_state)

        incr = generate_slumbot_action(agent, sb_state)
        r = slumbot.Act(token, incr)


def generate_slumbot_action(agent, sb_state):
    comm_state = encode.sb_state_to_comm_state(sb_state)
    tmp_state = encode.sb_state_to_tmp_state(sb_state)
    data = {
        "inputs": comm_state.to_dict(),
        "params": {
            "return_rl_action": True
        }
    }
    action_code = agent.predict_api(data)
    return encode.rl_action_to_sb_action(Action(action_code["action"]), tmp_state)
