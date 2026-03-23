import time
from collections import OrderedDict

import numpy as np

from core.coder import encode
from core.coder.predict import PredictInput
from core.coder.state import State
from core.game.action import Action, comm_action_to_rl
from core.game.card import CardCode
from testing.thirdpart.vs_slumbot import play_with_slumbot, log

legal_actions = list(Action)


def tournament_vs_slumbot(agent, hands, print_info=False):
    token = None
    total = 0
    win_count = 0
    real_times = 0
    winrate = 0
    mbbh = 0
    env = SlumbotEnv(agent, print_info=print_info)
    for i in range(hands):
        print(f"-----strat hand {i}-----")
        _, payoff = env.run()
        total += payoff[0]
        real_times += 1
        if payoff[0] > 0:
            win_count += 1
        winrate = win_count / real_times * 100
        mbbh = total / real_times / 100 * 1000  # bb的值为100，mbb的单位得再乘以1000
        if real_times % 100 == 0:
            log.info(f'winrate: {win_count}/{real_times} : {winrate :.1f}%, mbb/h: {mbbh :.1f}')

    env.debug_print_static()
    return winrate, mbbh


class SlumbotEnv(object):
    def __init__(self, agent, num_players=2, print_info=False):
        self.trajectory = []
        self.slumbot_token = None
        self.agent = agent
        self.num_players = num_players
        self.print_info = print_info
        self.clear_static()
        self.is_training = False

    def set_agent(self, agent):
        self.agent = agent

    def reset(self):
        self.trajectory = []

    def run(self, is_training=True):
        self.is_training = is_training
        tr, payoff, _ = self.run_get_extra_info()
        return tr, payoff

    def run_get_extra_info(self):
        self.reset()
        self.run_count += 1
        token, winnings, sb_state = play_with_slumbot(self, self.slumbot_token, print_info=self.print_info)
        self.slumbot_token = token
        state = encode.sb_state_to_comm_state(sb_state)
        self.trajectory.append(state)
        self.update_oppo_action_static(state)
        pay_offs = int(winnings / state.small_blind)
        return [self.trajectory, []], np.array([pay_offs, -pay_offs]), sb_state.get("bot_hole_cards", [])

    def predict_api(self, input_dict):
        state, return_rl_action = PredictInput.parse_input(input_dict)
        if self.is_training:
            agent_action = self.agent.step(state)
        else:
            #t1=time.time()
            agent_action = self.agent.eval_step(state)
            #t2=time.time()
            #print(f'time cost: {t2-t1}')
        if isinstance(agent_action, Action):
            agent_action = int(agent_action.value)
        self.trajectory.append(state)
        self.trajectory.append(agent_action)
        self.action_static[0][agent_action] += 1

        return {
            "action": agent_action,
        }

    def clear_static(self):
        self.run_count = 0
        self.action_static = [[0 for _ in range(len(Action))] for _ in range(self.num_players)]

    def debug_print_static(self):
        for i in range(self.num_players):
            print(f"player {i} action_static: (hands: {self.run_count})")
            print("----------------")
            print(f"{''.ljust(30)}   ratio   per-hand")
            actions = self.action_static[i]
            value_sum = sum(actions)
            if value_sum == 0:
                value_sum = 1
            run_count = self.run_count
            if run_count == 0:
                run_count = 1
            for j in range(len(actions)):
                print(f"{str(Action(j)).ljust(30)}: {actions[j] / value_sum : .3f}  {actions[j] / run_count : .3f}")

    def update_oppo_action_static(self, state: State):

        my_id = state.my_id
        for a in state.actions:
            if a.player_id == state.my_id:
                continue
            if a.action < 0:
                continue

            self.action_static[1][a.action] += 1

    def get_bb(self):
        return 100
