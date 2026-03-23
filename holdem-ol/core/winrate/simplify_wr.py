from treys import Evaluator, Card, Deck
import pandas as pd
class ValueEstimator:
    def __init__(self):
        self.evaluator = Evaluator()

        # Define the order of ranks and suits as given
        self.RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
        self.SUITS = ['s', 'h', 'd', 'c']  # Spades, Hearts, Diamonds, Clubs

        # Precompute a list of all cards in the given order
        self.all_cards = []
        for suit in self.SUITS:
            for rank in self.RANKS:
                self.all_cards.append(rank + suit)

                # Load the preflop lookup table
        # The CSV should have columns: "Hole Cards", "Win Prob", "Tie Prob"
        # self.preflop_data = pd.read_csv('preflop_probs.csv')
        val = [['AAo ', 0.8493, 0.0054],
               ['KKo ', 0.8211, 0.0055],
               ['QQo ', 0.7963, 0.0058],
               ['JJo ', 0.7715, 0.0063],
               ['TTo ', 0.7466, 0.007],
               ['99o ', 0.7166, 0.0078],
               ['88o ', 0.6871, 0.0089],
               ['AKs ', 0.6621, 0.0165],
               ['77o ', 0.6572, 0.0102],
               ['AQs ', 0.6531, 0.0179],
               ['AJs ', 0.6439, 0.0199],
               ['AKo ', 0.6446, 0.017],
               ['ATs ', 0.6348, 0.0222],
               ['AQo ', 0.635, 0.0184],
               ['AJo ', 0.6253, 0.0205],
               ['KQs ', 0.624, 0.0198],
               ['66o ', 0.627, 0.0116],
               ['A9s ', 0.615, 0.0254],
               ['ATo ', 0.6156, 0.023],
               ['KJs ', 0.6147, 0.0218],
               ['A8s ', 0.605, 0.0287],
               ['KTs ', 0.6058, 0.024],
               ['KQo ', 0.6043, 0.0204],
               ['A7s ', 0.5938, 0.0319],
               ['A9o ', 0.5944, 0.0264],
               ['KJo ', 0.5944, 0.0225],
               ['55o ', 0.5964, 0.0136],
               ['QJs ', 0.5907, 0.0237],
               ['K9s ', 0.5863, 0.027],
               ['A5s ', 0.5806, 0.0371],
               ['A6s ', 0.5817, 0.0345],
               ['A8o ', 0.5837, 0.0299],
               ['KTo ', 0.5849, 0.0248],
               ['QTs ', 0.5817, 0.0259],
               ['A4s ', 0.5713, 0.0379],
               ['A7o ', 0.5716, 0.0334],
               ['K8s ', 0.5679, 0.0304],
               ['A3s ', 0.5633, 0.0377],
               ['QJo ', 0.569, 0.0245],
               ['K9o ', 0.564, 0.028],
               ['A5o ', 0.5574, 0.039],
               ['A6o ', 0.5587, 0.0362],
               ['Q9s ', 0.5622, 0.0288],
               ['K7s ', 0.5584, 0.0338],
               ['JTs ', 0.5615, 0.0274],
               ['A2s ', 0.555, 0.0374],
               ['QTo ', 0.5594, 0.0268],
               ['44o ', 0.5625, 0.0153],
               ['A4o ', 0.5473, 0.0399],
               ['K6s ', 0.548, 0.0367],
               ['K8o ', 0.5443, 0.0317],
               ['Q8s ', 0.5441, 0.032],
               ['A3o ', 0.5385, 0.0397],
               ['K5s ', 0.5383, 0.0391],
               ['J9s ', 0.5411, 0.031],
               ['Q9o ', 0.5386, 0.0299],
               ['JTo ', 0.5382, 0.0284],
               ['K7o ', 0.5341, 0.0354],
               ['A2o ', 0.5294, 0.0396],
               ['K4s ', 0.5288, 0.0399],
               ['Q7s ', 0.5252, 0.0355],
               ['K6o ', 0.5229, 0.0385],
               ['K3s ', 0.5207, 0.0396],
               ['T9s ', 0.5237, 0.033],
               ['J8s ', 0.5231, 0.034],
               ['33o ', 0.5283, 0.017],
               ['Q6s ', 0.5167, 0.0386],
               ['Q8o ', 0.5193, 0.0333],
               ['K5o ', 0.5125, 0.0412],
               ['J9o ', 0.5163, 0.0322],
               ['K2s ', 0.5123, 0.0394],
               ['Q5s ', 0.5071, 0.0411],
               ['T8s ', 0.505, 0.0365],
               ['K4o ', 0.5022, 0.042],
               ['J7s ', 0.5045, 0.0374],
               ['Q4s ', 0.4976, 0.0418],
               ['Q7o ', 0.499, 0.0372],
               ['T9o ', 0.4981, 0.0343],
               ['J8o ', 0.4971, 0.0355],
               ['K3o ', 0.4933, 0.0418],
               ['Q6o ', 0.4899, 0.0405],
               ['Q3s ', 0.4893, 0.0416],
               ['98s ', 0.4885, 0.0388],
               ['T7s ', 0.4865, 0.0397],
               ['J6s ', 0.4857, 0.0406],
               ['K2o ', 0.4842, 0.0417],
               ['22o ', 0.4938, 0.0189],
               ['Q2s ', 0.481, 0.0413],
               ['Q5o ', 0.4795, 0.0432],
               ['J5s ', 0.4782, 0.0433],
               ['T8o ', 0.4781, 0.038],
               ['J7o ', 0.4772, 0.0391],
               ['Q4o ', 0.4692, 0.044],
               ['97s ', 0.4699, 0.0425],
               ['J4s ', 0.4686, 0.044],
               ['T6s ', 0.468, 0.0428],
               ['J3s ', 0.4604, 0.0437],
               ['Q3o ', 0.4602, 0.0438],
               ['98o ', 0.4606, 0.0405],
               ['87s ', 0.4568, 0.045],
               ['T7o ', 0.4582, 0.0415],
               ['J6o ', 0.4571, 0.0426],
               ['96s ', 0.4515, 0.0455],
               ['J2s ', 0.452, 0.0435],
               ['Q2o ', 0.451, 0.0437],
               ['T5s ', 0.4493, 0.0455],
               ['J5o ', 0.449, 0.0455],
               ['T4s ', 0.442, 0.0465],
               ['97o ', 0.4407, 0.0445],
               ['86s ', 0.4381, 0.0484],
               ['J4o ', 0.4386, 0.0463],
               ['T6o ', 0.4384, 0.0448],
               ['95s ', 0.4331, 0.0481],
               ['T3s ', 0.4337, 0.0462],
               ['76s ', 0.4282, 0.0508],
               ['J3o ', 0.4296, 0.0461],
               ['87o ', 0.4269, 0.0471],
               ['T2s ', 0.4254, 0.0459],
               ['85s ', 0.4199, 0.051],
               ['96o ', 0.421, 0.0477],
               ['J2o ', 0.4204, 0.0459],
               ['T5o ', 0.4185, 0.0478],
               ['94s ', 0.414, 0.049],
               ['75s ', 0.4097, 0.0539],
               ['T4o ', 0.4105, 0.0489],
               ['93s ', 0.408, 0.0491],
               ['86o ', 0.4069, 0.0508],
               ['65s ', 0.4034, 0.0557],
               ['84s ', 0.401, 0.0519],
               ['95o ', 0.4013, 0.0506],
               ['T3o ', 0.4015, 0.0487],
               ['92s ', 0.3997, 0.0488],
               ['76o ', 0.3965, 0.0533],
               ['74s ', 0.391, 0.0548],
               ['T2o ', 0.3923, 0.0485],
               ['54s ', 0.3853, 0.0584],
               ['85o ', 0.3874, 0.0537],
               ['64s ', 0.3848, 0.057],
               ['83s ', 0.3828, 0.0518],
               ['94o ', 0.3808, 0.0517],
               ['75o ', 0.3767, 0.0567],
               ['82s ', 0.3767, 0.0518],
               ['73s ', 0.373, 0.0546],
               ['93o ', 0.3742, 0.0518],
               ['65o ', 0.3701, 0.0586],
               ['53s ', 0.3675, 0.0586],
               ['63s ', 0.3668, 0.0569],
               ['84o ', 0.367, 0.0547],
               ['92o ', 0.3651, 0.0516],
               ['43s ', 0.3572, 0.0582],
               ['74o ', 0.3566, 0.0577],
               ['72s ', 0.3543, 0.0543],
               ['54o ', 0.3507, 0.0616],
               ['64o ', 0.35, 0.0601],
               ['52s ', 0.3492, 0.0583],
               ['62s ', 0.3483, 0.0566],
               ['83o ', 0.3474, 0.0546],
               ['42s ', 0.3391, 0.0582],
               ['82o ', 0.3408, 0.0548],
               ['73o ', 0.3371, 0.0576],
               ['53o ', 0.3316, 0.0619],
               ['63o ', 0.3306, 0.0601],
               ['32s ', 0.3309, 0.0578],
               ['43o ', 0.3206, 0.0615],
               ['72o ', 0.3171, 0.0574],
               ['52o ', 0.3119, 0.0618],
               ['62o ', 0.3107, 0.0599],
               ['42o ', 0.3011, 0.0616],
               ['32o ', 0.2923, 0.0612]]
        self.preflop_data = pd.DataFrame(columns=['Hole Cards', 'Win Prob', 'Tie Prob'], data=val)

        # Create a dictionary for quick lookup: { 'AAo': win_prob, 'KKo': win_prob, ... }
        self.preflop_lookup = {row['Hole Cards'].strip(): float(row['Win Prob']) for _, row in
                               self.preflop_data.iterrows()}

        # Map ranks to a numerical value for sorting by strength (A high)
        self.rank_strength = {
            'A': 14, 'K': 13, 'Q': 12, 'J': 11,
            'T': 10, '9': 9, '8': 8, '7': 7,
            '6': 6, '5': 5, '4': 4, '3': 3, '2': 2
        }

    def calculate_heuristic_win_prob(self, card_vector):
        """
        Calculate the heuristic win probability using a one-hot encoded 52-length vector.

        card_vector: List or array of length 52 with 0/1 indicating which cards are present.
                     The first two '1's found will be considered as hole cards,
                     and the remaining '1's (if any) are considered as board cards.
        """
        card_vector = [i[1]+i[0].lower() for i in card_vector]

        # Convert indices to card strings
        hole_cards_str = card_vector[:2]
        board_cards_str = card_vector[2:]

        # Check if preflop (no board cards)
        if len(board_cards_str) == 0:
            # Preflop scenario: Use the lookup table
            # Construct a key like 'AAo' or 'AKs' from hole_cards_str
            preflop_key = self._construct_preflop_key(hole_cards_str)

            if preflop_key in self.preflop_lookup:
                return self.preflop_lookup[preflop_key]
            else:
                # If not found in lookup, return a default value
                return 0.5
        else:
            # Postflop scenario: Use the heuristic (Treys evaluator)
            hole_cards = [Card.new(c) for c in hole_cards_str]
            board = [Card.new(c) for c in board_cards_str]
            score = self.evaluator.evaluate(board, hole_cards)
            percentile = self.evaluator.get_five_card_rank_percentage(score)
            win_prob = 1.0 - percentile
            return win_prob

    def _construct_preflop_key(self, hole_cards_str):
        """
        Construct a preflop hand key (e.g., 'AAo', 'AKs') from two hole cards strings (e.g. ['As', 'Kd']) to index the csv.

        Steps:
        1. Extract ranks and suits from the two hole cards.
        2. Determine the higher-ranked card and put it first.
        3. Determine if suited ('s') or offsuit ('o').
        """

        # Extract ranks and suits
        ranks = [c[0] for c in hole_cards_str]
        suits = [c[1] for c in hole_cards_str]

        # Sort by rank strength so highest rank comes first
        # We have two cards, so we just find the order
        if self.rank_strength[ranks[0]] > self.rank_strength[ranks[1]]:
            high_rank, low_rank = ranks[0], ranks[1]
            suit1, suit2 = suits[0], suits[1]
        else:
            high_rank, low_rank = ranks[1], ranks[0]
            suit1, suit2 = suits[1], suits[0]

        # Determine suited or offsuit
        if suit1 == suit2:
            suited_char = 's'
        else:
            suited_char = 'o'

        # Construct hand key
        hand_key = f"{high_rank}{low_rank}{suited_char}"
        return hand_key

    # def calculate_mc_win_prob(self, card_vector, num_samples=1000):
    #     """
    #     Monte Carlo approximation of heads-up win probability with full game simulation
    #     using a one-hot encoded 52-length vector for the hero's hole cards and board.
    #
    #     card_vector: A list/array of length 52 with 0/1 indicating which cards are present.
    #                 The first two '1's found will be considered hole cards,
    #                 and the rest are considered board cards.
    #     """
    #     # Decode card_vector into hole_cards_str and board_cards_str
    #     selected_indices = [i for i, val in enumerate(card_vector) if val == 1]
    #
    #     if len(selected_indices) < 2:
    #         raise ValueError("At least 2 cards are needed (2 hole cards).")
    #
    #     hole_indices = selected_indices[:2]
    #     board_indices = selected_indices[2:]
    #
    #     hole_cards_str = [self.all_cards[i] for i in hole_indices]
    #     board_cards_str = [self.all_cards[i] for i in board_indices]
    #
    #     evaluator = Evaluator()
    #
    #     # Convert hero's hole cards and board cards to Treys Card ints
    #     hero_hole = [Card.new(c) for c in hole_cards_str]
    #     board = [Card.new(c) for c in board_cards_str]
    #
    #     known_cards = hero_hole + board
    #
    #     wins, ties = 0, 0
    #
    #     for _ in range(num_samples):
    #         # Initialize a new deck and remove known cards
    #         deck = Deck()
    #         for kc in known_cards:
    #             deck.cards.remove(kc)
    #
    #         # Opponent hand
    #         opp_hand = deck.draw(2)
    #
    #         # Complete the board if needed
    #         remaining_board = deck.draw(5 - len(board))
    #         full_board = board + remaining_board
    #
    #         # Evaluate final hands
    #         hero_score = evaluator.evaluate(full_board, hero_hole)
    #         opp_score = evaluator.evaluate(full_board, opp_hand)
    #
    #         if hero_score < opp_score:
    #             wins += 1
    #         elif hero_score == opp_score:
    #             ties += 1
    #
    #     # Compute win probability
    #     win_prob = wins / num_samples
    #     return win_prob