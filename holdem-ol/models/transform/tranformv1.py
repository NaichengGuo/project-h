import numpy as np
import torch

from models.nnx.pack import TsSeq
from models.transform.base import BaseTransform, gen_padding_transform_cls, gen_extra_transform_cls
from models.transform.statics import UserStatic


class FullStateInfoV1(object):
    """
    Full state info
    action_mask: action mask
    trajectory_state: trajectory state
    inference_state: inference state
    """

    def __init__(self, trajectory_state, inference_state):
        self.trajectory_state = trajectory_state
        self.inference_state = inference_state


class InferenceInfoV1(object):
    """
    State info
    action_mask: action mask
    inference_state: inference state
    """

    def __init__(self, action_mask, inference_state):
        self.action_mask = action_mask
        self.inference_state = inference_state


class StateInfoV1(object):
    """
    State info
    action_mask: action mask
    static_info: static info
    comm_cards_info: community cards info
    action_history_info: action history info
    """

    def __init__(self, action_mask, static_info, comm_cards_info, action_history_info):
        self.action_mask = action_mask
        self.static_info = static_info
        self.comm_cards_info = comm_cards_info
        self.action_history_info = action_history_info


class TransformV1Base(BaseTransform):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)

    def convert_general_state(self, state) -> StateInfoV1:
        """
        Convert the raw state to the input of the model
        :param state: raw state
        :return: action_mask, static_info, comm_cards_info, action_history_info
        """
        action_mask = self.convert_action_mask(state)
        static_info = self.convert_static_info(state)
        comm_cards_info = self.convert_comm_cards_info(state)
        action_history_info = self.convert_action_history_info(state)
        return StateInfoV1(
            action_mask=action_mask,
            static_info=static_info,
            comm_cards_info=comm_cards_info,
            action_history_info=action_history_info
        )

    def convert_inference_state(self, state) -> StateInfoV1:
        return self.convert_general_state(state)

    def feed_static_base_info(self, state, static_info: np.array):
        static_info[0] = state.dealer_id # dealer id
        static_info[1] = state.my_id # my id
        if self.static_base_info_dim == 3:
            static_info[2] = state.ante / state.small_blind

    def warp_full_state_info(self, state_info: StateInfoV1, trajectory_state, device: str):
        inference_info = self.wrap_inference_info(state_info, device)
        return FullStateInfoV1(trajectory_state=trajectory_state, inference_state=inference_info)

    def wrap_inference_info(self, state_info: StateInfoV1, device: str):
        action_mask = np.expand_dims(state_info.action_mask, axis=0)
        inference_state = self.wrap_inference_state(state_info, device)
        return InferenceInfoV1(action_mask=action_mask, inference_state=inference_state)


class TransformExtraV1Base(BaseTransform):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)
        self.static_extra_info_dim = schema.get_static_extra_info_dim()
        self.static_info_whole_dim = self.static_base_info_dim + self.static_extra_info_dim
        self.user_statics = UserStatic(player_num=schema.player_num,
                                       min_us_size=schema.min_us_size,
                                       max_us_size=schema.max_us_size,
                                       padding_value=self.padding_value)

    def convert_inference_state(self, state):
        action_mask = self.convert_action_mask(state)
        static_info = self.convert_inference_static_info(state)
        comm_cards_info = self.convert_comm_cards_info(state)
        action_history_info = self.convert_action_history_info(state)
        return StateInfoV1(
            action_mask=action_mask,
            static_info=static_info,
            comm_cards_info=comm_cards_info,
            action_history_info=action_history_info
        )

    def convert_inference_static_info(self, state) -> np.array:
        """
        Convert the static info
        :param state: raw state
        :return: static info
        """
        static_info = np.zeros(self.static_info_whole_dim, dtype=np.float32)
        self.feed_static_base_info(state, static_info)
        self.user_statics.feed_statics_info(state, static_info, self.static_base_info_dim)
        return static_info

    def feed_static_extra_info(self, state, static_info: np.array):
        # copy state.player_statics to static_info from index self.static_base_info_dim
        static_info[self.static_base_info_dim:] = state.player_statics


class TransformHybridV1Base(TransformExtraV1Base):
    def convert_state_to_full_info(self, state, device: str):
        """
        Convert the raw state to the input of the model
        :param state: raw state
        :param device: device
        :return: action_mask, trajectory state, inference state
                 返回 动作掩码/弹道格式/推理格式
        """
        state_info = self.convert_general_state(state)
        trajectory_state = (state_info.static_info, state_info.comm_cards_info, state_info.action_history_info)
        state_info.static_info = state_info.static_info[:self.static_base_info_dim]
        return self.warp_full_state_info(state_info, trajectory_state, device)


class TransformTinyV1(TransformV1Base):
    def __init__(self, schema):
        BaseTransform.__init__(self, schema)
        self.packer = TsSeq(self.padding_value)

    def wrap_comm_cards_info_input(self, comm_cards_info):
        return np.expand_dims(comm_cards_info, axis=0)

    def wrap_action_history_info_input(self, action_history_info):
        return np.expand_dims(action_history_info, axis=0)

    def convert_save_state_for_training(self, ds: list[tuple], device: str):
        """
        Convert the raw state to the input of the model for training
        :param ds: raw state list
        :param device: device
        :return: input tuple
        """
        batch_size = len(ds)
        batch_comm_cards_info = []
        batch_action_history_info = []
        batch_static_info = np.zeros((batch_size, self.static_info_whole_dim), dtype=np.float32)
        for idx, trajectory_state in enumerate(ds):
            static_info, comm_cards_info, action_history_info = trajectory_state
            batch_static_info[idx] = static_info[:self.static_info_whole_dim]
            batch_comm_cards_info.append(comm_cards_info)
            batch_action_history_info.append(action_history_info)
        batch_static_info_tensor = torch.tensor(batch_static_info, dtype=torch.float32, device=device)
        batch_comm_cards_info, _ = self.packer.pad_and_pack(batch_comm_cards_info)
        batch_action_history_info, _ = self.packer.pad_and_pack(batch_action_history_info)
        return batch_static_info_tensor, batch_comm_cards_info.to(device), batch_action_history_info.to(device)


TransformTinyExtraV1 = gen_extra_transform_cls(TransformTinyV1, TransformExtraV1Base)


class TransformTinyHybridV1(TransformTinyExtraV1, TransformHybridV1Base):
    def convert_state_to_full_info(self, state, device: str):
        return TransformHybridV1Base.convert_state_to_full_info(self, state, device)


TransformSlimV1 = gen_padding_transform_cls(TransformV1Base)

TransformSlimExtraV1 = gen_extra_transform_cls(TransformSlimV1, TransformExtraV1Base)


class TransformSlimHybridV1(TransformSlimExtraV1, TransformHybridV1Base):
    def convert_state_to_full_info(self, state, device: str) -> (np.array, tuple, tuple):
        return TransformHybridV1Base.convert_state_to_full_info(self, state, device)
