import random
import time

from core.coder.state import State, print_actions
from core.game.action import Action, to_comm_action_str
from core.utils.logger import print_red
from models.agent.base.base_agent import BaseAgent
from rlcard.utils import print_card


action_name = [
    "fold",
    "cc",
    "1/2pot",
    "3/4pot",
    "pot",
    "3/2pot",
    "2pot",
    "allin"
]

class HumanAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)

    def step(self, state: State):
        oppo_id = 1 if state.my_id == 0 else 0

        # print(
        #     f"pot: {state.pot}, my_id: {state.my_id}")
        # print(
        #     f"my  : remain chips: {state.players[state.my_id].chips_remain}, chips to desk: {state.players[state.my_id].chips_to_desk}")
        # print(
        #     f"oppo: remain chips: {state.players[oppo_id].chips_remain}, chips to desk: {state.players[oppo_id].chips_to_desk}")

        print_actions(state.actions, state.my_id)

        print("public cards:\n")
        if len(state.public_cards) > 0:
            print_card(state.public_cards)
        else:
            print("[]")

        print("your cards:\n")
        print_card(state.my_hand_cards)

        oppo_last_action = None
        last_action = state.actions[-1]
        if last_action.player_id == oppo_id and last_action.stage >= 0:
            oppo_last_action = f"{to_comm_action_str(last_action.action)} : {last_action.num} chips"

        my_player = state.players[state.my_id]
        print_red(f"oppo last action: {oppo_last_action}")
        print_red(f"pot: {state.pot}, oppo_chips_to_desk: {state.players[oppo_id].chips_to_desk}, my_chips_to_desk: {my_player.chips_to_desk}, my_remain: {my_player.chips_remain}")

        print("available actions: ")
        for a in list(Action):
            _, num = state.generate_comm_action(a)
            if num > my_player.chips_remain:
                num = my_player.chips_remain
            print(f"{a.value}: {action_name[a.value]}({num}), ", end="")
        print()
        while True:
            try:
                action = int(input(
                    '>> You choose action: '))
                if action < 0 or action >= 8:
                    print('Action illegal...')
                else:
                    break
            except Exception as e:
                print('illegal input : {e}')
        for _ in range(10):
            # time.sleep(0.1)
            print("-", end="", flush=True)
        print()
        return action

    def eval_step(self, state):
        return self.step(state)
