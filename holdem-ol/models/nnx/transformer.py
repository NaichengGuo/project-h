import math

import torch
import torch.nn as nn
import torch.nn.init as init

TRF_INPUT_DIM_KEY = "input_dim"
TRF_NUM_HEADS_KEY = "num_heads"
TRF_HIDDEN_SIZE_KEY = "hidden_size"
TRF_NUM_LAYERS_KEY = "num_layers"
TRF_OUTPUT_DIM_KEY = "output_dim"
TRF_NORM_FIRST_KEY = "norm_first"
TRF_MAX_LEN_KEY = "max_len"
TRF_DROPOUT_KEY = "dropout"
TRF_MASK_KEY = "mask"


class PositionalEncoding(nn.Module):
    def __init__(self, dim, max_len=128):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, dim)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, dim, 2).float() * (-math.log(10000.0) / dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return x

    def to(self, device):
        self.pe = self.pe.to(device)
        return self


class SlimTransformerEncoder(nn.Module):
    def __init__(self,
                 input_dim, num_heads, hidden_size, num_layers, output_dim, padding_value: float,
                 use_padding_mask: bool = False, norm_first=True, max_len=128, dropout=0.02):
        super(SlimTransformerEncoder, self).__init__()
        self.input_dim = input_dim
        self.num_heads = num_heads
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_dim = output_dim
        self.padding_value = padding_value
        self.use_padding_mask = use_padding_mask
        self.norm_first = norm_first
        self.max_len = max_len
        self.dropout = dropout

        self.input_linear = nn.Linear(input_dim, hidden_size)
        encoder_layers = nn.TransformerEncoderLayer(hidden_size, num_heads, dropout=dropout, norm_first=norm_first,
                                                    dim_feedforward=hidden_size, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers,
                                                         enable_nested_tensor=False, mask_check=False)
        self.output_linear = nn.Linear(hidden_size, output_dim)
        self._init_weights()

    def to(self, device):
        self.input_linear.to(device)
        self.transformer_encoder.to(device)
        self.output_linear.to(device)
        return self

    def train(self, mode=True):
        self.input_linear.train(mode)
        self.transformer_encoder.train(mode)
        self.output_linear.train(mode)
        return self

    def eval(self):
        self.input_linear.eval()
        self.transformer_encoder.eval()
        self.output_linear.eval()
        return self

    def forward(self, x):
        # x: [batch_size, sequence_length, num_features]
        src_key_padding_mask = self.create_mask(x)
        _input = self.input_linear(x)
        _output = self.transformer_encoder(_input, src_key_padding_mask=src_key_padding_mask)
        _output = _output[:, -1, :]
        _output = self.output_linear(_output)
        return _output

    def net_schema(self) -> dict:
        return {
            TRF_INPUT_DIM_KEY: self.input_dim,
            TRF_NUM_HEADS_KEY: self.num_heads,
            TRF_HIDDEN_SIZE_KEY: self.hidden_size,
            TRF_NUM_LAYERS_KEY: self.num_layers,
            TRF_OUTPUT_DIM_KEY: self.output_dim,
            TRF_NORM_FIRST_KEY: self.norm_first,
            TRF_MAX_LEN_KEY: self.max_len,
            TRF_DROPOUT_KEY: self.dropout,
            TRF_MASK_KEY: self.mask
        }

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                init.ones_(module.weight)
                init.zeros_(module.bias)

    def create_mask(self, x):
        if not self.use_padding_mask:
            return None
        return (x == self.padding_value).all(dim=-1).bool()


class TransformerEncoder(SlimTransformerEncoder):
    def __init__(self,
                 input_dim, num_heads, hidden_size, num_layers, output_dim, padding_value: float,
                 use_padding_mask: bool = False, norm_first=True, max_len=128, dropout=0.02):
        super(TransformerEncoder, self).__init__(input_dim, num_heads, hidden_size, num_layers, output_dim,
                                                 padding_value, use_padding_mask, norm_first, max_len, dropout)
        self.pos_encoder = PositionalEncoding(hidden_size, max_len=max_len)

    def to(self, device):
        self.input_linear.to(device)
        self.pos_encoder.to(device)
        self.transformer_encoder.to(device)
        self.output_linear.to(device)
        return self

    def forward(self, x):
        # x: [batch_size, sequence_length, num_features]
        src_key_padding_mask = self.create_mask(x)
        _input = self.input_linear(x)
        embeddings = self.pos_encoder(_input)
        _output = self.transformer_encoder(embeddings, src_key_padding_mask=src_key_padding_mask)
        _output = _output[:, -1, :]
        _output = self.output_linear(_output)
        return _output
