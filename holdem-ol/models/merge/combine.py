import argparse

import torch

from models.dqn.slim import Slim


def average_slim_models(models: list[Slim]):
    # 获取模型参数字典的键
    param_keys = models[0].get_parameters().keys()

    # 初始化一个新的参数字典，用于存储平均后的参数
    avg_params = {}
    for key in param_keys:
        # 获取所有模型中相同键的参数
        params = [model.get_parameters()[key] for model in models]

        # 将所有参数转换为tensor，并计算平均值
        avg_params[key] = {k: torch.mean(torch.stack([param[k] for param in params]), dim=0) for k in params[0].keys()}

    # 创建一个新的模型实例
    new_model = Slim(models[0].schema, models[0].transform, models[0].device, models[0].argmax_action)

    # 将平均后的参数加载到新模型中
    new_model.set_parameters(avg_params)

    return new_model


def read_models(paths: list[str], device: str = 'cpu') -> list[Slim]:
    models = []
    for path in paths:
        model = Slim.restore(path, device)
        models.append(model)
    return models


def combine_models(paths: list[str], tar_file: str, device: str = 'cpu'):
    models = read_models(paths, device)
    avg_model = average_slim_models(models)
    avg_model.save_model(tar_file)


def add_args():
    parser = argparse.ArgumentParser('Combine models')
    parser.add_argument('--paths', type=str, nargs='+', help='Paths to models to combine')
    parser.add_argument('--tar_file', type=str, help='Path to the target file')
    parser.add_argument('--device', type=str, default='cpu', help='Device to load the models to')
    return parser


def main():
    parser = add_args()
    args = parser.parse_args()
    combine_models(args.paths, args.tar_file, args.device)


if __name__ == '__main__':
    main()
