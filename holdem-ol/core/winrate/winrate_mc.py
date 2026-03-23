from treys import Card, Deck, Evaluator
import random
class winrate_calculator:
    def __init__(self):
        super().__init__()
        self.valid_ranks = {'2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a'}
        self.valid_suits = {'h', 'd', 'c', 's'}
        self.evaluator = Evaluator()

    def stander_format_trans(self,cards):
        res=[]
        for card in cards:
            c0,c1=card[0],card[1]
            rank,suit=c1,c0.lower()
            res.append(rank+suit)
        return res

    def calculate_equity(self,hole_cards, community_cards, num_players, num_simulations=1000):

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
            hero_score = self.evaluator.evaluate(hero_cards, simulation_community)

            # 计算其他玩家的得分
            other_scores = [self.evaluator.evaluate(player_cards, simulation_community)
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