import pandas as pd

from core.game.action import Action, rl_action_to_comm, to_comm_action_str
from core.game.game_base import GameType


class PlayerInfo:
    def __init__(self,
                 id=0,
                 chips_remain=0,
                 chips_to_desk=0
                 ):
        self.id: int = id
        self.chips_remain: int = chips_remain
        self.chips_to_desk: int = chips_to_desk

    def __str__(self):
        return f'"id": {self.id}, "chips_remain": {self.chips_remain}, "chips_to_desk": {self.chips_to_desk}'


class ActionInfo:
    def __init__(self,
                 player_id=0,
                 stage=0,
                 action=0,
                 num=0,
                 after_remain_chips=0,
                 after_pot=0,
                 rl_raw_action=0
                 ):
        self.player_id: int = player_id
        self.stage: int = stage
        self.action: int = action
        self.num: int = num
        self.after_remain_chips: int = after_remain_chips
        self.after_pot: int = after_pot
        self.rl_raw_action: int = rl_raw_action

    def to_dict(self):
        return {
            'player_id': self.player_id,
            'stage': self.stage,
            'action': self.action,
            'num': self.num,
            'after_remain_chips': self.after_remain_chips,
            'after_pot': self.after_pot
        }


class State:
    def __init__(self,
                 players,
                 my_id=0,
                 small_blind=1,
                 ante=0,
                 my_hand_cards=None,
                 public_cards=None,
                 actions=None,
                 legal_actions=None,
                 dealer_id=0,
                 action_history=None,
                 game_type=GameType.HOLDEM.value,
                 ):
        self.players: list[PlayerInfo] = players
        self.my_id: int = my_id
        self.small_blind: int = small_blind
        self.ante: int = ante
        self.my_hand_cards: list[str] = my_hand_cards
        if self.my_hand_cards is None:
            self.my_hand_cards = []
        self.public_cards: list[str] = public_cards
        if self.public_cards is None:
            self.public_cards = []
        self.actions: list[ActionInfo] = actions
        if self.actions is None:
            self.actions = []
        self.legal_actions: list[int] = legal_actions
        self.dealer_id: int = dealer_id
        self.action_history = action_history
        if self.action_history is None:
            self.action_history = [[] for _ in range(len(players))]

        self.game_type: GameType = GameType(game_type)

        self.pot: int = 0
        for i in range(len(players)):
            self.pot += players[i].chips_to_desk

        if self.legal_actions is None:
            self.legal_actions = [int(a.value) for a in Action]

    def my_remain_chips(self):
        return self.players[self.my_id].chips_remain

    def my_chips_to_desk(self):
        return self.players[self.my_id].chips_to_desk

    def calc_legal_actions(self):

        diff = self.get_diff_chips()
        virtual_pot = self.pot + diff
        remain_chip = self.my_remain_chips()

        legal_actions = [int(Action.FOLD.value), int(Action.CHECK_CALL.value)]
        full_action_costs = [0, diff]
        if remain_chip <= diff:
            full_action_costs[1] = remain_chip
            return legal_actions, full_action_costs

        raw_remained_chips = remain_chip
        remain_chip = remain_chip - diff

        raise_values = [int(virtual_pot / 2), int(virtual_pot * 3 / 4), virtual_pot, int(virtual_pot * 3 / 2),
                        virtual_pot * 2, remain_chip]
        for i, value in enumerate(raise_values):
            legal_actions.append(int(i + Action.RAISE_HALF_POT.value))
            full_action_costs.append(diff + value)
            if remain_chip <= value:
                full_action_costs[-1] = raw_remained_chips
                break
        # if [int(Action.ALL_IN.value) not in legal_actions]:
        #     legal_actions.append(int(Action.ALL_IN.value))
        #     full_action_costs.append(diff + remain_chip)
        # print('*******state*******')
        return legal_actions, full_action_costs

    def get_diff_chips(self):
        my_chips_to_desk = 0
        max_chips_to_desk = -1
        for i in range(len(self.players)):
            player = self.players[i]
            if player.id == self.my_id:
                my_chips_to_desk = player.chips_to_desk
            if player.chips_to_desk > max_chips_to_desk:
                max_chips_to_desk = player.chips_to_desk
        return max_chips_to_desk - my_chips_to_desk

    def get_cur_stage(self) -> int:
        count = len(self.public_cards)
        if count == 0:
            return 0
        if count == 3:
            return 1
        if count == 4:
            return 2

        return 3

    def to_dict(self):
        return {
            'players': [player.__dict__ for player in self.players],
            'my_id': int(self.my_id),
            'dealer_id': int(self.dealer_id),
            'small_blind': int(self.small_blind),
            'ante': int(self.ante),
            'my_hand_cards': self.my_hand_cards,
            'public_cards': self.public_cards,
            'actions': [action.__dict__ for action in self.actions],
            'legal_actions': self.legal_actions,
            'action_history': self.action_history,
            'game_type': int(self.game_type.value),
        }

    def generate_comm_action(self, action: Action, return_rl_action=False):
        diff = self.get_diff_chips()
        remain_chip = self.my_remain_chips()
        virtual_pot = self.pot + diff

        action_code, num = rl_action_to_comm(action, diff, remain_chip, virtual_pot)

        if return_rl_action:
            action_code = int(action.value)
        return action_code, num

    def do_call_if_not_need_pay(self, action: Action) -> Action:
        if action != Action.FOLD:
            return action
        diff = self.get_diff_chips()
        print("diff:", diff)
        if diff == 0:
            return Action.CHECK_CALL
        return action

    @staticmethod
    def from_dict(data):
        # 使用get的方式，避免外部使用json序列化时 omitempty 忽略了该字段的序列化的场景
        players = [PlayerInfo(**p) for p in data['players']]
        dealer_id = data.get('dealer_id', 0)
        my_id = data.get('my_id', 0)
        small_blind = data.get('small_blind', 1)
        ante = data.get('ante', 0)
        my_hand_cards = data.get('my_hand_cards', [])
        public_cards = data.get('public_cards', [])
        action_dict = data.get('actions', [])
        actions = [ActionInfo(**a) for a in action_dict]
        legal_actions = data.get("legal_actions", None)
        action_history = data.get("action_history", None)
        game_type = data.get("game_type", GameType.HOLDEM.value)
        return State(
            players=players,
            my_id=my_id,
            small_blind=small_blind,
            ante=ante,
            my_hand_cards=my_hand_cards,
            public_cards=public_cards,
            actions=actions,
            legal_actions=legal_actions,
            dealer_id=dealer_id,
            action_history=action_history,
            game_type=game_type
        )

    @staticmethod
    def parse_input(input_dict: dict):
        state = State.from_dict(input_dict["inputs"])
        params = input_dict.get("params", {})
        return_rl_action = params.get("return_rl_action", False)
        return state, return_rl_action


