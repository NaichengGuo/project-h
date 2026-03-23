import argparse
import boto3
import json
import numpy as np
import traceback
import sys
import os

# Add parent directory to path to find modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.coder.state import State, print_actions
from core.utils.logger import print_red
from core.game.action import Action
from models.agent.base.base_agent import BaseAgent
from models.agent.simple.human_agent import HumanAgent
from rlcard.envs.holdem_env import HoldemEnv
from rlcard.utils import print_card

# SageMaker Agent
class SageMakerAgent(BaseAgent):
    def __init__(self, endpoint_name, model_name=None):
        super().__init__()
        self.endpoint_name = endpoint_name
        self.model_name = model_name
        self.runtime_client = boto3.client('sagemaker-runtime')
        print(f"Initialized SageMakerAgent with endpoint: {endpoint_name}")

    def step(self, state: State):
        return self.eval_step(state)

    def eval_step(self, state: State):
        # Prepare input payload for SageMaker endpoint
        # The endpoint expects {'inputs': {...}, 'params': {...}}
        
        # We need to construct the input dictionary carefully
        input_data = {
            'inputs': state.to_dict(),
            'params': {
                'return_rl_action': True, # Request the RL action index (0-7)
                'on_game_start': False
            }
        }
        if self.model_name:
            input_data["params"]["model_name"] = self.model_name
        
        print(f"Invoking SageMaker endpoint {self.endpoint_name} with input: {input_data}")
        try:
            # Invoke SageMaker endpoint
            response = self.runtime_client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(input_data)
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            
            # The result structure from our inference code is {'predictions': {'action': ..., 'num': ...}}
            predictions = result.get('predictions', {})
            
            # We requested return_rl_action=True, so 'action' should be the RL action index (0-7)
            action = predictions.get('action')
            
            # Basic validation
            if action is None:
                print_red("Warning: SageMaker response missing 'action' field. Defaulting to FOLD.")
                return Action.FOLD.value
                
            return int(action)
            
        except Exception as e:
            print_red(f"Error invoking SageMaker endpoint: {e}")
            traceback.print_exc()
            return Action.FOLD.value

def main(endpoint_name, num_players=2, region_name="us-east-1", model_name=None):
    # Initialize agents
    # 1 Human Agent (me)
    # N-1 SageMaker Agents (opponents)
    
    print(f"Starting Hold'em Human vs SageMaker (Endpoint: {endpoint_name})")
    
    sagemaker_agent = SageMakerAgent(endpoint_name, model_name=model_name)
    
    # Create opponent list
    opponents = [sagemaker_agent for _ in range(num_players - 1)]
    
    # Setup environment
    env = HoldemEnv({'num_players': num_players})
    
    human_agent = HumanAgent()
    
    # In HoldemEnv, agents are set in order. 
    # Usually position 0 is relative to the dealer button rotation.
    # We will put the human agent at index 0.
    env.set_agents([human_agent] + opponents)
    
    total_payoff = 0
    round_count = 0
    
    while True:
        round_count += 1
        print(f"\n>> ------------- Start Game (Round {round_count}) --------------")
        
        # Run one episode (hand)
        # is_training=False ensures eval_step is called
        trajectories, payoffs = env.run(is_training=False)
        
        # Update total payoff for human agent (index 0)
        # payoffs is a list of payoffs for each player
        current_payoff = payoffs[0]
        total_payoff += current_payoff
        
        # Get final states for display
        if trajectories and len(trajectories) > 0 and len(trajectories[0]) > 0:
            my_last_state: State = trajectories[0][-1]
            
            print('\n===============     Result     ===============')
            print("My cards:")
            print_card(my_last_state.my_hand_cards)
            
            # Show opponent cards
            for i in range(1, num_players):
                if len(trajectories) > i and len(trajectories[i]) > 0:
                    oppo_state = trajectories[i][-1]
                    print(f"Opponent {i} cards:")
                    print_card(oppo_state.my_hand_cards)
            
            print("Public cards:")
            if len(my_last_state.public_cards) > 0:
                print_card(my_last_state.public_cards)
            else:
                print("[]")
                
            # Show history of actions from perspective of human agent
            print('Action History:')
            # print_actions expects (actions, my_id)
            print_actions(my_last_state.actions, my_last_state.my_id)
        
        print_red(f"Round Payoff: {current_payoff}, Total Payoff: {total_payoff}")

        # Ask to continue
        choice = input('>> Start new game? (y/n): ').lower().strip()
        if choice != 'y':
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Holdem against SageMaker Agent")
    parser.add_argument("--endpoint_name", type=str, required=True, help="SageMaker Endpoint Name")
    parser.add_argument("--num_players", type=int, default=2, help="Number of players (default: 2)")
    parser.add_argument("--model_name", type=str, default=None, help="Model name to route to (optional)")
    args = parser.parse_args()
    
    try:
        main(args.endpoint_name, num_players=args.num_players, model_name=args.model_name)
    except KeyboardInterrupt:
        print("\nGame interrupted.")
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
