from core.coder.state import State
from core.game.action import Action
from core.utils.logger import log
from models.agent.base.base_agent import BaseAgent
from models.restore import restore_model


class WrapDqnAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            raise ValueError("config is None")
        device = config.get("device", "cpu")
        model_path = config.get("model_path", "")
        if model_path == "":
            raise ValueError("model_path is empty")
        argmax_action = config.get("argmax_action", False)

        # log.info(f"load model from {model_path}")
        self.model_path = model_path
        log.info(f"load model from:{model_path} -- argmax_action:{argmax_action}  -- device:{device}")
        self.model, self.model_tpye = restore_model(model_path, device, argmax_action)

    def get_name(self):
        return f"{self.model_tpye}({self.model_path})"

    def eval_step(self, state: State) -> Action:
        action = self.model.inference(state)
        # if state.get_cur_stage() < 3:
        # return Action(action)
        return state.do_call_if_not_need_pay(Action(action))
