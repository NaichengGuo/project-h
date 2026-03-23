import numpy as np


def feed_matrix(src: np.array, des: np.array):
    sl, dl = src.shape[0], des.shape[0]
    if dl >= sl:
        des[:sl, :] = src
    else:
        # copy last src rows[same with desc length] to des
        des[:dl, :] = src[-dl:, :]
    return des


def feed_matrix_column(src: np.array, des: np.array, src_column: int, dst_column: int):
    sl, dl = src.shape[0], des.shape[0]
    if dl >= sl:
        des[:sl, dst_column] = src[:, src_column]
    else:
        # copy last src rows[same with desc length] to des
        des[:dl, dst_column] = src[-dl:, src_column]
    return des
