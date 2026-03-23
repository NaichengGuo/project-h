from collections import deque

from core.coder.state import ActionInfo
from rlcard.envs import consts


class HistoryActionRecord(object):
    def __init__(self, player_num, max_len=consts.PREVIOUS_INFO_NP_SIZE):
        self.player_num = player_num
        # 这里记录的index顺序和原始的agents顺序一致
        self.action_record = [deque(maxlen=max_len) for _ in range(player_num)]

    def add_history(self, history_record: list[ActionInfo], payoffs, to_org_func, small_blind):
        new_history_action = [[] for _ in range(self.player_num)]

        for i in range(self.player_num):
            meta_info = [small_blind, int(payoffs[i])]
            new_history_action[i].append(meta_info)

        for action in history_record:
            if action.action < 0:
                continue
            player_id = action.player_id
            data = [
                action.stage,
                action.action,
                action.num,
            ]
            new_history_action[player_id].append(data)

        for i in range(self.player_num):
            if len(new_history_action[i]) == 0:
                continue
            self.action_record[to_org_func(i)].append(new_history_action[i])

    def get_history_snap(self, to_cur_func):
        new_history_action = [[] for _ in range(self.player_num)]
        for i in range(len(self.action_record)):
            new_history_action[to_cur_func(i)] = list(self.action_record[i])

        return new_history_action

    def clear(self):
        for record in self.action_record:
            record.clear()
