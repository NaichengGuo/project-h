from core.coder.state import State
from core.game.action import Action, rl_action_to_comm
from models.agent.base.base_agent import BaseAgent
import random
import numpy as np
from core.winrate.winrate_mc import winrate_calculator
from core.winrate.winrate_acc import WinRateProcessorNP_LRU


strategy_data_v2_0 = [
    [
        0,  # pot
        [0.2, 0.44, 0.68, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        10,
        [0.3, 0.58, 0.7, 1.01],  # winrate  #弃牌快了一点吧？
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        40,#池子大
        [0.45, 0.66, 0.8, 1.01],
        [Action.CHECK_CALL,Action.RAISE_POT, Action.ALL_IN],
    ],
    [
        80,#池子大
        [0.65, 0.7, 0.85, 1.01],
        [Action.CHECK_CALL,Action.RAISE_POT, Action.ALL_IN],
    ],
    [
        100000,
    ]
]

strategy_data_v2_3 = [
    [
        0,  # pot
        [0.22, 0.7, 0.8, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        10,
        [0.25, 0.73, 0.85, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        25,
        [0.33, 0.75, 0.87,1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT,Action.CHECK_CALL],
    ],
    [
        40,
        [0.37, 0.78, 0.88, 1.01],
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.CHECK_CALL],
    ],
    [
        60,
        [0.60, 0.7, 0.9, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT, Action.CHECK_CALL],
    ],
    [
        100000,
    ]
]


strategy_data_v2_5 = [
    [
        0,  # pot
        [0.35, 0.63, 0.75, 1.01],  # winrate
        [Action.CHECK_CALL, Action.RAISE_HALF_POT,Action.RAISE_POT],
    ],
    [
        20,
        [0.45, 0.68, 0.9, 1.01],  # winrate  #可能过低
        [Action.CHECK_CALL, Action.RAISE_HALF_POT,Action.RAISE_POT],
    ],
    [
        40,
        [0.57, 0.73, 0.93, 1.01],
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        60,
        [0.59,0.8,0.95,1.01],
        [Action.CHECK_CALL, Action.RAISE_HALF_POT, Action.RAISE_POT],
    ],
    [
        80,
        [0.75, 0.85, 0.96, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    ],
    [
        150,
        [0.85, 0.9, 0.95, 1.01],
        [Action.CHECK_CALL, Action.RAISE_POT, Action.ALL_IN],
    ],
    [
        100000,
    ]
]

strategy_data_v2 = [
    ([0], strategy_data_v2_0),
    ([3], strategy_data_v2_3),
    ([4], strategy_data_v2_3),
    ([5], strategy_data_v2_5),
]


class WinrateBaseAgentNeutral(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}
        self.win_rate_cal = winrate_calculator()
        board_path = config.get("board_path", './')
        self.win_rate_acc_cal = WinRateProcessorNP_LRU(board_path)
        # === Bluff 相关配置 ===
        self.enable_bluff = config.get("enable_bluff", True)
        self.bluff_frequency = config.get("bluff_frequency", 0.05)
        self.bluff_min_equity = config.get("bluff_min_equity", 0.20)
        self.bluff_max_equity = config.get("bluff_max_equity", 0.45)
        self.no_bluff_phases = config.get("no_bluff_phases", [0])     # 禁止诈唬的阶段：# 0: preflop, 3: flop, 4: turn, 5: river
        self.randomize_threshold_noise = config.get("randomize_threshold_noise", 0.05)
        self.random_action_prob =  config.get("random_action_prob", 0.03) #
        self.smoothing_window = config.get("smoothing_window", 0.08) #
        self.valid_bluff_actions = config.get("valid_bluff_actions",[Action.RAISE_HALF_POT,Action.RAISE_POT,Action.ALL_IN])
        self.stage_map= {0:0,3:1,4:2,5:3}
        self.raise_list=  [Action.RAISE_HALF_POT,Action.RAISE_3_4_POT,Action.RAISE_POT,Action.RAISE_3_2_POT,Action.RAISE_DOUBLE_POT]
        self.bet_threshold_table = [
            [0.0, 0.3,0.5,0.6, 0.7, 0.8, 0.9, 0.95, 1.01],  # 胜率区间
            [10, 30, 50,80, 200, 400, 500, 1000000]  # 对应最大下注金额
        ]
    def step(self, state: State):
        n_players=len(state.players)
        hands = state.my_hand_cards
        public_cards = state.public_cards
        legal_actions = state.legal_actions
        pot = state.pot / (state.small_blind * 1)
        history_seq = state.actions
        # 获取ation
        final_action = self.decide_action(hands, public_cards, pot,n_players,legal_actions,history_seq,state.my_id,state.small_blind,state)
        return state.do_call_if_not_need_pay(final_action)

    def eval_step(self, state: State):
        return self.step(state)

    def calc_win_rate(self, hands, public_cards,n_players=2):
        hands=self.win_rate_cal.stander_format_trans(hands)
        public_cards=self.win_rate_cal.stander_format_trans(public_cards)
        winrate,tierate=self.win_rate_cal.calculate_equity(hands,public_cards,n_players)
        return winrate+1/2*tierate #self.win_rate_mgr.get_winrate(hands, public_cards)

    def get_strategy_data(self):
        return strategy_data_v2

    def decide_raise(self,legal_actions,total_raise_cnt, current_stage_raise_cnt,current_action):
        legal_actions_list=[]
        action_map={}
        for i in legal_actions:
            act=Action(i)
            if act not in [Action.ALL_IN,Action.FOLD]:
                legal_actions_list.append(act)
                action_map[act]=1
        if current_action==Action.RAISE_HALF_POT: #[0,4,2,1,1,1,0]
            if Action.RAISE_HALF_POT in action_map:
                action_map[Action.RAISE_HALF_POT]+=1
            if Action.RAISE_3_4_POT in action_map:
                action_map[Action.RAISE_3_4_POT]+=1
        elif current_action==Action.RAISE_POT: #[0,1,1,4,3,2,0]
            if Action.RAISE_POT in action_map:
                action_map[Action.RAISE_POT]+=3
            if Action.RAISE_3_2_POT in action_map:
                action_map[Action.RAISE_3_2_POT]+=2
            if Action.RAISE_DOUBLE_POT in action_map:
                action_map[Action.RAISE_DOUBLE_POT]+=1
        if current_stage_raise_cnt>=2:
            action_map[Action.CHECK_CALL]+=100
        else:
            action_map[Action.CHECK_CALL]=0
        sum_p=sum(list(action_map.values()))
        p_list=[i/sum_p for i in list(action_map.values())]
        #print(f'action_map:{action_map.keys()},prob:{p_list}')
        return np.random.choice(list(action_map.keys()), p=p_list)

    def parse_history(self, history_seq,com_cards_size,my_id):
        total_raise_cnt=0
        current_stage_raise_cnt=0
        fold_cnt=0
        for act in history_seq:
            if act.player_id == my_id and act.action>=0 and Action(act.action) in self.raise_list:
                total_raise_cnt+=1
            if act.player_id==my_id and act.action>=0 and act.stage == self.stage_map[com_cards_size] and Action(act.action) in self.raise_list:
                current_stage_raise_cnt+=1
            if act.action>=0 and Action(act.action)==Action.FOLD:
                fold_cnt+=1
        return total_raise_cnt,current_stage_raise_cnt,fold_cnt


    def decide_action(self, hands, public_cards, pot,n_players=2,legal_actions=None,history_seq=None,my_id=None,small_blind=None,state=None) -> Action:
        if len(public_cards)<5:
            win_rate = self.win_rate_acc_cal.get_winrate(hands, public_cards)
        else:
            win_rate = self.calc_win_rate(hands, public_cards)
        noise = random.uniform(-self.randomize_threshold_noise, self.randomize_threshold_noise)
        noisy_win_rate = max(0.0, min(1.0, win_rate + noise))
        #print(f'win_rate:{win_rate}, noisy_win_rate:{noisy_win_rate}')

        #读取此轮 max_bet
        max_bet = 0
        for i in range(len(self.bet_threshold_table[0]) - 1):
            if self.bet_threshold_table[0][i] <= noisy_win_rate < self.bet_threshold_table[0][i+1]:
                max_bet = self.bet_threshold_table[1][i] * small_blind # real chips 筹码数/金额
                break


        legal_action_objs = [Action(i) for i in legal_actions]
        if Action.ALL_IN not in legal_actions:
            legal_action_objs.append(Action.ALL_IN)
        #print(f'legal_action_objs:{legal_action_objs}')
        filtered_actions = []
        if max_bet > 0:  # 如果有设置最大下注限制
            for act in legal_action_objs:
                if act in [Action.FOLD]:
                    filtered_actions.append(act)
                else:
                    action_code, bet_amount = state.generate_comm_action(act)
                    if bet_amount <= max_bet:
                        #print(f'action_code:{act},bet_amount:{bet_amount},max_bet:{max_bet}')
                        filtered_actions.append(act)

        # legal_action_objs = [Action(i) for i in legal_actions]
        if random.random() < self.random_action_prob: #random strategy
            #print(f'------random strategy------,{filtered_actions}')
            return random.choice(filtered_actions)
        current_phase = len(public_cards)  # 0: preflop, 3: flop, 4: turn, 5: river

        # 获取对应阶段的策略表
        sd = [] #当前轮策略
        tmp_strategy_data = self.get_strategy_data()
        for phases, strategy in tmp_strategy_data:
            if current_phase in phases:
                sd = strategy
                break
        #历史行为解析
        total_raise_cnt, current_stage_raise_cnt,fold_cnt = self.parse_history(history_seq, current_phase, my_id)
        # alive player
        pot=pot/(n_players-fold_cnt)
        # === 正常决策流程 ===
        action = Action.FOLD
        for i in range(len(sd) - 1):
            if sd[i][0] < pot <= sd[i+1][0]:
                #print(f'check pot{pot},{sd[i][0]},{sd[i+1][0]}')
                for j in range(len(sd[i][1]) - 1):
                    if sd[i][1][j] <= noisy_win_rate < sd[i][1][j + 1]:
                        action = sd[i][2][j]
                        #print(f'action:{action}')
                        break
                break
        #print(f'--------org action-----:{action},pot:{pot}')
        # 如果原action不在过滤后的动作中，则降级为CHECK_CALL
        if action not in filtered_actions:
            action = filtered_actions[-1]
            #action = Action.CHECK_CALL if Action.CHECK_CALL in filtered_actions else filtered_actions[0]
        # == raise 多样性
        if action in [Action.RAISE_HALF_POT,Action.RAISE_3_4_POT,Action.RAISE_POT,Action.RAISE_3_2_POT,Action.RAISE_DOUBLE_POT]:
            #print(f'add action diversity...........')
            action = self.decide_raise(filtered_actions,total_raise_cnt, current_stage_raise_cnt,action)
        #=== Bluff ===
        if (action == Action.CHECK_CALL and Action.RAISE_POT in filtered_actions and self.enable_bluff and
                current_phase not in self.no_bluff_phases and
                self.bluff_min_equity <= noisy_win_rate < self.bluff_max_equity and
                random.random() < self.bluff_frequency):
            # 从可用的诈唬动作中随机选一个
            #print(f'-----------bluff----------')
            bluff_action = random.choice(self.valid_bluff_actions)
            return bluff_action
        #print(f'action return......:{action}')
        return action
    def get_name(self):
        return f"winrate-neutral"

    def get_version(self):
        return "ev-neutral-250908"
