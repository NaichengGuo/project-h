from core.game.action import Action

# [0, 4, 20, 40, 60, 80, 100000000]
strategy_data_v2_0 = [
    [
        0, # pot
        [-0.00001, 0.39, 0.6, 0.75, 1.00001],  # winrate 区间
        [
            (Action.FOLD, 0.95),
            (Action.CHECK_CALL, 0.05),
            (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0),
                (Action.RAISE_3_4_POT, 0),
                (Action.RAISE_POT, 0),
                (Action.RAISE_3_2_POT, 0),
                (Action.RAISE_DOUBLE_POT, 0),
            ]
        ],
        [
            (Action.FOLD, 0.01),
            (Action.CHECK_CALL, 0.7),
            (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.01),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.4),
                (Action.RAISE_3_4_POT, 0.3),
                (Action.RAISE_POT, 0.15),
                (Action.RAISE_3_2_POT, 0.1),
                (Action.RAISE_DOUBLE_POT, 0.08),
            ],
        ],
        [
            (Action.FOLD, 0.005),
            (Action.CHECK_CALL, 0.5),
            (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.3),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],
        [
            (Action.FOLD, 0.0),
            (Action.CHECK_CALL, 0.2),
            (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.2),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],

    ],
    [
        4,
        [-0.00001, 0.41, 0.6, 0.75, 1.00001],  # winrate 区间
        [
            (Action.FOLD, 0.9),
            (Action.CHECK_CALL, 0.1),
            (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0),
                (Action.RAISE_3_4_POT, 0),
                (Action.RAISE_POT, 0),
                (Action.RAISE_3_2_POT, 0),
                (Action.RAISE_DOUBLE_POT, 0),
            ]
        ],
        [
            (Action.FOLD, 0.01),
            (Action.CHECK_CALL, 0.7),
            (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.01),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.4),
                (Action.RAISE_3_4_POT, 0.3),
                (Action.RAISE_POT, 0.15),
                (Action.RAISE_3_2_POT, 0.1),
                (Action.RAISE_DOUBLE_POT, 0.08),
            ],
        ],
        [
            (Action.FOLD, 0.005),
            (Action.CHECK_CALL, 0.5),
            (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.3),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],
        [
            (Action.FOLD, 0.0),
            (Action.CHECK_CALL, 0.2),
            (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.2),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],

    ],
    [
        20,
        [-0.00001, 0.5, 0.6, 0.75, 1.00001],  # winrate 区间
        [
            (Action.FOLD, 0.9),
            (Action.CHECK_CALL, 0.1),
            (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0),
                (Action.RAISE_3_4_POT, 0),
                (Action.RAISE_POT, 0),
                (Action.RAISE_3_2_POT, 0),
                (Action.RAISE_DOUBLE_POT, 0),
            ]
        ],
        [
            (Action.FOLD, 0.01),
            (Action.CHECK_CALL, 0.7),
            (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.01),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.4),
                (Action.RAISE_3_4_POT, 0.3),
                (Action.RAISE_POT, 0.15),
                (Action.RAISE_3_2_POT, 0.1),
                (Action.RAISE_DOUBLE_POT, 0.08),
            ],
        ],
        [
            (Action.FOLD, 0.005),
            (Action.CHECK_CALL, 0.5),
            (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.3),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],
        [
            (Action.FOLD, 0.0),
            (Action.CHECK_CALL, 0.2),
            (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.2),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],

    ],
    [
        40,
        [-0.00001, 0.6, 0.75, 0.8, 1.01],  # winrate 区间
        [
            (Action.FOLD, 0.85),
            (Action.CHECK_CALL, 0.15),
            (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0),
                (Action.RAISE_3_4_POT, 0),
                (Action.RAISE_POT, 0),
                (Action.RAISE_3_2_POT, 0),
                (Action.RAISE_DOUBLE_POT, 0),
            ]
        ],
        [
            (Action.FOLD, 0.01),
            (Action.CHECK_CALL, 0.7),
            (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.01),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.4),
                (Action.RAISE_3_4_POT, 0.3),
                (Action.RAISE_POT, 0.15),
                (Action.RAISE_3_2_POT, 0.1),
                (Action.RAISE_DOUBLE_POT, 0.08),
            ],
        ],
        [
            (Action.FOLD, 0.005),
            (Action.CHECK_CALL, 0.5),
            (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.3),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],
        [
            (Action.FOLD, 0.0),
            (Action.CHECK_CALL, 0.2),
            (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.2),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],

    ],
    [
        80,
        [-0.00001, 0.7, 0.75, 0.82, 1.01],  # winrate 区间
        [
            (Action.FOLD, 0.6),
            (Action.CHECK_CALL, 0.4),
            (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0),
                (Action.RAISE_3_4_POT, 0),
                (Action.RAISE_POT, 0),
                (Action.RAISE_3_2_POT, 0),
                (Action.RAISE_DOUBLE_POT, 0),
            ]
        ],
        [
            (Action.FOLD, 0.01),
            (Action.CHECK_CALL, 0.7),
            (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.01),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.4),
                (Action.RAISE_3_4_POT, 0.3),
                (Action.RAISE_POT, 0.15),
                (Action.RAISE_3_2_POT, 0.1),
                (Action.RAISE_DOUBLE_POT, 0.08),
            ],
        ],
        [
            (Action.FOLD, 0.005),
            (Action.CHECK_CALL, 0.5),
            (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.05),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.3),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],
        [
            (Action.FOLD, 0.0),
            (Action.CHECK_CALL, 0.2),
            (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
            (Action.ALL_IN, 0.1),
            # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
            [
                (Action.RAISE_HALF_POT, 0.1),
                (Action.RAISE_3_4_POT, 0.1),
                (Action.RAISE_POT, 0.2),
                (Action.RAISE_3_2_POT, 0.3),
                (Action.RAISE_DOUBLE_POT, 0.3),
            ],
        ],

    ],
    [10000000]
    # [
    #     [0.41, 0.75, 1.01],
    #     [Action.CHECK_CALL, Action.RAISE_POT],
    # ],
    # [
    #     [0.5, 0.85, 0.9, 1.01],
    #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    # ],
    # [
    #     [0.6, 0.85, 0.92, 1.01],
    #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    # ],
    # [
    #     [0.65, 0.9, 0.93, 1.01],
    #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    # ],
    # [
    #     [0.72, 0.9, 0.95, 1.01],
    #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    # ],

]
#
# strategy_data_v2_3 = [
#     [
#         0,
#         [0.55, 0.78, 1.01],
#         [Action.CHECK_CALL, Action.RAISE_POT],
#     ],
#     [
#         20,
#         [0.65, 0.85, 0.95, 1.01],
#         [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     ],
#     [
#         40,
#         [0.75, 0.87, 0.95, 1.01],
#         [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     ],
#     [
#         60,
#         [0.8, 0.9, 0.95, 1.01],
#         [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     ],
#     [
#         80,
#         [0.85, 0.9, 0.95, 1.01],
#         [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     ],
#     [
#         10000,
#     ]
# ]

strategy_data_v2 = [
    ([0, 3, 4, 5], strategy_data_v2_0),
    # ([0], strategy_data_v2_0),
    # ([3, 4, 5], strategy_data_v2_3),
]