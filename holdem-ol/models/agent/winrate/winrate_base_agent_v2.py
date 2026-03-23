from core.game.action import Action
from models.agent.winrate.winrate_base_agent import WinrateBaseAgent

strategy_data_v2_0 = [
    [
        0,  # pot
        [0.38, 0.54, 0.571, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        10,
        [0.47, 0.571, 0.587, 1.01],  # winrate  #弃牌快了一点吧？
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        60,
        [0.570, 0.67, 1.01],
        [Action.CHECK_CALL, Action.ALL_IN], #池子大了就不会 raise 了，只有 allin 这一个选择，why？
    ],
    [
        10000,
    ]
]

strategy_data_v2_3 = [
    [
        0,  # pot
        [0.55, 0.61, 0.7, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        10,
        [0.60, 0.72, 0.8, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        40,
        [0.64, 0.80, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT],
    ],
    [
        60,
        [0.70, 0.88, 1.01],
        [Action.CHECK_CALL, Action.ALL_IN], 
    ],
    [
        10000,
    ]
]

strategy_data_v2_4 = [
    [
        0,  # pot
        [0.56, 0.8, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_POT],
    ],
    [
        10,
        [0.65, 0.85, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT],
    ],
    [
        40,
        [0.70, 0.87, 1.01],
        [Action.CHECK_CALL, Action.RAISE_HALF_POT],
    ],
    [
        60,
        [0.75, 0.9, 1.01],
        [Action.CHECK_CALL, Action.ALL_IN],
    ],
    [
        10000,
    ]
]

strategy_data_v2_5 = [
    [
        0,  # pot
        [0.57, 0.75, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_POT],
    ],
    [
        20,
        [0.7, 0.85, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT],
    ],
    [
        60,
        [0.78, 0.9, 1.01],
        [Action.CHECK_CALL, Action.ALL_IN],
    ],
    [
        10000,
    ]
]

strategy_data_v2 = [
    ([0], strategy_data_v2_0),
    ([3], strategy_data_v2_3),
    ([4], strategy_data_v2_4),
    ([5], strategy_data_v2_5),
]


# 基准的全看概率的agent
class WinrateBaseAgentV2(WinrateBaseAgent):
    ''' A random agent. Random agents is for running toy examples on the card games
    '''

    def get_strategy_data(self):
        return strategy_data_v2

    def get_name(self):
        return f"winrate_v2"
