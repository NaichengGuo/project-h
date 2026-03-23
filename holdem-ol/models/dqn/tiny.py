import torch
import torch.nn as nn

from models.dqn.base import DqnBase, convert_state_param_to_device
from models.dqn.tiny_schema import TinySchema
from torch.nn import init
from models.nnx.fcl import Fcl

from models.consts import *
from models.dqn.consts import *
from models.nnx.pack import TsSeq
from models.transform.tranformv1 import TransformTinyV1


class Tiny(nn.Module, DqnBase):
    def __init__(self,
                 schema: TinySchema,
                 transform=None,
                 device: str = 'cpu',
                 argmax_action: bool = False):
        super(Tiny, self).__init__()
        DqnBase.__init__(self, argmax_action)
        self.comm_cards_lstm = nn.LSTM(input_size=schema.comm_cards_size,
                                       hidden_size=schema.comm_cards_hidden_size,
                                       batch_first=True)
        self.act_history_lstm = nn.LSTM(input_size=schema.act_trf_input_dim,
                                        hidden_size=schema.act_trf_hidden_dim,
                                        num_layers=schema.act_trf_num_layers,
                                        batch_first=True)
        fcl_input_size = schema.comm_cards_hidden_size + schema.act_trf_hidden_dim + schema.static_info_size
        self.advantage_fcl = Fcl(input_size=fcl_input_size,
                                 hidden_layers=schema.advantage_fcl_hidden_layers,
                                 output_size=schema.action_size)
        self.value_fcl = Fcl(input_size=fcl_input_size,
                             hidden_layers=schema.value_fcl_hidden_layers,
                             output_size=1)
        init.xavier_uniform_(self.comm_cards_lstm.weight_ih_l0)
        init.xavier_uniform_(self.comm_cards_lstm.weight_hh_l0)
        init.xavier_uniform_(self.act_history_lstm.weight_ih_l0)
        init.xavier_uniform_(self.act_history_lstm.weight_hh_l0)
        init.xavier_uniform_(self.act_history_lstm.weight_ih_l1)
        init.xavier_uniform_(self.act_history_lstm.weight_hh_l1)
        self.advantage_fcl.init_weights(init.xavier_uniform_)
        self.value_fcl.init_weights(init.xavier_uniform_)
        self.schema = schema
        if transform is None:
            self.transform = TransformTinyV1(schema)
        else:
            self.transform = transform
        self.ts_unpacker = TsSeq(self.schema.padding_value)
        self.device = device
        self.to(self.device)
        self.eval()

    def forward(self, state_tuple: tuple):
        # [batch_size, state_tuple]
        static_info, comm_cards_info, action_history_info = state_tuple
        self.comm_cards_lstm.flatten_parameters()
        self.act_history_lstm.flatten_parameters()
        # get batch size
        batch_size = static_info.size(0)
        comm_cards_output, _ = self.comm_cards_lstm(comm_cards_info)
        act_history_output, _ = self.act_history_lstm(action_history_info)
        if batch_size > 1:
            # unpack comm cards info
            comm_cards_output, _ = self.ts_unpacker.unpack(comm_cards_output)
            # unpack action history info
            act_history_output, _ = self.ts_unpacker.unpack(act_history_output)
        comm_cards_output = comm_cards_output[:, -1, :]
        act_history_output = act_history_output[:, -1, :]
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
        act_history_lstm_p = self.act_history_lstm.state_dict()
        advantage_fcl_p = self.advantage_fcl.state_dict()
        value_fcl_p = self.value_fcl.state_dict()
        if to_device is not None:
            comm_cards_lstm_p = convert_state_param_to_device(comm_cards_lstm_p, to_device)
            act_history_lstm_p = convert_state_param_to_device(act_history_lstm_p, to_device)
            advantage_fcl_p = convert_state_param_to_device(advantage_fcl_p, to_device)
            value_fcl_p = convert_state_param_to_device(value_fcl_p, to_device)
        p[COMM_CARD_LSTM] = comm_cards_lstm_p
        p[ACTS_LSTM] = act_history_lstm_p
        p[ADVANTAGE_FCL] = advantage_fcl_p
        p[VALUE_FCL] = value_fcl_p
        return p

    def set_parameters(self, parameters):
        """
        Args:
            parameters: network parameters
        """
        self.comm_cards_lstm.load_state_dict(parameters[COMM_CARD_LSTM])
        self.act_history_lstm.load_state_dict(parameters[ACTS_LSTM])
        self.advantage_fcl.load_state_dict(parameters[ADVANTAGE_FCL])
        self.value_fcl.load_state_dict(parameters[VALUE_FCL])

    def deep_clone(self):
        """
        Returns: deep clone of the network
        """
        clone = Tiny(self.schema, self.transform, self.device, self.argmax_action)
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
        p[ACTS_LSTM] = convert_state_param_to_device(parameters[ACTS_LSTM], to_device)
        p[ADVANTAGE_FCL] = convert_state_param_to_device(parameters[ADVANTAGE_FCL], to_device)
        p[VALUE_FCL] = convert_state_param_to_device(parameters[VALUE_FCL], to_device)
        return p

    @classmethod
    def get_model_type(cls):
        """
        Returns: model type
        """
        return DQN_TINY

    @classmethod
    def generate_schema(cls, dict_data: dict):
        """
        Returns: schema class
        """
        s = TinySchema()
        s.update(**dict_data)
        return s

    @classmethod
    def generate_transform(cls, schema):
        """
        Returns: model type
        """
        return TransformTinyV1(schema)
