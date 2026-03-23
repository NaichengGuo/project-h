import numpy as np

from models.transform.base import BaseTransform, gen_padding_transform_cls, gen_extra_transform_cls
from models.transform.statics import UserStatic


class FullStateInfoV2(object):
    """
    Full state info
    action_mask: action mask
    action_cost: action cost
    trajectory_state: trajectory state
    inference_state: inference state
    """

    def __init__(self, trajectory_state, inference_state):
        self.trajectory_state = trajectory_state
        self.inference_state = inference_state


class InferenceInfoV2(object):
    """
    State info
    action_mask: action mask
    action_cost: action cost
    inference_state: inference state
    """

    def __init__(self, action_mask, action_cost, inference_state):
        self.action_mask = action_mask
        self.action_cost = action_cost
        self.inference_state = inference_state


class StateInfoV2(object):
    """
    State info
    action_mask: action mask
    action_cost: action cost
    static_info: static info
    comm_cards_info: community cards info
    action_history_info: action history info
    """

    def __init__(self, action_mask, action_cost, static_info, comm_cards_info, action_history_info):
        self.action_mask = action_mask
        self.action_cost = action_cost
        self.static_info = static_info
        self.comm_cards_info = comm_cards_info
        self.action_history_info = action_history_info


class TransformV2Base(BaseTransform):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)

    def convert_general_state(self, state) -> StateInfoV2:
        """
        Convert the raw state to the input of the model
        :param state: raw state
        :return:
        """
        action_mask, action_cost = self.convert_action_mask_and_cost(state) # 合法行为掩码和行为成本
        static_info = self.convert_static_info_v2(state, action_mask, action_cost)
        comm_cards_info = self.convert_comm_cards_info(state)
        action_history_info = self.convert_action_history_info(state)
        return StateInfoV2(
            action_mask=action_mask,
            action_cost=action_cost,
            static_info=static_info,
            comm_cards_info=comm_cards_info,
            action_history_info=action_history_info
        )

    def convert_inference_state(self, state) -> StateInfoV2:
        return self.convert_general_state(state)

    def warp_full_state_info(self, state_info: StateInfoV2, trajectory_state, device: str):
        inference_info = self.wrap_inference_info(state_info, device)
        return FullStateInfoV2(trajectory_state=trajectory_state, inference_state=inference_info)

    def wrap_inference_info(self, state_info: StateInfoV2, device: str):
        action_mask = np.expand_dims(state_info.action_mask, axis=0)
        action_cost = np.expand_dims(state_info.action_cost, axis=0)
        inference_state = self.wrap_inference_state(state_info, device)
        return InferenceInfoV2(action_mask=action_mask, action_cost=action_cost, inference_state=inference_state)

    def feed_static_base_info(self, state, static_info: np.array):
        static_info[0] = state.dealer_id
        static_info[1] = state.my_id

    def feed_action_info_into_static_info(self, action_mask, action_cost, static_info: np.array):
        size = len(action_mask)
        for i in range(size):
            static_info[i + 2] = action_mask[i]
            static_info[i + 2 + size] = action_cost[i]


class TransformExtraV2Base(BaseTransform):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)
        self.static_extra_info_dim = schema.get_static_extra_info_dim()
        self.static_info_whole_dim = self.static_base_info_dim + self.static_extra_info_dim
        self.user_statics = UserStatic(player_num=schema.player_num,
                                       min_us_size=schema.min_us_size,
                                       max_us_size=schema.max_us_size,
                                       padding_value=self.padding_value)

    def convert_inference_state(self, state):
        action_mask, action_cost = self.convert_action_mask_and_cost(state)
        static_info = self.convert_inference_static_info(state, action_mask, action_cost)
        comm_cards_info = self.convert_comm_cards_info(state)
        action_history_info = self.convert_action_history_info(state)
        return StateInfoV2(
            action_mask=action_mask,
            action_cost=action_cost,
            static_info=static_info,
            comm_cards_info=comm_cards_info,
            action_history_info=action_history_info
        )

    def convert_inference_static_info(self, state, action_mask, action_cost) -> np.array:
        """
        Convert the static info
        :param state: raw state
        :param action_mask: action mask
        :param action_cost: action cost
        :return: static info
        """
        static_info = np.zeros(self.static_info_whole_dim, dtype=np.float32)
        self.feed_static_base_info(state, static_info)
        self.feed_action_info_into_static_info(
            action_mask=action_mask, action_cost=action_cost, static_info=static_info)
        self.user_statics.feed_statics_info(state, static_info, self.static_base_info_dim)
        return static_info

    def feed_static_extra_info(self, state, static_info: np.array):
        # copy state.player_statics to static_info from index self.static_base_info_dim
        static_info[self.static_base_info_dim:] = state.player_statics


class TransformHybridV2Base(TransformExtraV2Base):
    def convert_state_to_full_info(self, state, device: str):
        state_info = self.convert_general_state(state)
        trajectory_state = (state_info.static_info, state_info.comm_cards_info, state_info.action_history_info)
        state_info.static_info = state_info.static_info[:self.static_base_info_dim]
        return self.warp_full_state_info(state_info, trajectory_state, device)


TransformSlimV2 = gen_padding_transform_cls(TransformV2Base)

TransformSlimExtraV2 = gen_extra_transform_cls(TransformSlimV2, TransformExtraV2Base)


class TransformSlimHybridV2(TransformSlimExtraV2, TransformHybridV2Base):
    def convert_state_to_full_info(self, state, device: str) -> (np.array, tuple, tuple):
        return TransformHybridV2Base.convert_state_to_full_info(self, state, device)
