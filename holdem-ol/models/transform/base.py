import numpy as np
import torch

from core.game.game_base import GameType
from core.utils.numpy_util import feed_matrix
from core.winrate.simplify_wr import ValueEstimator
from core.winrate.srv_card import WinRateDocker, ShortWinRateDocker
from core.winrate.winrate_processer import WinRateProcessor
ACTION_MASK_PADDING = 0


class BaseTransform(object):
    """
    Transform the raw state to the input of the model
    """

    def __init__(self, schema):
        self.action_size = schema.action_size
        self.static_base_info_dim = schema.get_static_base_info_dim()
        self.static_info_whole_dim = self.static_base_info_dim
        self.comm_card_dim = schema.comm_cards_size
        self.action_history_dim = schema.act_trf_input_dim
        self.padding_value = schema.padding_value
        #self.win_rate_docker = WinRateProcessor()
        self.win_rate_docker = ValueEstimator()
        #self.win_rate_docker = WinRateDocker()
        #self.short_rate_docker = ShortWinRateDocker()

    def convert_state_to_full_info(self, state, device: str):
        """
        Convert the raw state to the input of the model
        :param state: raw state
        :param device: device
        :return: game limitation, trajectory state, inference state
                 返回 游戏限制(包括动作掩码或动作代价)/弹道格式/推理格式
        """
        state_info = self.convert_general_state(state)
        trajectory_state = (state_info.static_info, state_info.comm_cards_info, state_info.action_history_info)
        return self.warp_full_state_info(state_info, trajectory_state, device)

    def convert_state_to_inference(self, state, device: str) -> (np.array, tuple):
        """
        Convert the raw state to the input of the model
        :param state: raw state
        :param device: device
        :return: action_mask, inference state
                 返回 动作掩码/推理格式
        """
        state_info = self.convert_inference_state(state)
        return self.wrap_inference_info(state_info, device)

    def convert_action_mask(self, state) -> np.array:
        """
        Convert the action mask
        :param state: raw state
        :return: action mask
        """
        action_mask = np.zeros(self.action_size, dtype=np.int8)
        for action in state.legal_actions:
            action_mask[action] = 1
        return action_mask

    def convert_action_mask_and_cost(self, state) -> (np.array, np.array):
        """
        Convert the action mask and cost
        :param state: raw state
        :return: action mask and cost
        [action_mask1, action_mask2, ..., action_maskN, action_cost1, action_cost2, ..., action_costN]
        """
        action_mask = np.zeros(self.action_size, dtype=np.int8)
        action_cost = np.full(self.action_size, ACTION_MASK_PADDING, dtype=np.float32)
        legal_actions, legal_actions_cost = state.calc_legal_actions()
        for i, action in enumerate(legal_actions):
            action_mask[action] = 1
            action_cost[action] = legal_actions_cost[i] / state.small_blind
        return action_mask, action_cost

    def convert_static_info(self, state) -> np.array:
        """
        Convert the static info
        :param state: raw state
        :return: static info
        """
        static_info = np.zeros(self.static_info_whole_dim, dtype=np.float32)
        self.feed_static_base_info(state, static_info)
        self.feed_static_extra_info(state, static_info)
        return static_info

    def convert_static_info_v2(self, state, action_mask, action_cost):
        static_info = np.zeros(self.static_info_whole_dim, dtype=np.float32)
        self.feed_static_base_info(state, static_info)
        self.feed_action_info_into_static_info(action_mask, action_cost, static_info)
        self.feed_static_extra_info(state, static_info)
        return static_info

    def convert_comm_cards_info(self, state) -> np.array:
        """
        Convert the community cards info
        :param state: raw state
        :return: community cards info
        """
        cards = state.my_hand_cards + state.public_cards
        size = len(cards)
        # if state.game_type == GameType.SHORT:
        #     win_rate_docker = self.short_rate_docker
        # else:
            #win_rate_docker = self.win_rate_docker
        if size == 7:
            comm_cards_info = np.zeros((4, self.comm_card_dim), dtype=np.float32)
            comm_cards_info[0][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:2])
            comm_cards_info[1][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:5])
            comm_cards_info[2][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:6])
            comm_cards_info[3][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards)
            # comm_cards_info[0][0] = win_rate_docker.win_rate_by_two_str(cards[:2])
            # comm_cards_info[1][0] = win_rate_docker.win_rate_by_str(cards[:5])
            # comm_cards_info[2][0] = win_rate_docker.win_rate_by_str(cards[:6])
            # comm_cards_info[3][0] = win_rate_docker.win_rate_by_str(cards)
        elif size == 6:
            comm_cards_info = np.zeros((3, self.comm_card_dim), dtype=np.float32)
            comm_cards_info[0][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:2])
            comm_cards_info[1][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:5])
            comm_cards_info[2][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards)
            # comm_cards_info[0][0] = win_rate_docker.win_rate_by_two_str(cards[:2])
            # comm_cards_info[1][0] = win_rate_docker.win_rate_by_str(cards[:5])
            # comm_cards_info[2][0] = win_rate_docker.win_rate_by_str(cards)
        elif size == 5:
            comm_cards_info = np.zeros((2, self.comm_card_dim), dtype=np.float32)
            comm_cards_info[0][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards[:2])
            comm_cards_info[1][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards)
            # comm_cards_info[0][0] = win_rate_docker.win_rate_by_two_str(cards[:2])
            # comm_cards_info[1][0] = win_rate_docker.win_rate_by_str(cards)
        elif size == 2:
            comm_cards_info = np.zeros((1, self.comm_card_dim), dtype=np.float32)
            comm_cards_info[0][0] = self.win_rate_docker.calculate_heuristic_win_prob(cards)
            #comm_cards_info[0][0] = win_rate_docker.win_rate_by_two_str(cards)
        else:
            raise ValueError(f"Invalid card size: {size}")
        return comm_cards_info

    def convert_action_history_info(self, state) -> np.array:
        """
        Convert the action history info
        :param state: raw state
        :return: action history info
        """
        act_history_size = len(state.actions)
        action_history_info = np.zeros((act_history_size, self.action_history_dim), dtype=np.float32)
        for idx, action in enumerate(state.actions):
            action_history_info[idx][0] = action.player_id #玩家id
            action_history_info[idx][1] = action.stage #阶段
            action_history_info[idx][2] = simplify_action(action.action) #动作
            action_history_info[idx][3] = action.num / state.small_blind #押注
            action_history_info[idx][4] = action.after_remain_chips / state.small_blind #玩家剩余筹码
            action_history_info[idx][5] = action.after_pot / state.small_blind #奖池
        return action_history_info

    def wrap_inference_state(self, state_info, device: str):
        static_info_input = np.expand_dims(state_info.static_info, axis=0)
        comm_cards_info_input = self.wrap_comm_cards_info_input(state_info.comm_cards_info)
        action_history_info_input = self.wrap_action_history_info_input(state_info.action_history_info)
        inference_state = (torch.from_numpy(static_info_input).to(dtype=torch.float32, device=device),
                           torch.from_numpy(comm_cards_info_input).to(dtype=torch.float32, device=device),
                           torch.from_numpy(action_history_info_input).to(dtype=torch.float32, device=device))
        return inference_state

    def convert_save_state_for_training(self, ds: list[tuple], device: str):
        raise NotImplementedError

    def convert_general_state(self, state):
        raise NotImplementedError

    def convert_inference_state(self, state):
        raise NotImplementedError

    def warp_full_state_info(self, state_info, trajectory_state, device: str):
        raise NotImplementedError

    def wrap_inference_info(self, state_info, device: str):
        raise NotImplementedError

    def wrap_comm_cards_info_input(self, comm_cards_info):
        raise NotImplementedError

    def wrap_action_history_info_input(self, action_history_info):
        raise NotImplementedError

    def feed_static_base_info(self, state, static_info: np.array):
        raise NotImplementedError

    def feed_static_extra_info(self, state, static_info: np.array):
        pass

    def feed_action_info_into_static_info(self, action_mask, action_cost, static_info: np.array):
        raise NotImplementedError


