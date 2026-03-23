from core.coder.predict import PredictInput
from core.coder.state import State
from core.game.action import Action
from core.winrate.winrate_wrapper import WinrateWrapper
from models.agent.base.base_agent import BaseAgent

action_order = [Action.ALL_IN, Action.RAISE_POT, Action.RAISE_HALF_POT, Action.CHECK_CALL, Action.FOLD]


class FoldAllInAgent(BaseAgent):

    def __init__(self, config):
        super().__init__(config)
        self.win_rate_processor = WinrateWrapper()

    def step(self, state: State):
        return self.decide_action(state)

    def eval_step(self, state: State):
        return self.step(state)

    def decide_action(self, state: State):
        hands = state.my_hand_cards
        public_cards = state.public_cards
        # win_rate = self.win_rate_processor.get_winrate(hands, public_cards) #暂时注释
        # if win_rate < 0.55:
        #     return state.do_call_if_not_need_pay(Action.FOLD)

        return Action.ALL_IN

    def get_name(self):
        return "fold_all_in"
