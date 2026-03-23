import argparse
import time

from models.agent.manager import make_agent
from testing.thirdpart.slumbot_env import tournament_vs_slumbot
from testing.thirdpart.vs_slumbot import log


def main(hands, agent_type, model_path, print_info):
    if agent_type == "":
        print("agent_type not specified")
        return

    agent = make_agent(agent_type, model_path)

    msg = f"{agent_type}({model_path}) vs slumbot"

    start_time = time.perf_counter()
    winrate, mbbh = tournament_vs_slumbot(agent, hands, print_info)
    end_time = time.perf_counter()

    log.info(f'final, {msg}, winrate: {winrate :.1f}%, mbb/h: {mbbh :.1f}, run time: {end_time - start_time : .1f}')


if __name__ == '__main__':
    parser = argparse.ArgmentParser("Slumbot Test")
    parser.add_argument("--hands", type=int, default=1)
    parser.add_argument("--agent_type", type=str, default="")
    parser.add_argument("--model_path", type=str, default="")
    parser.add_argument("--print_info", type=bool, default=False)
    args = parser.parse_args()

    main(args.hands, args.agent_type, args.model_path, args.print_info)
