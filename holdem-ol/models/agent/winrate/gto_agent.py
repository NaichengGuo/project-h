from core.coder.state import State
from core.game.action import Action
from core.winrate.winrate_wrapper import WinrateWrapper
from core.game.card import CardCode
from models.agent.base.base_agent import BaseAgent
from treys import Card, Deck, Evaluator
import random
import pickle
import numpy as np


class winrate_calculator:
    def __init__(self):
        super().__init__()
        self.valid_ranks = {'2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a'}
        self.valid_suits = {'h', 'd', 'c', 's'}

    def stander_format_trans(self,cards):
        res=[]
        for card in cards:
            c0,c1=card[0],card[1]
            rank,suit=c1,c0.lower()
            res.append(rank+suit)
        return res

    def calculate_equity(self,hole_cards, community_cards, num_players, num_simulations=1000):
        evaluator = Evaluator()
        deck = Deck()

        # 转换手牌和公共牌为 treys 格式
        hero_cards = [Card.new(card) for card in hole_cards]
        community = [Card.new(card) for card in community_cards]

        # 从牌堆中移除已知的牌
        for card in hero_cards + community:
            deck.cards.remove(card)

        wins = 0
        ties = 0

        for _ in range(num_simulations):
            # 重新洗牌
            simulation_deck = deck.cards.copy()
            random.shuffle(simulation_deck)

            # 为其他玩家发牌
            other_players_cards = []
            for i in range(num_players - 1):
                player_cards = [simulation_deck.pop(), simulation_deck.pop()]
                other_players_cards.append(player_cards)

            # 补齐公共牌
            simulation_community = community.copy()
            remaining_community = 5 - len(simulation_community)
            for _ in range(remaining_community):
                simulation_community.append(simulation_deck.pop())

            # 计算hero的得分
            hero_score = evaluator.evaluate(hero_cards, simulation_community)

            # 计算其他玩家的得分
            other_scores = [evaluator.evaluate(player_cards, simulation_community)
                           for player_cards in other_players_cards]

            # 注意：在 treys 中，分数越低表示牌力越大
            best_score = min([hero_score] + other_scores)

            if hero_score == best_score:
                if other_scores.count(best_score) > 0:
                    ties += 1
                else:
                    wins += 1

        equity = wins / num_simulations
        tie_equity = ties / num_simulations
        return equity, tie_equity

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

class GTOAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None:
            config = {}
        self.win_rate_cal = winrate_calculator()
        with open('./board3_5.pkl', 'rb') as file:  # 打开文件，模式为二进制读取 ('rb')
            self.memo = pickle.load(file)

        # === Bluff 相关配置 ===
        self.enable_bluff = config.get("enable_bluff", True)
        self.bluff_frequency = config.get("bluff_frequency", 0.15)  # 15% 概率诈唬
        self.bluff_min_equity = config.get("bluff_min_equity", 0.20)  # 最低胜率才考虑诈唬
        self.bluff_max_equity = config.get("bluff_max_equity", 0.45)   # 超过这个就不算“弱牌”
        self.no_bluff_phases = config.get("no_bluff_phases", {0})     # 禁止诈唬的阶段：0=preflop
        self.valid_bluff_actions = config.get(
            "valid_bluff_actions",
            [Action.RAISE_HALF_POT, Action.CHECK_CALL,Action.RAISE_POT]
        )

    def pubcard2stage(self,community_cards):
        len_community=len(community_cards)
        if len_community==0:
            return 0
        elif len_community==3:
            return 1
        elif len_community==4:
            return 2
        elif len_community==5:
            return 3
        return None
    def getAction(self,strategy):
        return np.random.choice(list(strategy.keys()), p=list(strategy.values()))

    def actions2historys(self,history_seq, stage, threshold=0.4):
        res = ['s']
        seq = []
        if len(history_seq) == 0:
            return ','.join(res)
        has_check = False
        has_bmin = False
        has_bmax = False
        stage_first_action = None
        bet_count = 0
        fold_count = 0
        bmin = float('inf')
        bmax = 0
        for act in history_seq:
            b_nums = 0
            if not act.stage == stage:  # 直达目标 stage
                continue
            action = act.action
            if stage_first_action is None:
                stage_first_action = act
            if action == 0:  # fold
                fold_count += 1
                continue
            if action == 1:  # check or call
                if act.num == 0:
                    seq.append('check')  # check
                    has_check = True
                else:
                    b_nums = act.num
                    seq.append(f'b{b_nums}')  # call
            if action in [2, 3, 4, 5, 6, 7]:
                bet_count += 1
                b_nums = act.num
                seq.append('b' + str(b_nums))
            if b_nums > 0:
                bmin = min(bmin, b_nums)
                bmax = max(bmax, b_nums)
        if not stage_first_action:
            return ','.join(res)
        pot_begin = stage_first_action.after_pot - stage_first_action.num
        if bmin > 0 and bmin / pot_begin < threshold:
            has_bmin = True
        if bmax / pot_begin > threshold:
            has_bmax = True
        if has_check:
            res.append('check')
        if has_bmin:
            res.append('bmin')
        if has_bmax:
            res.append('bmax')
        return ','.join(res)

    def decide_postflop_action(self, hands, public_cards, history_seq,legal_actions):
        history = self.actions2historys(history_seq,self.pubcard2stage(public_cards)) # 格式转换
        win_rate = self.calc_win_rate(hands, public_cards,2)
        n_bucket= int(win_rate*100//1)
        print(f'history:{history},win_rate:{win_rate},n_bucket:{n_bucket}')
        attrs=self.memo[(len(public_cards))][n_bucket]
        if len(public_cards)==5 and 'bmax' in history: # river轮，key处理
            temp=[]
            history=history.replace('bmax','bmin')
            for i in history.split(','):
                if i not in temp:
                    temp.append(i)
            history=','.join(temp)
        if history in attrs:
            strategy = attrs[history]
            act=self.getAction(strategy)
            print(f'strategy:{strategy},act:{act}')
        if act=='check' or act=='call':
            act=Action.CHECK_CALL
        elif act=='fold':
            act=Action.FOLD
        elif act=='bmin':
            act=Action.RAISE_HALF_POT
        elif act=='bmax':
            act=Action.RAISE_POT
        else:
            act = Action.FOLD
        return act#np.random.choice(legal_actions)#abstracted_action

    def step(self, state: State):
        n_players=len(state.players)
        hands = state.my_hand_cards
        public_cards = state.public_cards
        legal_actions = state.legal_actions
        pot = state.pot / state.small_blind
        stage=self.pubcard2stage(public_cards)
        history_seq= state.actions
        # 获取ation
        if stage==0:
            final_action = self.decide_action(hands, public_cards, pot,n_players,legal_actions)
        else:
            final_action = self.decide_postflop_action(hands, public_cards,history_seq,legal_actions)
        return state.do_call_if_not_need_pay(final_action)

    def eval_step(self, state: State):
        return self.step(state)

    def calc_win_rate(self, hands, public_cards,n_players):
        hands=self.win_rate_cal.stander_format_trans(hands)
        public_cards=self.win_rate_cal.stander_format_trans(public_cards)
        winrate,tierate=self.win_rate_cal.calculate_equity(hands,public_cards,n_players)
        return winrate+1/2*tierate

    def get_strategy_data(self):
        return strategy_data_v2

    def decide_raise(self,legal_actions):
        legal_li=[]
        for action in legal_actions:
            if action not in [Action.CHECK_CALL,Action.ALL_IN,Action.FOLD]:
                legal_li.append(action)
        print(f'legal_li:{legal_li}')
        return random.choice(legal_li)
    def decide_action(self, hands, public_cards, pot,n_players=2,legal_actions=None) -> Action:
        win_rate = self.calc_win_rate(hands, public_cards,n_players)
        community_card_num = len(public_cards)
        current_phase = community_card_num  # 0: preflop, 3: flop, 4: turn, 5: river
        # 获取对应阶段的策略表
        sd = []
        tmp_strategy_data = self.get_strategy_data()
        for phases, strategy in tmp_strategy_data:
            if current_phase in phases:
                sd = strategy
                break
        # === 正常决策流程 ===
        action = Action.FOLD
        for i in range(len(sd) - 1):
            if sd[i][0] < pot <= sd[i+1][0]:
                for j in range(len(sd[i][1]) - 1):
                    if sd[i][1][j] <= win_rate < sd[i][1][j + 1]:
                        action = sd[i][2][j]
                        break
                break
        # == 增加 raise 多样性
        if action in [Action.RAISE_HALF_POT,Action.RAISE_3_4_POT,Action.RAISE_POT,Action.RAISE_3_2_POT,Action.RAISE_DOUBLE_POT]:
            action = self.decide_raise(legal_actions)
        # === Bluff 逻辑插入点：仅当原本要 Fold 且符合条件时尝试诈唬 ===
        if (action == Action.FOLD and self.enable_bluff and
                current_phase not in self.no_bluff_phases and
                self.bluff_min_equity <= win_rate < self.bluff_max_equity and
                random.random() < self.bluff_frequency):
            # 从可用的诈唬动作中随机选一个
            bluff_action = random.choice(self.valid_bluff_actions)
            return bluff_action
        return action

    def get_name(self):
        return f"gto_v1"

