import torch
import torch.nn as nn

from models.consts import *
from models.dqn.slim import Slim
# from models.dqn.mix import MixDqn
# from models.dqn.tiny import TinyDqn
# from models.dqn.tiny_mix import TinyMixDqn
# from models.dqn.alpha import AlphaDqn
# from models.ppo.slim import SlimPPO


def restore_model(checkpoint_path: str, device: str = 'cpu', argmax_action: bool = False) -> tuple[nn.Module, str]:
    """
    Args:
        checkpoint_path: path to the checkpoint file.
        device: device to load the model to.
        argmax_action: flag indicating whether the model should use argmax action selection.
    Returns:
        model: the restored model.
        model_type: the type of the model.
    """
    p = torch.load(checkpoint_path, map_location=device)
    model_type = p[MODEL_TYPE_KEY]
    if model_type == DQN_SLIM:
        return Slim.restore_from_dict(p, device, argmax_action), DQN_SLIM
    elif model_type == DQN_MIX:
        return Mix.restore_from_dict(p, device, argmax_action), DQN_MIX
    elif model_type == DQN_TINY:
        return Tiny.restore_from_dict(p, device, argmax_action), DQN_TINY
    elif model_type == DQN_TINY_MIX:
        return TinyMix.restore_from_dict(p, device, argmax_action), DQN_TINY_MIX
    else:
        raise ValueError(f'Unknown model type: {model_type}')
