from core.winrate.srv_card import WinRateDocker

class WinrateWrapper:
    def __init__(self, real_time_cal_win_rate=False):
        self.real_time_cal_win_rate = real_time_cal_win_rate
        self.win_rate_docker = WinRateDocker()

    def get_winrate(self, hands, public_cards):
        """
        :param hands: like ['CA', 'C2']
        :param public_cards: [] | ['CA', 'C2', 'C3']
        :return: float
        """
        # if self.real_time_cal_win_rate:
        #     return calculate_win_rate(hands, public_cards)

        return self.win_rate_docker.win_rate_by_str(hands + public_cards)
