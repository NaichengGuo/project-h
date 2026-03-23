import numpy as np
import torch.nn as nn
import torch

from core.coder.predict import PredictInput
from core.coder.state import State
from core.game.action import to_stage, Action
from core.game.card import CardCode
from core.utils.logger import log
from core.winrate.winrate_wrapper import WinrateWrapper
from models.agent.base.base_agent import BaseAgent


def to_obs(winrate, stage, pot, my_chips, other_chips, win_state):
    # obs(8) [winrate, stage, pot, my_chips, other_chips, i_win, i_loss]
    obs = np.zeros(10)
    obs[0] = float(winrate)
    state_one_hot = np.zeros(4)
    state_one_hot[stage] = 1
    obs[1:5] = state_one_hot
    obs[5] = float(pot)
    obs[6] = float(my_chips)
    obs[7] = float(other_chips)
    if win_state == 1:
        obs[8] = 1
    elif win_state == -1:
        obs[9] = 1
    return obs


def state_to_obs(state: State, reward, done: bool, winrate):
    public_cards = state.public_cards
    pot = state.pot / state.small_blind
    my_chips = state.my_remain_chips() / state.small_blind
    if done:
        if reward >= 0:
            win_state = 1
        else:
            win_state = -1
    else:
        win_state = 0

    other_chips = pot - my_chips
    stage = to_stage(len(public_cards))
    return to_obs(winrate, stage, pot, my_chips, other_chips, win_state)


class EstimatorNetwork(nn.Module):
    ''' The function approximation network for Estimator
        It is just a series of tanh layers. All in/out are torch.tensor
    '''

    def __init__(self, num_actions=2, state_shape=None, mlp_layers=None):
        ''' Initialize the Q network

        Args:
            num_actions (int): number of legal actions
            state_shape (list): shape of state tensor
            mlp_layers (list): output size of each fc layer
        '''
        super(EstimatorNetwork, self).__init__()

        self.num_actions = num_actions
        self.state_shape = state_shape
        self.mlp_layers = mlp_layers

        # build the Q network
        layer_dims = [np.prod(self.state_shape)] + self.mlp_layers
        fc = [nn.Flatten()]
        fc.append(nn.BatchNorm1d(layer_dims[0]))
        for i in range(len(layer_dims) - 1):
            fc.append(nn.Linear(layer_dims[i], layer_dims[i + 1], bias=True))
            fc.append(nn.ReLU())
        fc.append(nn.Linear(layer_dims[-1], self.num_actions, bias=True))
        self.fc_layers = nn.Sequential(*fc)

    def forward(self, s):
        ''' Predict action values

        Args:
            s  (Tensor): (batch, state_shape)
        '''
        return self.fc_layers(s)

    @staticmethod
    def restore(path):
        ''' Restore the model from file

        Args:
            path (str): path to the model file
        '''
        if torch.cuda.is_available():
            checkpoint = torch.load(path)
        else:
            checkpoint = torch.load(path, map_location=torch.device('cpu'))

        q_estimator = checkpoint['q_estimator']
        estimator = EstimatorNetwork(
            num_actions=q_estimator['num_actions'],
            state_shape=q_estimator['state_shape'],
            mlp_layers=q_estimator['mlp_layers'],
        )

        estimator.load_state_dict(q_estimator['qnet'])
        return estimator


class WinrateDqnTesting(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}
        device = config.get("device", "cpu")
        self.device = device

        model_path = config.get("model_path", "")
        if model_path == "":
            raise ValueError("model_path is empty")

        # log.info(f"load model from {model_path}")

        self.model_path = model_path
        self.model = EstimatorNetwork.restore(model_path)
        self.model.eval()
        self.win_rate_processor = WinrateWrapper()

    def step(self, state: State):
        return self.eval_step(state)

    def eval_step(self, state: State):
        hands = state.my_hand_cards
        public_cards = state.public_cards
        pot = state.pot / state.small_blind
        my_chips = state.my_chips_to_desk() / state.small_blind
        win_state = 0
        other_chips = pot - my_chips

        stage = state.get_cur_stage()
        winrate = self.win_rate_processor.get_winrate(hands, public_cards)
        obs = to_obs(winrate, stage, pot, my_chips, other_chips, win_state)

        action = self.predict(obs)
        return state.do_call_if_not_need_pay(Action(action))

    def predict(self, obs):
        obs = np.expand_dims(obs, 0)
        q_as = self.model_predict(obs)[0]
        best_action = np.argmax(q_as)
        return best_action

    def model_predict(self, s):
        with torch.no_grad():
            s = torch.from_numpy(s).float().to(self.device)
            q_as = self.model(s).cpu().numpy()
        return q_as

    def get_name(self):
        return f"winrate_dqn({self.model_path})"


if __name__ == "__main__":
    o = to_obs(0.85, 1, 1.1, 2, 3)
    print(o)
