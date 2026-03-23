from core.winrate.srv_card import WinRateCli, SrvCardV2
from core.winrate.winrate_bench import TestWinRate
from testing.agent.winrate.winrate_base_agent import calculate_win_rate


def test_calculate_win_rate_cmp():
    WinRateCli.initialize()
    WinRateCli.set_srv_card_mod(SrvCardV2)

    def fn1(_cs: list[str]) -> float:
        return calculate_win_rate(_cs[:2], _cs[2:], 10000)

    for i in range(100000):
        cs = TestWinRate.random_gen_cards_str()
        TestWinRate.compare_win_rate(fn1, WinRateCli.win_rate, cs)
        # print only in one line
        print(f"\r{i}", end='')


if __name__ == "__main__":
    test_calculate_win_rate_cmp()
