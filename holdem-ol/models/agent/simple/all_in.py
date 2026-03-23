from core.coder.predict import PredictInput
from core.coder.state import State
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent


class AllInAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)

    def step(self, state: State):
        return self.decide_action(state)

    def eval_step(self, state: State):
        return self.decide_action()

    def decide_action(self, state=None):
        return Action.ALL_IN

    def get_name(self):
        return "all_in"