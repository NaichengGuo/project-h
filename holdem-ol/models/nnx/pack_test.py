import numpy as np
import torch

from models.nnx.pack import TsSeq, Batch


def test_pad_and_pack1():
    sequences = [
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[-1, -2, -3]],
    ]
    ts = TsSeq()
    packed_sequence, size = ts.pad_and_pack(sequences)
    print(packed_sequence)
    print(size)
    padded_sequence, size = ts.unpack(packed_sequence)
    print(padded_sequence)
    print(size)
    print(len(padded_sequence))


def test_pad_and_pack2():
    s1 = [
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[-1, -2, -3]],
    ]

    s2 = [
        [[0, 0, 0], [1, 1, 1]],
        [[-1, -1, -1]],
    ]

    # cat s1 and s2
    sequences = s1 + s2
    ts = TsSeq()
    packed_sequence, size = ts.pad_and_pack(sequences)
    print(packed_sequence)
    print(size)
    padded_sequence, size = ts.unpack(packed_sequence)
    print(padded_sequence)
    print(size)
    print(len(padded_sequence))


def test_pad_and_pack3():
    sequences = [
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
        np.array([[-1, -2, -3]]),
        np.array([[-8, -9, 0], [1, 1, 1]]),
        np.array([[-1, -10, -10]]),
    ]
    ts = TsSeq(1e-7)
    packed_sequence, size = ts.pad_and_pack(sequences)
    print('packed_sequence:')
    print(packed_sequence)
    print()

    print('size:')
    print(size)
    print()

    padded_sequence, size = ts.unpack(packed_sequence)
    print('padded_sequence:')
    print(padded_sequence)
    print()

    print('padded size:')
    print(size)
    print()

    print('packed_sequence.len:')
    print(len(padded_sequence))


def test_expand1():
    x1 = np.array([1, 2, 3])
    x2 = np.array([[0, 0, 0], [1, 1, 1]])
    x3 = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
    size = 2
    # x1 = Expand.expand(x1, size)
    # x2 = Expand.expand(x2, size)
    # x3 = Expand.expand(x3, size)
    x1, x2, x3 = Batch.expand_x(size, x1, x2, x3)
    print(f"x1: {x1}")
    print(f"x2: {x2}")
    print(f"x3: {x3}")

    x1 = torch.from_numpy(x1)
    x2 = torch.from_numpy(x2)
    x3 = torch.from_numpy(x3)
    print(f"torch x1: {x1}")
    print(f"torch x2: {x2}")
    print(f"torch x3: {x3}")


def test_cat_matrix1():
    x1 = np.array([[1, 2, 3], [4, 5, 6]])
    x2 = np.array([[7, 8, 9], [10, 11, 12]])

    x1 = torch.from_numpy(x1)
    x2 = torch.from_numpy(x2)
    print(f"x1: {x1}")
    print(f"x2: {x2}")
    x = torch.cat((x1, x2), dim=1)
    print(f"x: {x}")
    x1_flatten = torch.flatten(x1, 1)
    x2_flatten = torch.flatten(x2, 1)
    print(f"x1_flatten: {x1_flatten}")
    print(f"x2_flatten: {x2_flatten}")
    x = torch.cat((x1_flatten, x2_flatten), dim=1)
    print(f"x: {x}")


if __name__ == '__main__':
    # test_pad_and_pack1()
    # test_expand1()
    # test_cat_matrix1()
    test_pad_and_pack3()
