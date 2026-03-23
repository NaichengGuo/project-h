import numpy as np

from core.coder.predict import PredictInput
from core.game.action import Action, rl_action_to_comm
from core.winrate.winrate_wrapper import WinrateWrapper
from core.game.card import CardCode
from models.agent.winrate.winrate_base_agent import WinrateBaseAgent
from models.agent.winrate.strategy_data_v2 import strategy_data_v2, base_strategy, decide_raise


# strategy_data_v2_0 = [
#     [0, 4, 20, 40, 60, 80, 100000000], # pot 区间
#     [
#         [-0.00001, 0.39, 0.6, 0.75, 1.00001],  # winrate 区间
#         [
#             (Action.FOLD, 0.95),
#             (Action.CHECK_CALL, 0.05),
#             (Action.RAISE_POT, 0),  # 代表raise的大类，而不仅仅是raise pot
#             (Action.ALL_IN, 0),
#             # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
#             [
#                 (Action.RAISE_HALF_POT, 0),
#                 (Action.RAISE_3_4_POT, 0),
#                 (Action.RAISE_POT, 0),
#                 (Action.RAISE_3_2_POT, 0),
#                 (Action.RAISE_DOUBLE_POT, 0),
#             ]
#         ],
#         [
#             (Action.FOLD, 0.01),
#             (Action.CHECK_CALL, 0.7),
#             (Action.RAISE_POT, 0.15),  # 代表raise的大类，而不仅仅是raise pot
#             (Action.ALL_IN, 0.01),
#             # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
#             [
#                 (Action.RAISE_HALF_POT, 0.4),
#                 (Action.RAISE_3_4_POT, 0.3),
#                 (Action.RAISE_POT, 0.15),
#                 (Action.RAISE_3_2_POT, 0.1),
#                 (Action.RAISE_DOUBLE_POT, 0.08),
#             ],
#         ],
#         [
#             (Action.FOLD, 0.005),
#             (Action.CHECK_CALL, 0.5),
#             (Action.RAISE_POT, 0.5),  # 代表raise的大类，而不仅仅是raise pot
#             (Action.ALL_IN, 0.05),
#             # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
#             [
#                 (Action.RAISE_HALF_POT, 0.1),
#                 (Action.RAISE_3_4_POT, 0.1),
#                 (Action.RAISE_POT, 0.3),
#                 (Action.RAISE_3_2_POT, 0.3),
#                 (Action.RAISE_DOUBLE_POT, 0.3),
#             ],
#         ],
#         [
#             (Action.FOLD, 0.0),
#             (Action.CHECK_CALL, 0.2),
#             (Action.RAISE_POT, 8),  # 代表raise的大类，而不仅仅是raise pot
#             (Action.ALL_IN, 0.05),
#             # 当选择 raise 时，下面的概率表示具体的 raise 类型的概率
#             [
#                 (Action.RAISE_HALF_POT, 0.1),
#                 (Action.RAISE_3_4_POT, 0.1),
#                 (Action.RAISE_POT, 0.2),
#                 (Action.RAISE_3_2_POT, 0.3),
#                 (Action.RAISE_DOUBLE_POT, 0.3),
#             ],
#         ],
#
#     ],
#     # [
#     #     [0.41, 0.75, 1.01],
#     #     [Action.CHECK_CALL, Action.RAISE_POT],
#     # ],
#     # [
#     #     [0.5, 0.85, 0.9, 1.01],
#     #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     # ],
#     # [
#     #     [0.6, 0.85, 0.92, 1.01],
#     #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     # ],
#     # [
#     #     [0.65, 0.9, 0.93, 1.01],
#     #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     # ],
#     # [
#     #     [0.72, 0.9, 0.95, 1.01],
#     #     [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
#     # ],
#
# ]
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
#
# strategy_data_v2 = [
#     ([0, 3, 4, 5], strategy_data_v2_0),
#     # ([0], strategy_data_v2_0),
#     # ([3, 4, 5], strategy_data_v2_3),
# ]

def interp(x, x1, x2, y1, y2):
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

def interp_by_ratio(ratio, y1, y2):
    return y1 + (y2 - y1) * ratio

def make_decision(winrate_sds, ratio):
    probs = [0,0,0,0]

    available_actions = []
    for i in range(4):
        wr1 = winrate_sds[i][1]
        # wr2 = winrate_sds[i][2]
        # probs[i] = wr1 + (wr2 - wr1) * ratio
        probs[i] = wr1
        available_actions.append(winrate_sds[i][0])

    sum_value = sum(probs)
    probs = [x / sum_value for x in probs]
    pick = np.random.choice(available_actions, p=probs)
    # print(f"probs: {probs}")
    if pick not in [Action.RAISE_HALF_POT, Action.RAISE_POT, Action.RAISE_DOUBLE_POT]:
        return pick

    return decide_raise(pick)

# 基准的全看概率的agent

class WinrateBaseAgentV2(WinrateBaseAgent):

    def decide_action(self, hands, public_cards, pot) -> Action:
        win_rate = self.calc_win_rate(hands, public_cards)
        # print(f"win_rate: {win_rate}")
        community_card_num = len(public_cards)
        sd = []
        for i in range(len(strategy_data_v2)):
            if community_card_num in strategy_data_v2[i][0]:
                sd = strategy_data_v2[i][1]
                break

        pot_sizes = sd[0]
        winrate_range = sd[1:]
        winrate_data = []
        for i in range(len(pot_sizes) - 1):
            if pot_sizes[i] <= pot < pot_sizes[i + 1]:
                winrate_data = winrate_range[i]
                break

        cur_sd = []
        ratio = 0.0
        for j in range(len(winrate_data) - 1):
            if winrate_data[j] <= win_rate < winrate_data[j + 1]:
                cur_sd = base_strategy[j]
                ratio = (win_rate - winrate_data[j]) / (winrate_data[j + 1] - winrate_data[j])
                break

        return make_decision(cur_sd, ratio)

    def get_name(self):
        return f"winrate_v2(rpc={not self.real_time_win_rate})"

if __name__ == "__main__":
    p = {
        "inputs": {
                "players": [
                    {
                        "id": 21,
                        "chips_remain": 19300,
                        "chips_to_desk": 50
                    },
                    {
                        "id": 20,
                        "chips_remain": 19300,
                        "chips_to_desk": 100
                    }
                ],
                "my_id": 21,
                "small_blind": 50,
                "ante": 0,
                "my_hand_cards": [
                    "As",
                    "Ad"
                ],
                "public_cards": [
                ],
                "actions": [

                ]
            },
            "params": {
                "model_level": 1,
                "player_num": 2
            }
        }
    s = WinrateBaseAgentV2({})
    hands = ["SA", "DA"]
    # a = s.decide_action(hands, [], 2)
    actions = [0 for _ in range(8)]
    for i in range(100):
        a = s.decide_action(hands, [], 81)
        actions[a.value] += 1
    print(actions)