import torch.nn.init as init
import torch.nn as nn


class SkipHiddenLayer(nn.Module):
    def __init__(self, unit_size):
        super(SkipHiddenLayer, self).__init__()
        self.hidden = nn.Linear(unit_size, unit_size)

    def forward(self, x):
        return self.hidden(x) + x


class Fcl(nn.Module):
    def __init__(self, input_size: int, hidden_layers: list, output_size: int,
                 name='fcl', activation=nn.ReLU()):
        super(Fcl, self).__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_layers = hidden_layers
        self.layer = nn.Sequential()
        self.layer.add_module('input', nn.Linear(input_size, hidden_layers[0]))
        self.layer.add_module('input_activation', activation)
        for i in range(len(hidden_layers) - 1):
            self.layer.add_module(f'hidden_{i}', nn.Linear(hidden_layers[i], hidden_layers[i + 1]))
            self.layer.add_module(f'hidden_{i}_activation', activation)
        self.layer.add_module('output', nn.Linear(hidden_layers[-1], output_size))
        self.name = name

    def init_weights(self, init_weight):
        if init_weight is None:
            init_weight = init.xavier_uniform_

        for m in self.modules():
            if isinstance(m, nn.Linear):
                init_weight(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        return self.layer(x)

    def get_name(self):
        return self.name


class SkipFcl(nn.Module):
    def __init__(self, input_size: int, hidden_layers: list, output_size: int,
                 name='skip', activation=nn.ReLU()):
        super(SkipFcl, self).__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_layers = hidden_layers
        self.layer = nn.Sequential()
        self.layer.add_module('input', nn.Linear(input_size, hidden_layers[0]))
        self.layer.add_module('input_activation', activation)
        for i in range(len(hidden_layers) - 1):
            if hidden_layers[i] == hidden_layers[i + 1]:
                self.layer.add_module(f'hidden_{i}', SkipHiddenLayer(hidden_layers[i]))
            else:
                self.layer.add_module(f'hidden_{i}', nn.Linear(hidden_layers[i], hidden_layers[i + 1]))
            self.layer.add_module(f'hidden_{i}_activation', activation)
        self.layer.add_module('output', nn.Linear(hidden_layers[-1], output_size))
        self.name = name

    def forward(self, x):
        return self.layer(x)

    def get_name(self):
        return self.name
