import argparse
import ray
from testing.analyse.analyse_play import play_vs_models


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_type_0", type=str, default="")
    parser.add_argument("--agent_type_1", type=str, default="")
    parser.add_argument("--model_path_0", type=str, default="")
    parser.add_argument("--model_path_1", type=str, default="")
    parser.add_argument("--round_count", type=int, default=1)
    parser.add_argument("--task_count", type=int, default=1)
    args = parser.parse_args()

    ray.init()
    oppo = [
        (args.agent_type_1, args.model_path_1)
    ]
    play_vs_models(args.agent_type_0, args.model_path_0, oppo, args.round_count, args.task_count)
    ray.shutdown()
