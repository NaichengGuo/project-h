import numpy as np

from core.coder.predict import PredictInput
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)

    def step(self, state):
        return self.random_action()

    def eval_step(self, state):
        return self.step(state)

    def random_action(self):
        rl_action = np.random.choice([Action.FOLD, Action.CHECK_CALL, Action.RAISE_POT], p=[0.15, 0.65, 0.2])
        if rl_action == Action.RAISE_POT:
            rl_action = np.random.choice([Action.RAISE_HALF_POT,
                                          Action.RAISE_3_4_POT,
                                          Action.RAISE_POT,
                                          Action.RAISE_3_2_POT,
                                          Action.RAISE_DOUBLE_POT,
                                          Action.ALL_IN])
        return rl_action

    def get_name(self):
        return "random"
