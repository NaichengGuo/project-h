import numpy as np
import torch

from abc import ABC, abstractmethod

from core.game.action import Action
from core.utils.collection import DDict
from models.consts import *
from models.dqn.consts import *


class BaseSchema(DDict):
    def __init__(self):
        """
        Just init
        """
        self.player_num = 0
        self.static_info_size = 0

    def get_static_base_info_dim(self):
        return self.static_info_size

    def get_static_extra_info_dim(self):
        return self.player_num * USER_STATICS_INFO_SIZE


class DqnBase(ABC):
    def __init__(self, argmax_action: bool = False, **kwargs):
        self.transform = None
        self.argmax_action = argmax_action
        self.device = None

    @abstractmethod
    def forward(self, state):
        """
        Args:
            state: state info
        Returns: q values
        """
        raise NotImplementedError

    @abstractmethod
    def schema_to_dict(self):
        """
        Returns: schema dict
        """
        raise NotImplementedError

    @abstractmethod
    def get_parameters(self, to_device=None):
        """
        Returns: network parameters
        """
        raise NotImplementedError

    @abstractmethod
    def set_parameters(self, parameters):
        """
        Args:
            parameters: network parameters
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def convert_parameters(cls, parameters, to_device: str):
        """
        Args:
            parameters: network parameters
            to_device: device
        Returns: converted parameters
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_model_type(cls):
        """
        Returns: model type
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def generate_schema(cls, dict_data: dict):
        """
        Returns: schema class
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def generate_transform(cls, schema):
        """
        Returns: transform
        """
        raise NotImplementedError

    def inference(self, state):
        inference_state = self.transform.convert_state_to_inference(state, self.device)
        return self.predict_action_with_mask(inference_state.inference_state, inference_state.action_mask)

    def convert_state_to_full_info(self, state, device: str):
        return self.transform.convert_state_to_full_info(state, device)

    def predict_action_with_mask(self, model_input, action_mask):
        q_values = self.predict_q_values(model_input, action_mask)
        if self.argmax_action:
            action_idx = np.argmax(q_values)
        else:
            q_values = torch.from_numpy(q_values)
            probs = torch.softmax(q_values, dim=0).cpu().numpy()
            action_idx = np.random.choice(np.arange(len(Action)), p=probs)
        return action_idx

    def predict_q_values(self, model_input, action_mask):
        """
        Args:
            model_input: state info
            action_mask: action mask
        Returns: q values
        """
        with torch.no_grad():
            q_values = self.forward(model_input).cpu().numpy()
        marked_q_values = np.where(action_mask == 0, -np.inf, q_values)
        marked_q_values = np.squeeze(marked_q_values, axis=0)
        return marked_q_values

    def save_model(self, f_name):
        """
        Args:
            f_name: file name
        """
        p = self.get_parameters()
        p[SCHEMA] = self.schema_to_dict()
        p[MODEL_TYPE_KEY] = self.get_model_type()
        torch.save(p, f_name)

    def save_model_with_params(self, f_name, params):
        """
        Args:
            f_name: file name
            params: parameters
        """
        p = dict()
        p[SCHEMA] = self.schema_to_dict()
        p[MODEL_TYPE_KEY] = self.get_model_type()
        p.update(params)
        torch.save(p, f_name)

    def load_from_file(self, f_name):
        """
        Args:
            f_name: file name
        """
        data = torch.load(f_name)
        self.set_parameters(data)

    @classmethod
    def restore(cls, f_name: str, device: str = 'cpu'):
        """
        Args:
            f_name: file name
            device: device
        Returns: model
        """
        p = torch.load(f_name, map_location=device)
        return cls.restore_from_dict(p, device)

    @classmethod
    def restore_from_dict(cls,
                          dict_data: dict,
                          device: str = 'cpu',
                          argmax_action: bool = False):
        """
        Args:
            dict_data: model parameters
            device: device
            argmax_action:
        Returns: model
        """
        model_schema = cls.generate_schema(dict_data[SCHEMA])
        transform = cls.generate_transform(model_schema)
        model = cls(schema=model_schema, transform=transform, device=device, argmax_action=argmax_action)
        model.set_parameters(dict_data)
        return model


def convert_state_param_to_device(param: dict, device: str):
    """
    Args:
        param: state info
        device: device
    Returns: state info
    """
    for k, v in param.items():
        param[k] = v.to(device)
    return param


def convert_full_param_device(param: dict, device: str):
    """
    Args:
        param: state info
        device: device
    Returns: state info
    """
    for k, v in param.items():
        if isinstance(v, dict):
            param[k] = convert_state_param_to_device(v, device)
        else:
            param[k] = v.to(device)
    return param
