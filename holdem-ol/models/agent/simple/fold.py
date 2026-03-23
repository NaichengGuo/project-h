from core.coder.predict import PredictInput
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent


class FoldAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)

    def step(self, state):
        return self.decide_action(state)

    def eval_step(self, state):
        return self.decide_action(state)

    def decide_action(self, state):
        return Action.FOLD

    def get_name(self):
        return "fold"