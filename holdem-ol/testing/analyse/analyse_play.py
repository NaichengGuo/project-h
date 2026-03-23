import argparse
import os
import pandas as pd
import ray

from models.agent.manager import make_agent
from rlcard.envs.holdem_env import HoldemEnv
from testing.analyse.distributed import aggregate_run_games
from testing.run_env import run

def play_vs_models(agent_type: str, model_path: str, oppo_agents: iter, round_count: int, task_count: int):
    results = []
    for o in oppo_agents:
        result = aggregate_run_games(agent_type, model_path, o[0], o[1], round_count, task_count)
        results.append(result)
    print_results(results, round_count)

def print_results(results, round_count):
    data = []
    model_names = []

    title = ["winrate", "mbb/h", "fold", "check/call", "pot/2", "3/4_pot", "pot", "3/2_pot", "double_pot",
             "all_in"]
    agent0_name = ""
    for result in results:
        oppo_model_name = result["agent1_name"]
        agent0_name = result["agent0_name"]
        model_names.append(oppo_model_name)
        play_result = to_play_result(result)
        data.append(play_result)
        stage_action_static_data = [play_result]
        stage_action_static = result["stage_action_statics"]
        index_name = [oppo_model_name]
        total_action = 0
        for stage in range(4):
            for v in stage_action_static[stage]:
                total_action += v

        for stage in range(4):
            d = ["-", "-"]
            d.extend(to_ratio_str(stage_action_static[stage], total_action))
            stage_action_static_data.append(d)
            index_name.append(f"stage_{stage}")
        df = pd.DataFrame(stage_action_static_data, columns=title, index=index_name)
        print(df.to_string())
    df = pd.DataFrame(data, columns=title, index=model_names)

    print(f"------sort by mbb [vs {agent0_name}] episode: {round_count} ------")
    df = df.sort_values(by='mbb/h', ascending=False)
    print(df.to_string())
    print("", flush=True)

def to_play_result(result):
    return [result["winrate"], result["mbb/h"]] + to_ratio_str(result["action_static"])


def to_ratio_str(data: list, sum_value=None):
    if sum_value is None:
        sum_value = sum(data)
    if sum_value == 0:
        return ["0%" for x in data]
    data = [x / sum_value for x in data]
    return [f"{x * 100:.2f}%" for x in data]


def play_with_model(env, agents, round_count):
    env.set_agents(agents)
    env.clear_static()
    result = run(env, round_count)
    action_static = env.get_action_static()[0]
    return [result["winrate"], result["mbb/h"]] + to_ratio_str(action_static)
