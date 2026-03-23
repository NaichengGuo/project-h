import os

import mlflow
from mlflow.models import infer_signature

from core.coder.predict import PredictInput
from core.game.action import PlayerAction, Action, RawAction
from core.game.card import CardCode
from core.winrate.winrate_wrapper import WinrateWrapper
from models.mm.tsmodel import TsModel
from models.mm.transform import Transform
import numpy as np
import torch
import pandas as pd
from core.game import strategy

input_example = {
    "players": [
        {
            "id": 1,
            "chips_remain": 19300,
            "chips_to_desk": 700
        }
    ],
    "my_id": 0,
    "small_blind": 50,
    "ante": 0,
    "my_hand_cards": [
        'Jc', 'Th'
    ],
    "public_cards": [
        'Qc', 'Ts', '9c'
    ],
    "actions": [
        {
            "player_id": 1,
            "stage": 2,
            "action": 3,
            "num": 350
        }
    ],
    "legal_actions": [1, None]  # 包含有None代表该字段是可选的
}

output_example = {"action": 2}

pip_requirements = [
    "mlflow==2.11.3",
    "cloudpickle==3.0.0",
    "numpy==1.26.4",
    "pandas==2.2.1",
    "torch==2.2.2",
    "grpcio==1.62.1",
    "protobuf==4.25.3",
    "cachetools==5.3.3"
]


def print_state(state):
    print(f"state['raw_hand'] : {state['raw_hand']}")
    print(f"state['raw_public_cards'] : {state['raw_public_cards']}")
    print(f"state['hand'] : {state['hand']}")
    print(f"state['dealer_id'] : {state['dealer_id']}")
    print(f"state['player_id'] : {state['player_id']}")
    print(f"state['legal_actions'] : {state['legal_actions']}")
    action_history = state['action_history']
    print("action_history:")
    for a in action_history:
        print(a)


