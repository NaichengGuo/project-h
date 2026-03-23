from core.coder.state import State
from core.game.action import Action
from core.utils.logger import log
from models.agent.base.base_agent import BaseAgent
from models.restore import restore_model


class WrapPpoAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            raise ValueError("config is None")
        device = config.get("device", "cpu")
        model_path = config.get("model_path", "")
        if model_path == "":
            raise ValueError("model_path is empty")

        # log.info(f"load model from {model_path}")
        self.model_path = model_path
        log.info(f"load model from:{model_path} -- device:{device}")
        self.model, self.model_tpye = restore_model(model_path, device)

    def get_name(self):
        return f"{self.model_tpye}({self.model_path})"

    def eval_step(self, state: State) -> Action:
        action = self.model.inference(state)
        return state.do_call_if_not_need_pay(Action(action))