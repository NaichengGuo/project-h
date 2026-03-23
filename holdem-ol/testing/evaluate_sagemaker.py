import json
import os
import mlflow
import boto3
from datetime import datetime, timezone
from core.game.action import Action
from models.agent.manager import make_agent
from models.agent.base.base_agent import BaseAgent
from rlcard.envs.holdem_env import HoldemEnv
from testing.thirdpart.slumbot_env import tournament_vs_slumbot
from core.utils.mlflowx import set_mlflow_env
from core.utils.aws.sqs import SqsQueue
import testing.config as config
from tqdm import tqdm
num_actions = len(Action)
test_once = False
debug_disable_mlflow = False


class SageMakerEndpointAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}
        self.name = config.get("name", "")
        self.version = config.get("version", "")
        self.endpoint_name = config.get("endpoint_name", "")
        self.model_name = config.get("model_name", "")
        self.region_name = config.get("region_name")
        if self.region_name:
            self.runtime_client = boto3.client('sagemaker-runtime', region_name=self.region_name)
        else:
            self.runtime_client = boto3.client('sagemaker-runtime')
        self.full_name = f"{self.name}-{self.version}"

    def step(self, state):
        return self.eval_step(state)

    def eval_step(self, state):
        payload = {
            "inputs": state.to_dict(),
            "params": {
                "return_rl_action": True,
                "on_game_start": False
            }
        }
        if self.model_name:
            payload["params"]["model_name"] = self.model_name
        response = self.runtime_client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload),
        )
        result = json.loads(response['Body'].read().decode())
        predictions = result.get("predictions", {})
        action = predictions.get("action", Action.FOLD.value)
        return Action(int(action))


def read_task():
    test_once = True
    return {
        "model_name": "dqn",
        "version": "v1.0.0",
        "endpoint_name": "holdem-ev-v1-endpoint",
        "model_route_names": ["ev_v1_aggressive", "ev_v2_neutral", "gto_v1", "gto_v2", "mtt_v1"],
        "appoint_agent": "",
        "result_file": os.path.join(os.path.dirname(__file__), "evaluate_sagemaker_results.jsonl"),
        "model_eval_rounds": 5,
        "per_round_battle_count": 1000,
        "round_count": 1000,
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
    while True:
        task = read_task()
        if task is None:
            return
        _do_model_testing(task, repeat_round, slumbot_count)


def _do_model_testing(task, repeat_round: int, slumbot_count: int):
    print(f"do task : {task}")
    per_round_battle_count = int(task.get("per_round_battle_count", 1000))
    model_eval_rounds = int(task.get("model_eval_rounds", 5))
    task_round_count = int(task.get("round_count", per_round_battle_count))
    if task_round_count != 0 and task_round_count < 10:
        task_round_count = 10

    task_slumbot_count = int(task.get("slumbot_count", per_round_battle_count))
    if task_slumbot_count <= 0:
        task_slumbot_count = per_round_battle_count
    if model_eval_rounds <= 0:
        model_eval_rounds = 5
    endpoint_name = task.get("endpoint_name") or task.get("model_service_url")
    appoint_agent = task.get("appoint_agent", "")
    enable_baselines = task.get("enable_baselines", False)
    result_file = task.get("result_file") or os.path.join(
        os.path.dirname(__file__), "evaluate_sagemaker_results.jsonl"
    )

    model_route_names = task.get("model_route_names")
    if not model_route_names:
        model_route_name = task.get("model_route_name", "")
        if isinstance(model_route_name, str) and "," in model_route_name:
            model_route_names = [name.strip() for name in model_route_name.split(",") if name.strip()]
        else:
            model_route_names = [model_route_name]

    for model_route_name in model_route_names:
        print(
            f"[MODEL-START] route={model_route_name}, eval_rounds={model_eval_rounds}, "
            f"per_round_battle_count={per_round_battle_count}, slumbot_count={task_slumbot_count}"
        )
        round_records = []
        model_agent = SageMakerEndpointAgent(
            {
                "name": task["model_name"],
                "version": task["version"],
                "endpoint_name": endpoint_name,
                "model_name": model_route_name,
                "region_name": task.get("region_name"),
            }
        )
        for round_idx in range(model_eval_rounds):
            print(f"[ROUND-START] route={model_route_name}, round={round_idx + 1}/{model_eval_rounds}")
            evaluate_results = []
            if enable_baselines:
                baseline_results = evaluate_vs_baselines(model_agent, task_round_count, appoint_agent)
                evaluate_results.extend(baseline_results)
            slumbot_result = evaluate_vs_slumbot(model_agent, task_slumbot_count)
            if slumbot_result is not None:
                evaluate_results.append(slumbot_result)

            round_record = {
                "round_index": round_idx + 1,
                "battle_count": task_slumbot_count,
                "results": evaluate_results,
            }
            round_records.append(round_record)
            print(f"[ROUND-END] route={model_route_name}, round={round_idx + 1}, results={evaluate_results}")

        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "endpoint_name": endpoint_name,
            "model_route_name": model_route_name,
            "agent_full_name": model_agent.full_name,
            "model_eval_rounds": model_eval_rounds,
            "per_round_battle_count": per_round_battle_count,
            "round_results": round_records,
        }
        write_eval_record(result_file, record)
        print(f"[MODEL-END] route={model_route_name}, saved evaluate record to {result_file}")


def evaluate_vs_baselines(model_agent, repeat_round: int, appoint_agent):
    if repeat_round == 0:
        return []
    if appoint_agent == "":
        base_line_agents = ["prob", "prob_v2"]
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

    write_mlflow(model_agent.full_name, results)
    return results


def evaluate_vs_slumbot(model_agent, slumbot_count: int):
    if slumbot_count == 0:
        return None
    winrate, mbbh = tournament_vs_slumbot(model_agent, slumbot_count, True)
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
    return ber


def write_eval_record(result_file, record):
    result_dir = os.path.dirname(result_file)
    if result_dir:
        os.makedirs(result_dir, exist_ok=True)
    with open(result_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def evaluate_model(model_agent, opponent_name: str, round_count: int):
    batch = 10
    run_round_count = round_count // batch
    real_times = 0
    total_payoffs_bb = 0
    total_winrate = 0
    for i in range(batch):
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
    env = HoldemEnv({'num_players': 3})
    config = {
    }
    agent1 = make_agent(opponent_name, config)
    agents = [model_agent, agent1, agent1]
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