class BasePaddingTransform(BaseTransform):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)
        self.comm_card_series_size = 4
        self.action_history_max_size = schema.act_trf_max_len
        self.comm_card_padding = np.full((self.comm_card_series_size, self.comm_card_dim),
                                         self.padding_value, dtype=np.float32)
        self.action_history_padding = np.full((self.action_history_max_size, self.action_history_dim),
                                              self.padding_value, dtype=np.float32)

    def wrap_comm_cards_info_input(self, comm_cards_info):
        _comm_cards_info = self.padding_comm_cards_info(comm_cards_info)
        return np.expand_dims(_comm_cards_info, axis=0)

    def wrap_action_history_info_input(self, action_history_info):
        _action_history_info = self.padding_action_history_info(action_history_info)
        return np.expand_dims(_action_history_info, axis=0)

    def convert_save_state_for_training(self, ds: list[tuple], device: str):
        """
        Convert the raw state to the input of the model for training
        :param ds: raw state list
        :param device: device
        :return: input tuple
        """
        batch_size = len(ds)
        batch_static_info = np.zeros((batch_size, self.static_info_whole_dim), dtype=np.float32)
        batch_comm_cards_info = np.zeros(
            (batch_size, self.comm_card_series_size, self.comm_card_dim), dtype=np.float32)
        batch_action_history_info = np.zeros(
            (batch_size, self.action_history_max_size, self.action_history_dim), dtype=np.float32)
        for idx, trajectory_state in enumerate(ds):
            static_info, comm_cards_info, action_history_info = trajectory_state
            batch_static_info[idx] = static_info[:self.static_info_whole_dim]
            batch_comm_cards_info[idx] = self.padding_comm_cards_info(comm_cards_info)
            batch_action_history_info[idx] = self.padding_action_history_info(action_history_info)
        batch_static_info_tensor = torch.tensor(batch_static_info, dtype=torch.float32, device=device)
        batch_comm_cards_info_tensor = torch.tensor(batch_comm_cards_info, dtype=torch.float32, device=device)
        batch_action_history_info_tensor = torch.tensor(batch_action_history_info, dtype=torch.float32, device=device)
        return batch_static_info_tensor, batch_comm_cards_info_tensor, batch_action_history_info_tensor

    def padding_comm_cards_info(self, comm_cards_info):
        dst = self.comm_card_padding.copy()
        return feed_matrix(comm_cards_info, dst)

    def padding_action_history_info(self, action_history_info):
        dst = self.action_history_padding.copy()
        return feed_matrix(action_history_info, dst)


