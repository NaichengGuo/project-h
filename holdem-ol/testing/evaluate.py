import json
import mlflow
from core.game.action import Action
from models.agent.manager import make_agent
from models.agent.simple.proxy import ProxyAgent
from rlcard.envs.holdem_env import HoldemEnv
from testing.thirdpart.slumbot_env import tournament_vs_slumbot
from core.utils.mlflowx import set_mlflow_env
from core.utils.aws.sqs import SqsQueue
import testing.config as config
from tqdm import tqdm
num_actions = len(Action)
test_once = False
debug_disable_mlflow = False

def read_task():
    """
    从SQS中读取任务
    :return:
    {
        "model_name": "model_name",
        "version": "v1.0.0",
        "model_service_url": "http://127.0.0.2:5060",
        "round_count": 100,
        "slumbot_count": 100
    }
    """
    # global test_once
    # if test_once:
    #     return None
    test_once = True
    return {
        "model_name": "dqn",
        "version": "v1.0.0",
        "model_service_url": "http://127.0.0.1:10202/invocations",
        "appoint_agent": "",
        "round_count": 100,
        "slumbot_count": 1000
    }
    print("read task from SQS")
    sqs = SqsQueue(config.region, config.sqs_url)
    message = sqs.receive_message()
    if message is None:
        return None
    task = json.loads(message['Body'])
    sqs.delete_message(message['ReceiptHandle'])
    return task


def model_testing(repeat_round: int, slumbot_count: int):
    # 从SQS中读取评测任务，如果没有的话，则结束
    while True:
        task = read_task()
        if task is None:
            return
        _do_model_testing(task, repeat_round, slumbot_count)

def _do_model_testing(task, repeat_round: int, slumbot_count: int):
    print(f"do task : {task}")
    # 对各个基线模型进行评测
    task_round_count = task.get("round_count", repeat_round)
    if task_round_count != 0 and task_round_count < 10:
        task_round_count = 10

    task_slumbot_count = task.get("slumbot_count", slumbot_count)

    model_agent = ProxyAgent(
        {"name": task["model_name"], "model_path": task["model_service_url"], "version": task["version"]}
    )
    appoint_agent = task.get("appoint_agent", "")
    #evaluate_vs_baselines(model_agent, task_round_count, appoint_agent)
    evaluate_vs_slumbot(model_agent, task_slumbot_count)


def evaluate_vs_baselines(model_agent, repeat_round: int, appoint_agent):
    if repeat_round == 0:
        return
    if appoint_agent == "":
        #base_line_agents = ["random", "all_in", "fold_all_in", "prob"]
        #base_line_agents = ["random", "all_in", "fold_all_in"]
        base_line_agents=["prob","prob_v2"]
    else:
        base_line_agents = [appoint_agent]

    results = []
    for bl in base_line_agents:
        er = evaluate_model(model_agent, bl, repeat_round)
        baseline_name = bl
        ber = {
            "baseline_name": baseline_name,
            "params": [
                {
                    "name": "hand_count",
                    "value": er["hand_count"]
                }
            ],
            "metrics": [
                {
                    "name": "mbb/h",
                    "value": er["mbb/h"]
                },
                {
                    "name": "winrate",
                    "value": er["winrate"]
                }
            ]
        }
        results.append(ber)
        print(f"{baseline_name}, hand_count: {er['hand_count']}, mbb/h: {er['mbb/h'] : .1f}, winrate: {er['winrate'] : .1f}%")

    # 评测结果写入mlflow
    write_mlflow(model_agent.full_name, results)


def evaluate_vs_slumbot(model_agent, slumbot_count: int):
    if slumbot_count == 0:
        return
    winrate, mbbh = tournament_vs_slumbot(model_agent, slumbot_count,True)
    ber = {
        "baseline_name": "slumbot",
        "params": [
            {
                "name": "hand_count",
                "value": slumbot_count
            }
        ],
        "metrics": [
            {
                "name": "mbb/h",
                "value": mbbh
            },
            {
                "name": "winrate",
                "value": winrate
            }
        ]
    }
    print(f"slumbot, hand_count: {slumbot_count}, mbb/h: {mbbh}, winrate: {winrate : .1f}%")
    write_mlflow(model_agent.full_name, [ber])


def evaluate_model(model_agent, opponent_name: str, round_count: int):
    batch = 10
    run_round_count = round_count // batch
    real_times = 0
    total_payoffs_bb = 0
    total_winrate = 0
    for i in (range(batch)):
        payoff, run_count, winrate = evaluate_run(model_agent, opponent_name, run_round_count)
        total_payoffs_bb += payoff
        real_times += run_count
        total_winrate += winrate
        print(f"{i+1}/{batch}, real_times: {real_times}, mbb/h: {total_payoffs_bb /real_times * 1000 : .1f}, total_winrate: {total_winrate/(i+1) : .1f}%")

    mbbh = total_payoffs_bb / real_times * 1000
    final_winrate = total_winrate / batch

    return {
        "hand_count": real_times,
        "mbb/h": mbbh,
        "winrate": final_winrate
    }


def evaluate_run(model_agent, opponent_name: str, round_count: int):
    # 评测模型
    env = HoldemEnv({'num_players':3})
    config = {
    }
    agent1 = make_agent(opponent_name, config)
    agents = [model_agent, agent1,agent1]
    env.set_agents(agents)

    total_payoffs = [0 for _ in range(len(agents))]
    win_counts = [0 for _ in range(len(agents))]
    real_times = 0
    for r in range(round_count):
        trajectories, payoffs = env.run(is_training=False)
        real_times += 1
        for i in range(len(payoffs)):
            total_payoffs[i] += payoffs[i]
            if payoffs[i] > 0:
                win_counts[i] += 1

    game_name = f"{model_agent.full_name}_vs_{opponent_name}"
    winrate = win_counts[0] / real_times * 100.0
    total_payoffs_bb = total_payoffs[0] / 2.0

    return total_payoffs_bb, real_times, winrate


def set_mlflow_params(local=False, disable_mlflow=False):
    global debug_disable_mlflow
    debug_disable_mlflow = disable_mlflow
    if local:
        tracking_uri = "http://127.0.0.1:5000"
        mlflow.set_tracking_uri(tracking_uri)
    else:
        set_mlflow_env()


def write_mlflow(model_name, result):

    if debug_disable_mlflow:
        return

    experiment = "Holdem_robot_model_testing"
    mlflow.set_experiment(experiment)

    print("write mlflow")

    for r in result:
        run_name = f"{model_name}_vs_{r['baseline_name']}"
        with mlflow.start_run(run_name=run_name):
            for p in r["params"]:
                mlflow.log_param(p["name"], p["value"])
            for m in r["metrics"]:
                mlflow.log_metric(m["name"], m["value"])


if __name__ == '__main__':
    model_testing(2, 2)
