import torch
import torch.nn as nn

from models.nnx.fcl import Fcl
from models.ppo.base import PpoBase, convert_state_param_to_device
from models.ppo.consts import *
from models.transform.transformv2 import TransformV2Base
from models.consts import *


class SlimSchema(object):
    def __init__(self):
        self.player_num = 6
        self.static_info_size = 2 + 8 * 2  # dealer_id, my_id, action_mask, action_cost
        self.comm_cards_size = 5 * 4  # 5 cards, 4 features per card
        self.act_trf_input_dim = 6 * 3  # 6 players, 3 features per player
        self.padding_value = -1
        self.action_size = 8  # Number of possible actions

    def get_static_base_info_dim(self):
        return self.static_info_size

    def get_static_extra_info_dim(self):
        return self.player_num * USER_STATICS_INFO_SIZE


class SlimPPO(PpoBase):
    def __init__(self, schema=None, transform=None, device='cpu', **kwargs):
        super(SlimPPO, self).__init__(**kwargs)
        self.schema = schema if schema is not None else SlimSchema()
        self.transform = transform if transform is not None else TransformV2Base(self.schema)
        self.device = device

        # Define network dimensions
        static_dim = self.schema.get_static_base_info_dim() + self.schema.get_static_extra_info_dim()
        comm_cards_dim = self.schema.comm_cards_size
        action_history_dim = self.schema.act_trf_input_dim
        input_dim = static_dim + comm_cards_dim + action_history_dim
        hidden_dim = [256, 128, 64]
        action_dim = self.schema.action_size
        value_dim = 1

        # Actor network (policy)
        self.actor = Fcl(input_dim, hidden_dim, action_dim, name='actor')
        self.actor.to(device)

        # Critic network (value function)
        self.critic = Fcl(input_dim, hidden_dim, value_dim, name='critic')
        self.critic.to(device)

    def forward_actor(self, state):
        """
        Forward pass through the actor network
        Args:
            state: state info (static_info, comm_cards_info, action_history_info)
        Returns: action logits
        """
        static_info = state['static_info']
        comm_cards_info = state['comm_cards_info']
        action_history_info = state['action_history_info']

        # Concatenate all inputs
        x = torch.cat([static_info, comm_cards_info, action_history_info], dim=1)
        return self.actor(x)

    def forward_critic(self, state):
        """
        Forward pass through the critic network
        Args:
            state: state info (static_info, comm_cards_info, action_history_info)
        Returns: state value
        """
        static_info = state['static_info']
        comm_cards_info = state['comm_cards_info']
        action_history_info = state['action_history_info']

        # Concatenate all inputs
        x = torch.cat([static_info, comm_cards_info, action_history_info], dim=1)
        return self.critic(x)

    def schema_to_dict(self):
        """
        Convert schema to dict
        Returns: schema dict
        """
        return {
            'player_num': self.schema.player_num,
            'static_info_size': self.schema.static_info_size,
            'comm_cards_size': self.schema.comm_cards_size,
            'act_trf_input_dim': self.schema.act_trf_input_dim,
            'padding_value': self.schema.padding_value,
            'action_size': self.schema.action_size
        }

    def get_parameters(self, to_device=None):
        """
        Get model parameters
        Args:
            to_device: device to move parameters to
        Returns: model parameters
        """
        device = to_device if to_device is not None else self.device
        return {
            ACTOR_KEY: self.actor.state_dict(),
            CRITIC_KEY: self.critic.state_dict()
        }

    def set_parameters(self, parameters):
        """
        Set model parameters
        Args:
            parameters: model parameters
        """
        if ACTOR_KEY in parameters:
            self.actor.load_state_dict(parameters[ACTOR_KEY])
        if CRITIC_KEY in parameters:
            self.critic.load_state_dict(parameters[CRITIC_KEY])

    @classmethod
    def convert_parameters(cls, parameters, to_device: str):
        """
        Convert parameters to device
        Args:
            parameters: model parameters
            to_device: device
        Returns: converted parameters
        """
        result = {}
        if ACTOR_KEY in parameters:
            result[ACTOR_KEY] = {k: v.to(to_device) for k, v in parameters[ACTOR_KEY].items()}
        if CRITIC_KEY in parameters:
            result[CRITIC_KEY] = {k: v.to(to_device) for k, v in parameters[CRITIC_KEY].items()}
        return result

    @classmethod
    def get_model_type(cls):
        """
        Get model type
        Returns: model type
        """
        return 'slim_ppo'

    @classmethod
    def generate_schema(cls, dict_data: dict):
        """
        Generate schema from dict
        Args:
            dict_data: schema dict
        Returns: schema
        """
        schema = SlimSchema()
        schema.player_num = dict_data.get('player_num', 6)
        schema.static_info_size = dict_data.get('static_info_size', 2 + 8 * 2)
        schema.comm_cards_size = dict_data.get('comm_cards_size', 5 * 4)
        schema.act_trf_input_dim = dict_data.get('act_trf_input_dim', 6 * 3)
        schema.padding_value = dict_data.get('padding_value', -1)
        schema.action_size = dict_data.get('action_size', 8)
        return schema

    @classmethod
    def generate_transform(cls, schema):
        """
        Generate transform from schema
        Args:
            schema: schema
        Returns: transform
        """
        return TransformV2Base(schema)

    def wrap_inference_state(self, state_info, device: str):
        """
        Wrap state info for inference
        Args:
            state_info: state info
            device: device
        Returns: inference state
        """
        static_info = torch.from_numpy(state_info.static_info).float().unsqueeze(0).to(device)
        comm_cards_info = torch.from_numpy(state_info.comm_cards_info).float().unsqueeze(0).to(device)
        action_history_info = torch.from_numpy(state_info.action_history_info).float().unsqueeze(0).to(device)

        return {
            'static_info': static_info,
            'comm_cards_info': comm_cards_info,
            'action_history_info': action_history_info
        }