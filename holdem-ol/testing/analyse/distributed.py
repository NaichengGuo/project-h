import ray
from core.game.action import Action
from models.agent.manager import make_agent
from rlcard.envs.holdem_env import HoldemEnv


@ray.remote
def run_games(agent_type_0, model_path_0, agent_type_1, model_path_1, round_count):
    env = HoldemEnv()
    agent0 = make_agent(agent_type_0, {
        "model_path": model_path_0,
        "argmax_action": True,
    })
    agent1 = make_agent(agent_type_1, {
        "model_path": model_path_1,
        "argmax_action": True,
    })
    env.set_agents([agent0, agent1])
    total_payoffs = []
    for _ in range(round_count):
        _, payoffs = env.run(is_training=False)
        total_payoffs.append(payoffs[0])

    result = {
        "payoffs": total_payoffs,
        "action_static": env.get_action_static()[0],
        "stage_action_statics": env.get_stage_action_static()[0],
        "agent0_name": agent0.get_name(),
        "agent1_name": agent1.get_name(),
    }

    return result


def aggregate_run_games(agent_type_0, model_path_0, agent_type_1, model_path_1, round_count, task_count):
    sub_round_count = round_count // task_count
    task_ids = [run_games.remote(agent_type_0, model_path_0, agent_type_1, model_path_1, sub_round_count) for _ in
                range(task_count)]
    results = ray.get(task_ids)
    all_payoffs = []
    action_static = [0 for _ in range(len(Action))]
    stage_action_statics = [[0 for _ in range(len(Action))] for _ in range(4)]
    for r in results:
        payoffs = r["payoffs"]
        action_static_partial = r["action_static"]
        stage_action_static_partial = r["stage_action_statics"]
        all_payoffs.extend(payoffs)
        for i in range(len(action_static_partial)):
            action_static[i] += action_static_partial[i]
        for j in range(4):
            for k in range(len(stage_action_static_partial[j])):
                stage_action_statics[j][k] += stage_action_static_partial[j][k]

    total = 0
    win_counts = 0
    for pay in all_payoffs:
        total += pay
        if pay > 0:
            win_counts += 1

    real_round_count = len(all_payoffs)

    result = {
        "winrate": win_counts / real_round_count * 100.0,
        "total_payoffs": total / 2.0,
        "mbb/h": total / 2.0 / real_round_count * 1000,
        "action_static": action_static,
        "stage_action_statics": stage_action_statics,
        "agent0_name": results[0]["agent0_name"],
        "agent1_name": results[0]["agent1_name"],
        "real_round_count": real_round_count,
    }

    return result
