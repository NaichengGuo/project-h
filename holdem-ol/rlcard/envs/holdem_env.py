import json

from core.coder.state import State, ActionInfo
from core.game.action import Action
from rlcard.envs.action_history import HistoryActionRecord
from rlcard.games.nolimitholdem.game import NolimitholdemGame
from rlcard.utils import seeding


class HoldemEnv(object):

    def __init__(self, config=None):
        if config is None:
            config = {}
        self.action_static = None
        self.run_count = 0
        seed = config.get('seed', None)
        config['seed'] = seed
        self.np_random, _ = seeding.np_random(seed)

        self.game = NolimitholdemGame(config)
        self.agents = None
        self.agent_index = None
        self.num_players = self.game.get_num_players()
        self.num_actions = self.game.num_actions
        self.action_history = HistoryActionRecord(self.num_players)
        self.action_history_snap = [[] for _ in range(self.num_players)]
        self.clear_static()

    def set_agents(self, agents):
        self.agents = agents
        if len(agents) != self.num_players:
            raise ValueError('The number of agents should be the same as the number of players')
        self.agent_index = [i for i in range(self.num_players)]
        self.clear_history_action()

    def reset(self) -> (State, int):

        self.np_random.shuffle(self.agent_index)
        self.action_history_snap = self.action_history.get_history_snap(self._org_to_cur)
        state, player_id = self.game.reset_game()
        state.action_history = self.action_history_snap

        return state, player_id

    def run(self, is_training=False) -> ([], list[int]):
        trajectories = [[] for _ in range(self.num_players)]
        state, player_id = self.reset()
        self.run_count += 1

        # 通知agent本轮游戏开始
        for a in self.agents:
            if hasattr(a, "on_game_start"):
                a.on_game_start()

        # Loop to play the game
        trajectories[player_id].append(state)
        while not self.is_over():
            # Agent plays
            agent = self._get_agent(player_id)
            if not is_training:
                action = agent.eval_step(state)
            else:
                action = agent.step(state)

            if isinstance(action, int):
                action = Action(action)

            # Environment steps
            next_state, next_player_id = self.step(action)

            # Save action
            trajectories[player_id].append(action)

            # Set the state and player
            state = next_state
            player_id = next_player_id

            # Save state.
            if not self.game.is_over():
                trajectories[player_id].append(state)

        # Add a final state to all the players
        for player_id in range(self.num_players):
            state = self.get_state(player_id)
            trajectories[player_id].append(state)

        # Payoffs
        payoffs = self.game.get_payoffs()

        ah = self.game.get_action_history()
        self._static_action(ah)
        self.action_history.add_history(ah, payoffs, self._cur_to_org, state.small_blind)

        org_view_payoffs = self._to_org_gent_view(payoffs)
        org_view_trajectories = self._to_org_gent_view(trajectories)

        return org_view_trajectories, org_view_payoffs

    def step(self, action) -> (State, int):
        state, player_id = self.game.step(action)
        state.action_history = self.action_history_snap
        return state, player_id

    def get_state(self, player_id):
        state = self.game.get_state(player_id)
        state.action_history = self.action_history_snap
        return state

    def is_over(self):
        return self.game.is_over()

    def clear_history_action(self):
        self.action_history_snap = [[] for _ in range(self.num_players)]
        self.action_history.clear()

    def _org_to_cur(self, index):
        for i in range(len(self.agent_index)):
            if self.agent_index[i] == index:
                return i
        raise ValueError('[_org_to_cur]index not found')

    def _cur_to_org(self, index):
        return self.agent_index[index]

    def _get_agent(self, player_id):
        return self.agents[self._cur_to_org(player_id)]

    def _to_org_gent_view(self, data):
        if len(data) != len(self.agent_index):
            raise ValueError('The number of data should be the same as the number of players')
        result = [None] * len(data)
        for i in range(len(data)):
            result[self._cur_to_org(i)] = data[i]
        return result

    def clear_static(self):
        self.run_count = 0
        self.action_static = [[0 for _ in range(self.num_actions)] for _ in range(self.num_players)]
        self.stage_action_static = [[[0 for _ in range(self.num_actions)] for _ in range(4)]for _ in range(self.num_players)]

    def _static_action(self, action_history: list[ActionInfo]):
        for i, action in enumerate(action_history):
            # print(action.to_dict())
            a = action.rl_raw_action
            if a < 0:
                continue
            player_id = action.player_id
            self.action_static[self._cur_to_org(player_id)][a] += 1
            self.stage_action_static[self._cur_to_org(player_id)][action.stage][a] += 1

    def get_action_static(self):
        return self.action_static

    def get_stage_action_static(self):
        return self.stage_action_static

    def debug_print_static(self):
        for i in range(self.num_players):
            print(f"player {i} action_static: (hands: {self.run_count})")
            print("----------------")
            print(f"{''.ljust(30)}   ratio   per-hand")
            actions = self.action_static[i]
            value_sum = sum(actions)
            # 避免除0
            if value_sum == 0:
                value_sum = 1
            run_count = self.run_count
            if run_count == 0:
                run_count = 1
            for j in range(len(actions)):
                print(f"{str(Action(j)).ljust(30)}: {actions[j] / value_sum : .3f}  {actions[j] / run_count : .3f}")

            # print("per hand static:")
            # if self.run_count != 0:
            #     for j in range(len(actions)):
            #         print(f"{str(Action(j)).ljust(30)}: {actions[j] / self.run_count : .3f}")