def print_state(state: State):
    print(f"my_id: {state.my_id}, small_blind: {state.small_blind}, ante: {state.ante}, dealer_id: {state.dealer_id}")
    print(f"my_hand_cards: {state.my_hand_cards}, public_cards: {state.public_cards}")
    print(f"legal_actions: {state.legal_actions}")
    for p in state.players:
        print(f"id: {p.id}, chips_remain: {p.chips_remain}, chips_to_desk: {p.chips_to_desk}")
    print("actions:")
    data = []
    for a in state.actions:
        d = [a.player_id, a.stage, a.action, a.num, a.after_remain_chips, a.after_pot, a.rl_raw_action]
        data.append(d)

    columns = ["player_id", "stage", "action", "num", "after_remain_chips", "after_pot", "rl_raw_action"]
    df = pd.DataFrame(data, columns=columns)
    print(df.to_string())


def print_actions(actions, my_id):
    data = []
    title = ['stage', 'player_id', 'action', 'chips']
    for a in actions:
        player_name = f'me:{a.player_id}' if a.player_id == my_id else f'oppo:{a.player_id}'
        data.append([a.stage, player_name, to_comm_action_str(a.action), a.num])
    df = pd.DataFrame(data, columns=title)
    print(df.to_string())


if __name__ == '__main__':
    pass
