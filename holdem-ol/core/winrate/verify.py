import argparse
import time

import pandas as pd

from core.game.game_base import GameType
from core.winrate.short_deck import ShortDeckWinRateDocker
from core.winrate.srv_card import WinRateDocker


def verify_winrate_rpc(winrate_file, game_type):
    if game_type == GameType.HOLDEM:
        winrate_docker = WinRateDocker()
    else:
        winrate_docker = ShortDeckWinRateDocker()
    df = pd.read_csv(winrate_file)
    progress = 0
    success = True
    start_time = time.perf_counter()
    for index, row in df.iterrows():
        hand = row.iloc[0].split(",")
        public_value = row.iloc[1]
        # padas 会吧空字符串解释为float类型的nan
        if isinstance(public_value, float):
            public = []
        else:
            public = row.iloc[1].split(",")
        result = row.iloc[2]

        rate = winrate_docker.win_rate_by_str(hand + public)
        if abs(rate-result) > 0.000001:
            print(f"not match!!!, hand: {hand}, public: {public}, result: {result}, rpc_result: {rate}")
            success = False
            break
        progress += 1
        if progress % 100 == 0:
            print(f"progress: {progress}/{len(df)}, {progress / len(df) * 100:.2f}%")
    diff_time = time.perf_counter() - start_time

    print(f"[{game_type}] verify result: {success}, consume time: {diff_time:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game_type", type=str, default="holdem")
    parser.add_argument("--file_path", type=str, default="")
    args = parser.parse_args()
    if args.game_type == "holdem":
        game_type = GameType.HOLDEM
    else:
        game_type = GameType.SHORT

    verify_winrate_rpc(args.file_path, game_type)
