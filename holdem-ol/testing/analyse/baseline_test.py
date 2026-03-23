import argparse
import ray
from testing.analyse.analyse_play import play_vs_models

def gen_agent():
    agent_names = ["prob", "random", "fold_all_in", "all_in", "call", "step_raise"]
    for agent_type in agent_names:
        yield agent_type, ""


if __name__ == '__main__':
    parser = argparse.ArgumentParser("main")

    parser.add_argument("--agent_type_0", type=str, default="")
    parser.add_argument("--model_path_0", type=str, default="")
    parser.add_argument("--round_count", type=int, default=1)
    parser.add_argument("--task_count", type=int, default=1)
    args = parser.parse_args()

    ray.init()
    agent_generator = gen_agent()
    play_vs_models(args.agent_type_0, args.model_path_0, agent_generator, args.round_count, args.task_count)
    print("\ndone!")
    ray.shutdown()
