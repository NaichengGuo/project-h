from core.utils.collection import DDict
from models.dqn.base import BaseSchema
from models.dqn.consts import USER_STATICS_INFO_SIZE


class TinySchema(BaseSchema):
    def __init__(self):
        """
        Just init
        """
        self.advantage_fcl_hidden_layers = []
        self.value_fcl_hidden_layers = []
        self.player_num = 0
        self.static_info_size = 0
        self.action_size = 0
        self.comm_cards_size = 0
        self.comm_cards_hidden_size = 0
        self.padding_value = 0
        self.act_trf_input_dim = 0
        self.act_trf_hidden_dim = 0
        self.act_trf_num_layers = 0


class TinyMixSchema(BaseSchema):
    def __init__(self):
        """
        Just init
        """
        self.advantage_fcl_hidden_layers = []
        self.value_fcl_hidden_layers = []
        self.player_num = 0
        self.static_info_size = 0
        self.action_size = 0
        self.comm_cards_size = 0
        self.comm_cards_hidden_size = 0
        self.padding_value = 0
        self.act_trf_input_dim = 0
        self.act_trf_hidden_dim = 0
        self.act_trf_num_layers = 0
        self.user_statics_info_size = 0
        self.min_us_size = 0
        self.max_us_size = 0
