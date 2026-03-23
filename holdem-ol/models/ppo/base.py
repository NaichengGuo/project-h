import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from abc import ABC, abstractmethod

from core.game.action import Action
from core.utils.collection import DDict
from models.consts import *
from models.ppo.consts import *


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


class PpoBase(ABC):
    def __init__(self, **kwargs):
        self.transform = None
        self.device = None
        self.actor = None
        self.critic = None

    @abstractmethod
    def forward_actor(self, state):
        """
        Args:
            state: state info
        Returns: action probabilities
        """
        raise NotImplementedError

    @abstractmethod
    def forward_critic(self, state):
        """
        Args:
            state: state info
        Returns: state value
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
        action_probs = self.predict_action_probs(model_input, action_mask)
        # During inference, we can either sample from the distribution or take the most probable action
        # Here we sample from the distribution
        action_distribution = torch.distributions.Categorical(torch.from_numpy(action_probs))
        action_idx = action_distribution.sample().item()
        return action_idx

    def predict_action_probs(self, model_input, action_mask):
        """
        Args:
            model_input: state info
            action_mask: action mask
        Returns: action probabilities
        """
        with torch.no_grad():
            logits = self.forward_actor(model_input).cpu().numpy()
        # Apply action mask by setting logits of invalid actions to -inf
        masked_logits = np.where(action_mask == 0, -np.inf, logits)
        masked_logits = np.squeeze(masked_logits, axis=0)
        # Convert to probabilities using softmax
        probs = F.softmax(torch.from_numpy(masked_logits), dim=0).numpy()
        return probs

    def predict_state_value(self, model_input):
        """
        Args:
            model_input: state info
        Returns: state value
        """
        with torch.no_grad():
            state_value = self.forward_critic(model_input).cpu().numpy()
        return state_value

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
                          device: str = 'cpu'):
        """
        Args:
            dict_data: model parameters
            device: device
        Returns: model
        """
        model_schema = cls.generate_schema(dict_data[SCHEMA])
        transform = cls.generate_transform(model_schema)
        model = cls(schema=model_schema, transform=transform, device=device)
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