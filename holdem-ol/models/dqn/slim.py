import torch
import torch.nn as nn

from models.dqn.base import DqnBase, convert_state_param_to_device
from models.dqn.slim_schema import SlimSchema
from models.nnx.transformer import TransformerEncoder
from torch.nn import init
from models.nnx.fcl import Fcl

from models.consts import *
from models.dqn.consts import *
from models.transform.tranformv1 import TransformSlimV1
from models.transform.transformv2 import TransformSlimV2


class Slim(nn.Module, DqnBase):
    def __init__(self,
                 schema: SlimSchema,
                 transform=None,
                 device: str = 'cpu',
                 argmax_action: bool = False):
        super(Slim, self).__init__()
        DqnBase.__init__(self, argmax_action)
        self.comm_cards_lstm = nn.LSTM(input_size=schema.comm_cards_size,
                                       hidden_size=schema.comm_cards_hidden_size,
                                       batch_first=True)
        self.acts_transformer = TransformerEncoder(input_dim=schema.act_trf_input_dim,
                                                   num_heads=schema.act_trf_num_heads,
                                                   hidden_size=schema.act_trf_hidden_dim,
                                                   num_layers=schema.act_trf_num_layers,
                                                   output_dim=schema.act_trf_output_dim,
                                                   padding_value=schema.padding_value,
                                                   use_padding_mask=schema.act_trf_use_padding_mask,
                                                   norm_first=schema.act_trf_norm_first,
                                                   max_len=schema.act_trf_max_len,
                                                   dropout=schema.act_trf_dropout)
        fcl_input_size = schema.comm_cards_hidden_size + schema.act_trf_output_dim + schema.static_info_size
        self.advantage_fcl = Fcl(input_size=fcl_input_size,
                                 hidden_layers=schema.advantage_fcl_hidden_layers,
                                 output_size=schema.action_size)
        self.value_fcl = Fcl(input_size=fcl_input_size,
                             hidden_layers=schema.value_fcl_hidden_layers,
                             output_size=1)
        init.xavier_uniform_(self.comm_cards_lstm.weight_ih_l0)
        init.xavier_uniform_(self.comm_cards_lstm.weight_hh_l0)
        self.advantage_fcl.init_weights(init.xavier_uniform_)
        self.value_fcl.init_weights(init.xavier_uniform_)
        self.schema = schema
        if transform is None:
            self.transform = self.generate_transform(schema)
        else:
            self.transform = transform
        self.device = device
        self.to(self.device)
        self.eval()

    def forward(self, state_tuple: tuple):
        # [batch_size, state_tuple]
        # [b,32,6] [b,4,1] [b,18]
        static_info, comm_cards_info, action_history_info = state_tuple
        self.comm_cards_lstm.flatten_parameters()
        comm_cards_output = self.comm_cards_lstm(comm_cards_info)[0][:, -1, :]
        act_history_output = self.acts_transformer(action_history_info)
        _input = torch.cat((static_info, comm_cards_output, act_history_output), dim=1)
        advantages = self.advantage_fcl(_input)
        values = self.value_fcl(_input)
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_values

    def schema_to_dict(self):
        """
        Returns: schema dict
        """
        return self.schema.to_dict()

    def get_parameters(self, to_device=None):
        """
        Returns: network parameters
        """
        p = dict()
        comm_cards_lstm_p = self.comm_cards_lstm.state_dict()
        acts_transformer_p = self.acts_transformer.state_dict()
        advantage_fcl_p = self.advantage_fcl.state_dict()
        value_fcl_p = self.value_fcl.state_dict()
        if to_device is not None:
            comm_cards_lstm_p = convert_state_param_to_device(comm_cards_lstm_p, to_device)
            acts_transformer_p = convert_state_param_to_device(acts_transformer_p, to_device)
            advantage_fcl_p = convert_state_param_to_device(advantage_fcl_p, to_device)
            value_fcl_p = convert_state_param_to_device(value_fcl_p, to_device)
        p[COMM_CARD_LSTM] = comm_cards_lstm_p
        p[ACTS_TRANSFORMER] = acts_transformer_p
        p[ADVANTAGE_FCL] = advantage_fcl_p
        p[VALUE_FCL] = value_fcl_p
        return p

    def set_parameters(self, parameters):
        """
        Args:
            parameters: network parameters
        """
        self.comm_cards_lstm.load_state_dict(parameters[COMM_CARD_LSTM])
        self.acts_transformer.load_state_dict(parameters[ACTS_TRANSFORMER])
        self.advantage_fcl.load_state_dict(parameters[ADVANTAGE_FCL])
        self.value_fcl.load_state_dict(parameters[VALUE_FCL])
        self.to(self.device)

    def to(self, device):
        """
        Args:
            device: device
        """
        self.comm_cards_lstm.to(device)
        self.acts_transformer.to(device)
        self.advantage_fcl.to(device)
        self.value_fcl.to(device)
        return self

    def deep_clone(self):
        """
        Returns: deep clone of the network
        """
        clone = Slim(self.schema, self.transform, self.device, self.argmax_action)
        clone.set_parameters(self.get_parameters())
        return clone

    @classmethod
    def convert_parameters(cls, parameters, to_device: str):
        """
        Args:
            parameters: network parameters
            to_device: device
        Returns: converted parameters
        """
        p = dict()
        p[COMM_CARD_LSTM] = convert_state_param_to_device(parameters[COMM_CARD_LSTM], to_device)
        p[ACTS_TRANSFORMER] = convert_state_param_to_device(parameters[ACTS_TRANSFORMER], to_device)
        p[ADVANTAGE_FCL] = convert_state_param_to_device(parameters[ADVANTAGE_FCL], to_device)
        p[VALUE_FCL] = convert_state_param_to_device(parameters[VALUE_FCL], to_device)
        return p

    @classmethod
    def get_model_type(cls):
        """
        Returns: model type
        """
        return DQN_SLIM

    @classmethod
    def generate_schema(cls, dict_data: dict):
        """
        Returns: schema class
        """
        s = SlimSchema()
        s.update(**dict_data)
        return s

    @classmethod
    def generate_transform(cls, schema):
        """
        Returns: model type
        """
        transform_version = schema.transform_version
        if transform_version == 'v1':
            return TransformSlimV1(schema)
        elif transform_version == 'v2':
            return TransformSlimV2(schema)
        else:
            raise ValueError(f"Unknown transform version: {transform_version}")
