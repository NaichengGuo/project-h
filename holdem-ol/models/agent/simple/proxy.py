import json
import numpy as np
import requests

from core.coder.state import State
from core.game.action import Action
import core.coder.encode as encode
from models.agent.base.base_agent import BaseAgent


class ProxyAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}
        self.name = config.get("name", "")
        self.url = config.get("model_path", "")
        self.version = config.get("version", "")
        self.full_name = f"{self.name}-{self.version}"

    def step(self, state: State):
        return self.decide(state)

    def eval_step(self, state: State):
        return self.step(state)

    def decide(self, state: State):

        data = {
            "inputs": state.to_dict(),
            "params": {
                "return_rl_action": True
            }
        }
        action_result = self.predict_api(data)
        action_code = action_result["action"]
        action = Action(action_code)

        return action

    def predict_api(self, input_dict: dict):
        comm_state_json = json.dumps(input_dict)

        response = requests.post(self.url, data=comm_state_json, headers={'Content-Type': 'application/json'},
                                 timeout=15).json()
        if "predictions" not in response:
            print(response)

        # 将响应的JSON格式数据转换为Python字典
        return response["predictions"]

    def get_name(self):
        return f"proxy({self.url})"
