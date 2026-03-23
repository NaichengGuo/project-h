import argparse
import os
import pandas as pd
from models.agent.manager import make_agent
from rlcard.envs.holdem_env import HoldemEnv
from testing.analyse.analyse_play import play_vs_models
from testing.run_env import run


def gen_agent(agent_type: str, model_dir: str, model_file_subfix: str):
    eval_model_names = os.listdir(model_dir)
    for mn in eval_model_names:
        if mn.endswith(model_file_subfix) is False:
            continue
        file_path = os.path.join(model_dir, mn)
        yield agent_type, file_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser("main")
    parser.add_argument("--agent_type_0", type=str, default="")
    parser.add_argument("--model_path_0", type=str, default="")
    parser.add_argument("--agent_type_1", type=str, default="random")
    parser.add_argument("--model_file_dir", type=str, default="")
    parser.add_argument("--model_file_subfix", type=str, default="pth")
    parser.add_argument("--round_count", type=int, default=1)
    parser.add_argument("--task_count", type=int, default=1)
    args = parser.parse_args()

    agent_generator = gen_agent(args.agent_type_1, args.model_file_dir, args.model_file_subfix)
    play_vs_models(args.agent_type_0, args.model_path_0, agent_generator, args.round_count, args.task_count)
