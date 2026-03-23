from core.coder.state import State
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent
import random

class StepRaiseAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)

    def step(self, state: State):
        return self.decide_action(state)

    def eval_step(self, state: State):
        return self.step(state)

    def decide_action(self, state: State):

        # 使得raise分布在更多的stage
        if state.get_cur_stage() < 3:
            if random.random() <= 0.35:
                return Action.CHECK_CALL

        pot = int(state.pot / state.small_blind)
        if pot < 20:
            return Action.RAISE_POT
        if pot < 60:
            return Action.RAISE_HALF_POT
        return Action.ALL_IN
    def get_name(self):
        return "step_raise"