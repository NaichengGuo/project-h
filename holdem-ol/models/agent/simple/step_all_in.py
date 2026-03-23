import random
from core.coder.state import State
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent


class StepAllInAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)

    def step(self, state: State):
        return self.decide_action(state)

    def eval_step(self, state: State):
        return self.decide_action(State)

    def decide_action(self, state):
        # 使得raise分布在更多的stage
        if state.get_cur_stage() < 3:
            if random.random() <= 0.35:
                return Action.CHECK_CALL
        return Action.ALL_IN

    def get_name(self):
        return "step_all_in"