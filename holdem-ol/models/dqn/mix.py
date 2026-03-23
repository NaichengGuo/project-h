import torch.nn as nn
from torch.nn import init

from models.consts import DQN_MIX
from models.dqn.base import DqnBase
from models.dqn.slim import Slim
from models.dqn.slim_schema import MixSchema
from models.nnx.fcl import Fcl
from models.nnx.transformer import TransformerEncoder
from models.transform.tranformv1 import TransformSlimExtraV1


class Mix(Slim):
    def __init__(self,
                 schema: MixSchema,
                 transform: TransformSlimExtraV1 = None,
                 device='cpu',
                 argmax_action=False):
        nn.Module.__init__(self)
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
        fcl_input_size = (schema.comm_cards_hidden_size + schema.act_trf_output_dim + schema.static_info_size + schema.player_num * schema.user_statics_info_size)
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
            self.transform = TransformSlimExtraV1(schema)
        else:
            self.transform = transform
        self.device = device
        self.to(self.device)
        self.eval()

    def deep_clone(self):
        clone = Mix(self.schema, self.transform, self.device, self.argmax_action)
        clone.set_parameters(self.get_parameters())
        return clone

    @classmethod
    def get_model_type(cls):
        """
        Returns: model type
        """
        return DQN_MIX

    @classmethod
    def generate_schema(cls, dict_data: dict):
        """
        Returns: schema class
        """
        s = MixSchema()
        s.update(**dict_data)
        return s

    @classmethod
    def generate_transform(cls, schema):
        """
        Returns: model type
        """
        return TransformSlimExtraV1(schema)
