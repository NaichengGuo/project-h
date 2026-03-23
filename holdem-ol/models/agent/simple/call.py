from core.coder.predict import PredictInput
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent


class CallAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)

    def step(self, state):
        return self.decide_action(state)

    def eval_step(self, state):
        return self.decide_action(state)

    def decide_action(self, state):
        return Action.CHECK_CALL

    def get_name(self):
        return "call"