def gen_padding_transform_cls(cls):
    """
    Args:
        cls: class, base class
    Returns:
        Mixin class
    """

    class PaddingTransform(cls, BasePaddingTransform):
        def __init__(self, schema):
            BasePaddingTransform.__init__(self, schema)

        def wrap_comm_cards_info_input(self, comm_cards_info):
            return BasePaddingTransform.wrap_comm_cards_info_input(self, comm_cards_info)

        def wrap_action_history_info_input(self, action_history_info):
            return BasePaddingTransform.wrap_action_history_info_input(self, action_history_info)

        def convert_save_state_for_training(self, ds: list[tuple], device: str):
            return BasePaddingTransform.convert_save_state_for_training(self, ds, device)

    return PaddingTransform


def gen_extra_transform_cls(base_cls, extra_cls):
    """
    Args:
        base_cls: class, base class
        extra_cls: class, extra class
    Returns:
        Mixin class
    """

    class ExtraTransform(base_cls, extra_cls):
        def __init__(self, schema):
            extra_cls.__init__(self, schema)

        def convert_static_info(self, state) -> np.array:
            return extra_cls.convert_static_info(self, state)

        def convert_inference_state(self, state):
            return extra_cls.convert_inference_state(self, state)

        def feed_static_extra_info(self, state, static_info: np.array):
            extra_cls.feed_static_extra_info(self, state, static_info)

    return ExtraTransform


def simplify_action(action: int) -> int:
    """
    Args:
        action: int, action value
    Returns:
        int, simplified action value(-1:强制下注, 0:弃牌, 1:跟注或加注)
    """
    if action < 0:
        # 强制下注
        return -1
    if action == 0:
        # 弃牌
        return 0
    # 跟注或加注
    return 1
