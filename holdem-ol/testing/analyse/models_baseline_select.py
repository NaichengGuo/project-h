import argparse
import os

from testing.analyse.analyse_play import print_results
from testing.analyse.distributed import aggregate_run_games


def _get_model_files(model_file_dir: str, model_file_subfix: str):
    return [os.path.join(model_file_dir, f) for f in os.listdir(model_file_dir) if f.endswith(model_file_subfix)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_type", type=str, default="dqn")
    parser.add_argument("--model_file_dir", type=str, default="")
    parser.add_argument("--model_file_subfix", type=str, default="pth")
    parser.add_argument("--mbb_threshold", type=int, default=0)
    parser.add_argument("--round_count", type=int, default=1)
    parser.add_argument("--task_count", type=int, default=1)
    args = parser.parse_args()

    baselines = ["prob", "all_in", "step_raise", "fold_all_in", "call", "random"]
    model_files = _get_model_files(args.model_file_dir, args.model_file_subfix)
    progress = 0
    for mf in model_files:
        results = []
        mbbh = []
        progress += 1
        print(f'[progress : {progress}/{len(model_files)} models]', end='')
        for b in baselines:
            r = aggregate_run_games(args.agent_type, mf, b, "", args.round_count, args.task_count)
            print('=', end='', flush=True)
            mbbh.append(r["mbb/h"])
            if r["mbb/h"] < args.mbb_threshold:
                break
            results.append(r)

        if len(results) < len(baselines):
            print(f"\n[no pass] {mf}, mbb/h: {mbbh} ({baselines})", flush=True)
            continue
        print()
        print_results(results, args.round_count)


if __name__ == '__main__':
    main()
