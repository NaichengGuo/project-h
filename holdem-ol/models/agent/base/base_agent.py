from core.coder.predict import PredictInput
from core.coder.state import State
from core.game.action import Action


class BaseAgent(object):
    def __init__(self, config=None):
        pass

    def step(self, state: State) -> Action:
        """
        内部Env训练的时候被调用
        :param state:
        :return:
        """
        raise NotImplementedError

    def eval_step(self, state: State) -> Action:
        """
        内部Env非训练的时候被调用
        :param state:
        :return:
        """
        raise NotImplementedError

    def on_game_start(self):
        pass

    def predict_api(self, input_dict: dict):
        """
        外部Env预测的时候被调用，输入为dict
        :param input_dict:
        :return:
        """
        state, return_rl_action, params = self.parse_input(input_dict)
        on_game_start_flag = params.get("on_game_start", False)
        if on_game_start_flag:
            self.on_game_start()
        #print(f"")
        action = self.eval_step(state)
        final_action, num = state.generate_comm_action(Action(action), return_rl_action)

        return {
            "action": int(final_action),
            "num": num
        }

    def get_name(self):
        return self.__class__.__name__

    @staticmethod
    def parse_input(input_dict: dict) -> (State, bool, dict):
        state = State.from_dict(input_dict["inputs"])
        params = input_dict.get("params", {})
        return_rl_action = params.get("return_rl_action", False)
        return state, return_rl_action, params
