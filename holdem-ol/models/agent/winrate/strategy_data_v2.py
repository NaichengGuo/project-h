import numpy as np

from core.game.action import Action

# base_strategy = [
#     # [-0.00001, 0.39, 0.6, 0.75, 1.00001]
#     # 概率区间1 (很弱）
#     [
#         (Action.FOLD,               0.850, 0.850),
#         (Action.CHECK_CALL,         0.150, 0.150),
#         (Action.RAISE_HALF_POT,     0.050, 0.050),
#         (Action.ALL_IN,             0.005, 0.005),
#     ],
#     # 概率区间2（中弱）
#     [
#         (Action.FOLD,               0.050, 0.020),
#         (Action.CHECK_CALL,         0.800, 0.700),
#         (Action.RAISE_HALF_POT,     0.050, 0.150),
#         (Action.ALL_IN,             0.010, 0.020),
#     ],
#     # 概率区间3（中强）
#     [
#         (Action.FOLD,               0.020, 0.010),
#         (Action.CHECK_CALL,         0.700, 0.500),
#         (Action.RAISE_POT,          0.150, 0.300),
#         (Action.ALL_IN,             0.020, 0.050),
#     ],
#     # 概率区间4（很强）
#     [
#         (Action.FOLD,               0.010, 0.000),
#         (Action.CHECK_CALL,         0.150, 0.050),
#         (Action.RAISE_DOUBLE_POT,   0.350, 0.800),
#         (Action.ALL_IN,             0.050, 0.150),
#     ],
# ]

base_strategy = [
    # [-0.00001, 0.39, 0.6, 0.75, 1.00001]
    # 概率区间1 (很弱）
    [
        (Action.FOLD,               0.850, 0.850),
        (Action.CHECK_CALL,         0.150, 0.150),
        (Action.RAISE_HALF_POT,     0.050, 0.050),
        (Action.ALL_IN,             0.005, 0.005),
    ],
    # 概率区间2（中弱）
    [
        (Action.FOLD,               0.050, 0.020),
        (Action.CHECK_CALL,         0.800, 0.700),
        (Action.RAISE_HALF_POT,     0.050, 0.150),
        (Action.ALL_IN,             0.010, 0.020),
    ],
    # 概率区间3（中强）
    [
        (Action.FOLD,               0.020, 0.010),
        (Action.CHECK_CALL,         0.700, 0.500),
        (Action.RAISE_POT,          0.150, 0.300),
        (Action.ALL_IN,             0.020, 0.050),
    ],
    # 概率区间4（很强）
    [
        (Action.FOLD,               0.005, 0.000),
        (Action.CHECK_CALL,         0.150, 0.050),
        (Action.RAISE_DOUBLE_POT,   0.750, 0.800),
        (Action.ALL_IN,             0.050, 0.150),
    ],
]

# preflop_strategy = [
#     [0, 20, 40, 80, 1000000],
#     [0, 0.390, 0.520, 0.610, 1.000001],
#     [0, 0.500, 0.580, 0.630, 1.000001],
#     [0, 0.556, 0.596, 0.660, 1.000001],
#     [0, 0.630, 0.700, 0.800, 1.000001],
# ]
#
# flop_strategy = [
#     [0, 20, 40, 80, 1000000],
#     [0, 0.410, 0.600, 0.700, 1.000001],
#     [0, 0.550, 0.650, 0.750, 1.000001],
#     [0, 0.600, 0.700, 0.800, 1.000001],
#     [0, 0.650, 0.750, 0.850, 1.000001],
# ]
#
# turn_strategy = [
#     [0, 20, 40, 80, 1000000],
#     [0, 0.450, 0.600, 0.700, 1.000001],
#     [0, 0.570, 0.680, 0.780, 1.000001],
#     [0, 0.620, 0.720, 0.820, 1.000001],
#     [0, 0.700, 0.770, 0.850, 1.000001],
# ]
#
# river_strategy = [
#     [0, 20, 40, 80, 1000000],
#     [0, 0.410, 0.600, 0.750, 1.000001],
#     [0, 0.600, 0.700, 0.800, 1.000001],
#     [0, 0.650, 0.750, 0.850, 1.000001],
#     [0, 0.750, 0.800, 0.900, 1.000001],
# ]

preflop_strategy = [
    [0, 20, 40, 80, 1000000],
    [0, 0.390, 0.520, 0.610, 1.000001],
    [0, 0.500, 0.580, 0.730, 1.000001],
    [0, 0.556, 0.596, 0.760, 1.000001],
    [0, 0.630, 0.700, 0.800, 1.000001],
]

flop_strategy = [
    [0, 20, 40, 80, 1000000],
    [0, 0.410, 0.600, 0.800, 1.000001],
    [0, 0.550, 0.650, 0.850, 1.000001],
    [0, 0.600, 0.700, 0.880, 1.000001],
    [0, 0.650, 0.750, 0.900, 1.000001],
]

turn_strategy = [
    [0, 20, 40, 80, 1000000],
    [0, 0.450, 0.600, 0.800, 1.000001],
    [0, 0.570, 0.680, 0.880, 1.000001],
    [0, 0.620, 0.720, 0.920, 1.000001],
    [0, 0.700, 0.770, 0.930, 1.000001],
]

river_strategy = [
    [0, 20, 40, 80, 1000000],
    [0, 0.410, 0.600, 0.850, 1.000001],
    [0, 0.600, 0.700, 0.880, 1.000001],
    [0, 0.650, 0.750, 0.900, 1.000001],
    [0, 0.750, 0.800, 0.930, 1.000001],
]

raise_weak = [
    (Action.RAISE_HALF_POT,     0.5),
    (Action.RAISE_3_4_POT,      0.2),
    (Action.RAISE_POT,          0.1),
    (Action.RAISE_3_2_POT,      0.05),
    (Action.RAISE_DOUBLE_POT,   0.02)
]

raise_mid = [
    (Action.RAISE_HALF_POT,     0.1),
    (Action.RAISE_3_4_POT,      0.2),
    (Action.RAISE_POT,          0.5),
    (Action.RAISE_3_2_POT,      0.2),
    (Action.RAISE_DOUBLE_POT,   0.1)
]

raise_strong = [
    (Action.RAISE_HALF_POT,     0.02),
    (Action.RAISE_3_4_POT,      0.05),
    (Action.RAISE_POT,          0.1),
    (Action.RAISE_3_2_POT,      0.2),
    (Action.RAISE_DOUBLE_POT,   0.5)
]

strategy_data_v2 = [
    ([0], preflop_strategy),
    ([3], flop_strategy),
    ([4], turn_strategy),
    ([5], river_strategy),
]

def decide_raise(raise_acion):
    if raise_acion == Action.RAISE_HALF_POT:
        return _internal_decide_raise(raise_weak)
    if raise_acion == Action.RAISE_POT:
        return _internal_decide_raise(raise_mid)
    if raise_acion == Action.RAISE_DOUBLE_POT:
        return _internal_decide_raise(raise_strong)

    return raise_acion

def _internal_decide_raise(data):
    available_actions = []
    probs = []
    for i in range(len(data)):
        prob = data[i][1]
        action = data[i][0]
        probs.append(prob)
        available_actions.append(action)

    sum_value = sum(probs)
    probs = [x / sum_value for x in probs]
    pick = np.random.choice(available_actions, p=probs)

    return pick