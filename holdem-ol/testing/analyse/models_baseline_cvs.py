import argparse
import os
import pandas as pd
from testing.analyse.distributed import aggregate_run_games


def _get_model_files(model_file_dir: str, model_file_subfix: str):
    return [os.path.join(model_file_dir, f) for f in os.listdir(model_file_dir) if f.endswith(model_file_subfix)]

def to_ratio(data):
    sum_value = sum(data)
    if sum_value == 0:
        return [0 for _ in data]
    data = [x / sum_value for x in data]
    return data

def to_result(result):
    new_result = [result["agent0_name"], result["winrate"], result["mbb/h"]]
    action_static = result["action_static"]
    new_result.extend(to_ratio(action_static))
    real_round_count = result["real_round_count"]
    for a in action_static:
        new_result.append(a / real_round_count)
    return new_result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_type", type=str, default="dqn")
    parser.add_argument("--model_file_dir", type=str, default="")
    parser.add_argument("--model_file_subfix", type=str, default="pth")
    parser.add_argument("--mbb_threshold", type=int, default=0)
    parser.add_argument("--output_dir", type=str, default="")
    parser.add_argument("--round_count", type=int, default=1)
    parser.add_argument("--task_count", type=int, default=1)
    args = parser.parse_args()

    if args.output_dir == "":
        print("output_dir is required")
        return
    os.makedirs(args.output_dir, exist_ok=True)

    title = ["model", "winrate", "mbb/h", "fold", "check/call", "pot/2", "3/4_pot", "pot", "3/2_pot", "double_pot", "all_in",
     "fold_per_game", "check/call_per_game", "pot/2_per_game", "3/4_pot_per_game", "pot_per_game", "3/2_pot_per_game", "double_pot_per_game", "all_in_per_game"]

    baselines = ["prob", "all_in", "step_raise", "fold_all_in", "call", "random"]
    model_files = _get_model_files(args.model_file_dir, args.model_file_subfix)

    progress = 0
    baselines_result = {
        "prob": [],
        "all_in": [],
        "step_raise": [],
        "fold_all_in": [],
        "call": [],
        "random": []
    }
    for mf in model_files:
        mbbh = []
        progress += 1
        print(f'[progress : {progress}/{len(model_files)} models]', end='', flush=True)
        one_result = {
        }
        pass_count = 0
        for b in baselines:
            r = aggregate_run_games(args.agent_type, mf, b, "", args.round_count, args.task_count)
            print('=', end='', flush=True)
            mbbh.append(r["mbb/h"])
            one_result[b] = to_result(r)
            if r["mbb/h"] < args.mbb_threshold:
                break
            pass_count += 1

        print()
        if pass_count < len(baselines):
            print(f"[no pass] {mf}, mbb/h: {mbbh} ({baselines})", flush=True)
            continue

        for b in baselines:
            baselines_result[b].append(one_result[b])

    for k, v in baselines_result.items():
        df = pd.DataFrame(v, columns=title, index=None)
        df.to_csv(os.path.join(args.output_dir, f"vs_{k}.csv"))


if __name__ == '__main__':
    main()
