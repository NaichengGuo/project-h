import json
import os
import random

from models.agent.base.base_agent import BaseAgent
from models.agent.manager import make_agent


class UnionAgent(BaseAgent):
    def __init__(self, config=None):
        if config is None:
            config = {}
        super().__init__(config)
        model_weights_file = config.get("model_path", "")
        with (open(model_weights_file) as f):
            model_weights = json.load(f)

        self.agents = []
        self.weights = []
        for model_weight in model_weights:
            agent_type = model_weight["agent_type"]
            model_path = model_weight["model_path"]
            weight = model_weight["weight"]
            argmax_action = model_weight.get("argmax_action", False)

            if not os.path.exists(model_path):
                raise Exception(f"model_path file not exists: {model_weight}")
            agent = make_agent(agent_type, {
                "model_path": model_path,
                "argmax_action": argmax_action,
            })
            self.agents.append(agent)
            self.weights.append(weight)

        if len(self.agents) == 0:
            raise Exception(f"agent is empty")
        self.agent = self.agents[0]

    def on_game_start(self):
        self.agent = random.choices(self.agents, self.weights)[0]
        print(f"[UnionAgent] game start, choice agent : {self.agent.get_name()}")

    def eval_step(self, state):
        return self.agent.eval_step(state)


