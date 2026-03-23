import argparse
from core.coder.state import State, print_actions
from core.utils.logger import print_red
from models.agent.manager import make_agent
from models.agent.simple.human_agent import HumanAgent
from rlcard.envs.holdem_env import HoldemEnv
from rlcard.utils import print_card


def main(agent_type, model_path, num_players=2):
    oppoli  = [make_agent(agent_type, {"model_path": model_path,}) for _ in range(num_players-1)] 
    # oppoli.append(make_agent('ev_v1_aggressive'))
    # oppoli.append(make_agent('ev_v2_neutral'))
    # num_players+=2
    env = HoldemEnv({'num_players':num_players})
   

    human_agent = HumanAgent()
    env.set_agents([human_agent]+oppoli)
    total_payoff = 0
    round_count = 0
    start_new_game = 'y'
    while start_new_game == 'y':
        print(">> -------------Start a new game--------------")
        round_count += 1
        trajectories, payoffs = env.run(is_training=False)
        total_payoff += payoffs[0]
        my_last_state: State = trajectories[0][-1]
        oppo_last_state: State = trajectories[1][-1]

        print('===============     Result     ===============')
        print("my cards:")
        print_card(my_last_state.my_hand_cards)
        print("opponent cards:")
        print_card(oppo_last_state.my_hand_cards)
        print("public cards:")
        if len(my_last_state.public_cards) != 0:
            print_card(my_last_state.public_cards)
        print('history actions:')
        print_actions(oppo_last_state.actions, my_last_state.my_id)
        print_red(f"payoff: {payoffs[0]}, total_payoff: {total_payoff}, round_count: {round_count}")

        start_new_game = input('>> Start new game?(y/n): ')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_type", type=str, default="prob_conservative_v1_250909")
    parser.add_argument("--model_path", type=str, default="./board3_5.pkl")
    parser.add_argument("--num_players", type=int, default=2)
    args = parser.parse_args()
    main(args.agent_type, args.model_path, num_players=args.num_players)
