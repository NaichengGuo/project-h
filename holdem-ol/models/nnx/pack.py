import numpy as np
import torch

from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence


class TsSeq(object):
    def __init__(self, padding_value: float = 0):
        self.padding_value = padding_value

    def pad_and_pack(self, sequences):
        # 填充序列
        padded_sequences = [torch.as_tensor(np.array(seq), dtype=torch.float32) for seq in sequences]
        # 填充序列
        padded_sequences = pad_sequence(padded_sequences, batch_first=True, padding_value=self.padding_value)
        # 获取每个序列的实际长度(As Tensor) size_tensor
        size_tensor = torch.tensor([len(seq) for seq in sequences], dtype=torch.int64)
        # 打包序列
        packed_sequence = pack_padded_sequence(padded_sequences, size_tensor, batch_first=True, enforce_sorted=False)
        return packed_sequence, size_tensor

    def unpack(self, packed_sequence):
        # 解包序列
        padded_sequence, size = pad_packed_sequence(packed_sequence, batch_first=True, padding_value=self.padding_value)
        return padded_sequence, size


class Batch(object):
    @staticmethod
    def expand(x, size: int):
        return np.repeat(x[np.newaxis, :], size, axis=0)

    @staticmethod
    def expand_x(size: int, *args):
        return (Batch.expand(x, size) for x in args)
