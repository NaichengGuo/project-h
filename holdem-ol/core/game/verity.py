import argparse
import time

import pandas as pd

from core.game.game_base import GameType
from core.game.compare import compare_hands

specail_cases = [
    [
        # 顺子和3条
        ['HA', 'CJ'],
        ['CQ', 'HQ'],
        ['C6', 'H7', 'D8', 'S9', 'DQ'],
        1
    ],
    [
        ['CQ', 'HQ'],
        ['HA', 'CJ'],
        ['C6', 'H7', 'D8', 'S9', 'DQ'],
        -1
    ],
    [
        # 顺子和4条
        ['HA', 'CJ'],
        ['D9', 'C9'],
        ['C6', 'H7', 'D8', 'S9', 'H9'],
        -1
    ],
    [
        # 顺子和4条
        ['D9', 'C9'],
        ['HA', 'CJ'],
        ['C6', 'H7', 'D8', 'S9', 'H9'],
        1
    ],
    [
        # 包含A的同花顺和4条
        ['HA', 'CJ'],
        ['D9', 'C9'],
        ['H6', 'H7', 'H8', 'H9', 'S9'],
        1
    ],
    [
        # 包含A的同花顺和4条
        ['D9', 'C9'],
        ['HA', 'CJ'],
        ['H6', 'H7', 'H8', 'H9', 'S9'],
        -1
    ],
    [
        # 包含A的同花顺和更大的同花顺
        ['HJ', 'HQ'],
        ['HA', 'DT'],
        ['H6', 'H7', 'H8', 'H9', 'HT'],
        1
    ],
    [
        # 相等的牌
        ['SA', 'HQ'],
        ['HA', 'CJ'],
        ['H6', 'S7', 'D8', 'H9', 'S9'],
        0
    ],
    [
        # flush > fullhouse
        ['HJ', 'HQ'],
        ['C6', 'D7'],
        ['H6', 'H7', 'H8', 'S6', 'DJ'],
        1
    ],
    [
        # fullhouse < flush
        ['C6', 'D7'],
        ['HJ', 'HQ'],
        ['H6', 'H7', 'H8', 'S6', 'DJ'],
        -1
    ]
]

def short_deck_special_case_test(game_type: GameType):
    for case in specail_cases:
        winners = compare_hands([case[0] + case[2], case[1] + case[2]], game_type)
        if winners[0] == 1:
            if winners[1] == 0:
                compare_result = 1
            else:
                compare_result = 0
        else:
            compare_result = -1

        if compare_result != case[3]:
            print(
                f"[special_cases_test] not match!!!, hand1: {case[0]}, hand2: {case[1]}, public: {case[2]}, result: {case[3]}, compare_result: {compare_result}")
            return
    print(f"[{game_type}] ({len(specail_cases)}) special case test success")

def verify_holdem(data_file_path: str, game_type: GameType):
    # 读取CSV文件
    df = pd.read_csv(data_file_path)

    progress = 0
    success = True
    dup_check = set()
    dup_count = 0
    start_time = time.perf_counter()
    for index, row in df.iterrows():
        hand1 = row.iloc[0].split(",")
        hand2 = row.iloc[1].split(",")
        public = row.iloc[2].split(",")
        result = row.iloc[3]

        key = row.iloc[0] + row.iloc[1] + row.iloc[2]
        if key in dup_check:
            dup_count += 1
        dup_check.add(key)
        winners = compare_hands([hand1 + public, hand2 + public], game_type)
        if winners[0] == 1:
            if winners[1] == 0:
                compare_result = 1
            else:
                compare_result = 0
        else:
            compare_result = -1

        if compare_result != result:
            print(
                f"not match!!!, hand1: {hand1}, hand2: {hand2}, public: {public}, result: {result}, compare_result: {compare_result}")
            success = False
            break

        progress += 1
        if progress % 10000 == 0:
            print(f"progress: {progress}/{len(df)}, {progress / len(df) * 100:.2f}%")
    diff_time = time.perf_counter() - start_time

    print("dup count: ", dup_count)
    if success:
        result_str = "success"
    else:
        result_str = "failed"
    print(f"[{game_type}] verify result: {result_str}, consume time: {diff_time:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--game_type", type=str, default="holdem")
    parser.add_argument("--file_path", type=str, default="")
    args = parser.parse_args()
    if args.game_type == "holdem":
        game_type = GameType.HOLDEM
    else:
        game_type = GameType.SHORT

    if game_type == GameType.SHORT:
        short_deck_special_case_test(game_type)
    verify_holdem(args.file_path, game_type)
