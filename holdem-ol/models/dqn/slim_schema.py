from models.dqn.base import BaseSchema


class SlimSchema(BaseSchema):
    def __init__(self):
        """
        Just init
        """
        BaseSchema.__init__(self)
        self.advantage_fcl_hidden_layers = []
        self.value_fcl_hidden_layers = []
        self.action_size = 0
        self.comm_cards_size = 0
        self.comm_cards_hidden_size = 0
        self.padding_value = 0
        self.act_trf_input_dim = 0
        self.act_trf_hidden_dim = 0
        self.act_trf_output_dim = 0
        self.act_trf_num_heads = 0
        self.act_trf_num_layers = 0
        self.act_trf_use_padding_mask = False
        self.act_trf_norm_first = False
        self.act_trf_max_len = 0
        self.act_trf_dropout = 0.0
        self.transform_version = 'v1'


class MixSchema(BaseSchema):
    def __init__(self):
        """
        Just init
        """
        BaseSchema.__init__(self)
        self.advantage_fcl_hidden_layers = []
        self.value_fcl_hidden_layers = []
        self.action_size = 0
        self.comm_cards_size = 0
        self.comm_cards_hidden_size = 0
        self.padding_value = 0
        self.act_trf_input_dim = 0
        self.act_trf_hidden_dim = 0
        self.act_trf_output_dim = 0
        self.act_trf_num_heads = 0
        self.act_trf_num_layers = 0
        self.act_trf_use_padding_mask = False
        self.act_trf_norm_first = False
        self.act_trf_max_len = 0
        self.act_trf_dropout = 0.0
        self.user_statics_info_size = 0
        self.min_us_size = 0
        self.max_us_size = 0
