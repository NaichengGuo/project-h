from models.ppo.base import BaseSchema


class SlimSchema(BaseSchema):
    def __init__(self):
        super(SlimSchema, self).__init__()
        self.player_num = 6
        self.static_info_size = 2 + 8 * 2  # dealer_id, my_id, action_mask, action_cost
        self.comm_cards_size = 5 * 4  # 5 cards, 4 features per card
        self.act_trf_input_dim = 6 * 3  # 6 players, 3 features per player
        self.padding_value = -1
        self.action_size = 8  # Number of possible actions