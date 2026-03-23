from core.game.game_base import GameType
from core.game.compare import compare_hands

if __name__ == "__main__":
    hand1 = ['H9', 'S9']
    hand2 = ['DQ', 'S6']
    public = ['CT', 'HT', 'ST', 'SJ', 'DJ']
    winnners = compare_hands([hand1 + public, None, hand2 + public], GameType.SHORT)
    print(winnners)