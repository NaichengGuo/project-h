import torch.nn as nn
from torch.nn import init

from models.consts import DQN_TINY_MIX
from models.dqn.base import DqnBase
from models.dqn.tiny import Tiny
from models.dqn.tiny_schema import TinyMixSchema
from models.nnx.fcl import Fcl
from models.nnx.pack import TsSeq
from models.transform.tranformv1 import TransformTinyExtraV1


class TinyMix(Tiny):
    """
    Mix model
    Attributes:
        inference_mode: bool, whether in inference mode
        min_us_size: int, min user statics size
        max_us_size: int, max user statics size
    """
    inference_mode: bool = False
    min_us_size: int
    max_us_size: int

    def __init__(self,
                 schema: TinyMixSchema,
                 transform: TransformTinyExtraV1 = None,
                 device='cpu',
                 argmax_action=False):
        nn.Module.__init__(self)
        DqnBase.__init__(self, argmax_action)
        self.comm_cards_lstm = nn.LSTM(input_size=schema.comm_cards_size,
                                       hidden_size=schema.comm_cards_hidden_size,
                                       batch_first=True)
        self.act_history_lstm = nn.LSTM(input_size=schema.act_trf_input_dim,
                                        hidden_size=schema.act_trf_hidden_dim,
                                        num_layers=schema.act_trf_num_layers,
                                        batch_first=True)
        fcl_input_size = (schema.comm_cards_hidden_size + schema.act_trf_hidden_dim + schema.static_info_size
                          + schema.player_num * schema.user_statics_info_size)
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
            self.transform = TransformTinyExtraV1(schema)
        else:
            self.transform = transform
        self.ts_unpacker = TsSeq(self.schema.padding_value)
        self.device = device
        self.to(self.device)
        self.eval()

    def deep_clone(self):
        clone = TinyMix(self.schema, self.transform, self.device, self.argmax_action)
        clone.set_parameters(self.get_parameters())
        return clone

    @classmethod
    def get_model_type(cls):
        """
        Returns: model type
        """
        return DQN_TINY_MIX

    @classmethod
    def generate_schema(cls, dict_data: dict):
        """
        Returns: schema class
        """
        s = TinyMixSchema()
        s.update(**dict_data)
        return s

    @classmethod
    def generate_transform(cls, schema):
        """
        Returns: model type
        """
        return TransformTinyExtraV1(schema)