class TexasModel(mlflow.pyfunc.PythonModel):
    model = None

    def __init__(self):
        self.device = None
        self.winrate_mgr = None

    def load_context(self, context):
        model_path = context.artifacts["texas_model"]
        self.model = TsModel.load(model_path)
        self.model.eval()
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.winrate_mgr = WinrateWrapper(real_time_cal_win_rate=True)
        print("finish loading model:")

    def predict(self, context, model_input: pd.DataFrame, params=None):
        print("----predict----")
        model_input_dict = model_input.to_dict(orient='records')[0]
        if params is not None:
            print(f"params[real_time]", params.get("real_time", 0))

        state = TexasModel.from_json_state(model_input_dict)
        action_keys, values = self.__predict(state)
        action = action_keys[np.argmax(values)]

        print(f"model_input_dict : {model_input_dict}")
        print_state(state)
        print(f"action_choice : {Action(action)}, hand: {state['raw_hand']}, public_cards: {state['raw_public_cards']}, legal_actions: {state['legal_actions']}")

        return {"action": int(action)}

    def __predict(self, state):

        raw_hand = state["raw_hand"]
        raw_public_cards = state["raw_public_cards"]
        state['comm_cards_ext'] = self._to_comm_matrix(raw_hand, raw_public_cards)

        print(f"state['comm_cards_ext'] : {state['comm_cards_ext']}" )

        static_info, comm_cards_info, action_history_info = Transform.convert_full_info(state)

        legal_actions = state['legal_actions']
        actions = Transform.convert_legal_actions_one_hot_list(legal_actions)

        legal_action_size = len(legal_actions)
        static_info = np.repeat(static_info[np.newaxis, :], legal_action_size, axis=0)
        comm_cards_info = np.repeat(comm_cards_info[np.newaxis, :], legal_action_size, axis=0)
        action_history_info = np.repeat(action_history_info[np.newaxis, :], legal_action_size, axis=0)

        # Predict Q values
        static_info = torch.from_numpy(static_info).to(self.device)
        actions = torch.from_numpy(actions).to(self.device)
        comm_cards_info = torch.from_numpy(comm_cards_info).to(self.device)
        action_history_info = torch.from_numpy(action_history_info).to(self.device)
        values = self.forward(static_info, actions, comm_cards_info, action_history_info)
        return np.array([act.value for act in legal_actions], dtype=np.int8), values.cpu().detach().numpy()

    def forward(self, static_info, action, comm_cards, act_history):
        comm_cards_output = self.model.comm_cards_lstm(comm_cards)
        act_history_output = self.model.act_history_lstm(act_history)

        _input = torch.cat((static_info, action, comm_cards_output, act_history_output), dim=1)
        return self.model.fcl(_input)

    def calculate_win_rate(self, hand, public_cards):
        return self.winrate_mgr.get_winrate(hand, public_cards)

    def _to_comm_matrix(self, hand, public_cards):
        public_cards_values = CardCode.to_values(public_cards)
        winrate_0 = self.calculate_win_rate(hand, [])
        line0 = [52, 52, 52, 52, 52, winrate_0]
        if len(public_cards) == 0:
            return [line0]

        winrate_1 = self.calculate_win_rate(hand, public_cards[:3])
        line1 = [*public_cards_values[:3], 52, 52, winrate_1]

        if len(public_cards) == 3:
            return [line0, line1]

        winrate_2 = self.calculate_win_rate(hand, public_cards[:4])
        line2 = [*public_cards_values[:4], 52, winrate_2]

        if len(public_cards) == 4:
            return [line0, line1, line2]

        if len(public_cards) == 5:
            winrate_3 = self.calculate_win_rate(hand, public_cards[:5])
            line3 = [*public_cards_values[:5], winrate_3]
            return [line0, line1, line2, line3]

    @staticmethod
    def custom_log_model(model_name, model: TsModel):

        folder_path = "local_data"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        model_save_path = f"{folder_path}/texas_model.pt"
        model.save_model(model_save_path)
        artifacts = {"texas_model": model_save_path}
        inferred_signature = infer_signature(input_example, output_example, None)
        # print(f"inferred_signature : {inferred_signature}")
        mlflow.pyfunc.log_model(artifact_path=model_name,
                                python_model=TexasModel(),
                                signature=inferred_signature,
                                artifacts=artifacts,
                                pip_requirements=pip_requirements,
                                code_path=["models", "core"])

    @staticmethod
    def data_frame_to_json(pd_data_frame):
        return pd_data_frame.to_dict(orient='records')

    @staticmethod
    def from_json_state(state):

        predict_data = PredictInput.from_dict(state)
        players = predict_data.players
        id_map = {}
        for i in range(len(players)):
            id_map[players[i].id] = i

        player0_id = id_map[players[0].id]
        player1_id = id_map[players[1].id]
        dealer_id = player1_id
        player_id = id_map[predict_data.my_id]

        hand = predict_data.my_hand_cards
        public_cards = predict_data.public_cards
        actions = predict_data.actions
        small_blind = predict_data.small_blind

        all_chips_0 = players[0].chips_remain + players[0].chips_to_desk
        all_chips_1 = players[1].chips_remain + players[1].chips_to_desk
        pot = players[0].chips_to_desk + players[1].chips_to_desk

        new_actions = [
            PlayerAction(0, player0_id, int(RawAction.Sb), 1, (all_chips_0 - small_blind) / small_blind),
            PlayerAction(0, player1_id, int(RawAction.Bb), 2, (all_chips_1 - 2 * small_blind) / small_blind),
        ]

        remain_chips = {player0_id: all_chips_0 - small_blind, player1_id: all_chips_1 - 2 * small_blind}
        tmp_pot = 1 + 2 # small_bid + big_bid

        for a in actions:
            pid = id_map[a.player_id]
            action = a.action
            num = a.num
            if action == 5 and num == 0:
                num = remain_chips[pid]

            remain_chips[pid] = remain_chips[pid] - num
            rl_action = TexasModel.comm_action_to_rl(action, num, tmp_pot)
            tmp_pot += num
            new_actions.append(
                PlayerAction(a.stage, pid, int(rl_action.value), num / small_blind, remain_chips[pid] / small_blind))

        new_state = {}

        new_state['raw_hand'] = CardCode.cmm_to_rl_strs(hand)
        new_state['raw_public_cards'] = CardCode.cmm_to_rl_strs(public_cards)
        new_state['hand'] = CardCode.to_values(new_state['raw_hand'])
        new_state['action_history'] = new_actions
        new_state['dealer_id'] = dealer_id
        new_state['player_id'] = player_id

        if predict_data.legal_actions is not None:
            legal_actions = [Action(a) for a in state["legal_actions"]]
            print(f"found legal_actions in state : {legal_actions}")
        else:
            legal_actions = strategy.calc_legal_actions(state)
            print(f"no found legal_actions in state, reconstruct to {legal_actions}")
        new_state['legal_actions'] = legal_actions

        return new_state

    @staticmethod
    def comm_action_to_rl(action, num, pot):
        if action == 1:
            return Action.FOLD
        if action == 2 or action == 3:
            return Action.CHECK_CALL
        if action == 5:
            return Action.ALL_IN

        if num >= pot:
            return Action.RAISE_POT
        return Action.RAISE_HALF_POT



if __name__ == "__main__":
    state_json = [{
        "players": [
            {
                "id": 1,
                "chips_remain": 19300,
                "chips_to_desk": 700
            },
            {
                "id": 0,
                "chips_remain": 19300,
                "chips_to_desk": 700
            }
        ],
        "my_id": 0,
        "small_blind": 50,
        "ante": 0,
        "my_hand_cards": ["Js", "6c"],
        "public_cards": ["8c", "3d", "2d", "Ac", "Kd"],
        "actions": [
            {
                "player_id": 1,
                "stage": 0,
                "action": 4,
                "num": 150
            },
            {
                "player_id": 0,
                "stage": 0,
                "action": 4,
                "num": 250
            },
            {
                "player_id": 1,
                "stage": 0,
                "action": 3,
                "num": 150
            },
            {
                "player_id": 0,
                "stage": 1,
                "action": 2,
                "num": 0
            },
            {
                "player_id": 1,
                "stage": 1,
                "action": 2,
                "num": 0
            },
            {
                "player_id": 0,
                "stage": 2,
                "action": 4,
                "num": 350
            },
            {
                "player_id": 1,
                "stage": 2,
                "action": 3,
                "num": 350
            }
        ],
        "legal_actions": [1]
    }]

    state = TexasModel.from_json_state(state_json[0])
    print_state(state)

    # t1 = pd.DataFrame(state_json)
    # print(t1)
    # o = t1.to_dict(orient='records')
    # print(o)
    # o2 = o[0]
    # print(o2)
