import argparse
from testing.run_env import evaluate
from core.game.action import Action
from models.agent.manager import make_agent


def main():
    parser = argparse.ArgumentParser("Ability Test")
    parser.add_argument("--agent0", type=str, default="")
    parser.add_argument("--agent1", type=str, default="")
    parser.add_argument("--model_path_0", type=str, default="")
    parser.add_argument("--model_path_1", type=str, default="")
    parser.add_argument("--round_count", type=int, default=10)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    if args.agent0 == "":
        print("agent 0 not specified")
        return
    if args.agent1 == "":
        print("agent 1 not specified")
        return

    config0 = {
        'model_path': args.model_path_0,
        'device': args.device,
    }
    config1 = {
        'model_path': args.model_path_1,
        'device': args.device,
    }
    agent0 = make_agent(args.agent0, config0)
    agent1 = make_agent(args.agent1, config1)

    agents = [agent0, agent1]
    if hasattr(agent0, 'get_name'):
        msg1 = agent0.get_name()
    else:
        msg1 = f"{args.agent0}({args.model_path_0})"

    if hasattr(agent1, 'get_name'):
        msg2 = agent1.get_name()
    else:
        msg2 = f"{args.agent1}({args.model_path_1})"

    evaluate(f"{msg1} vs {msg2}", agents, args.round_count)


if __name__ == '__main__':
    main()
