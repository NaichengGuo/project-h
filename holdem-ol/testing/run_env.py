import rlcard
import time

from rlcard.envs.holdem_env import HoldemEnv


def run(env, times: int):
    total_payoffs = [0 for _ in range(env.num_players)]
    win_counts = [0 for _ in range(env.num_players)]
    real_times = 0
    start_time = time.perf_counter()
    for r in range(times):
        trajectories, payoffs = env.run(is_training=False)
        real_times += 1
        for i in range(len(payoffs)):
            total_payoffs[i] += payoffs[i]
            if payoffs[i] > 0:
                win_counts[i] += 1

    time_diff = time.perf_counter() - start_time

    result = {
        "winrate": win_counts[0] / real_times * 100.0,
        "total_payoffs": total_payoffs[0] / 2.0,
        "mbb/h": total_payoffs[0] / 2.0 / real_times * 1000,
        "run_time": time_diff
    }

    return result


def run_with_msg(env, times: int, msg: str = ''):
    result = run(env, times)
    print(
        f"{msg}, winrate: {result['winrate'] :.1f}%), total payoffs: {result['total_payoffs']: .1f} bb , mbb/h: {result['mbb/h']: .1f}, run time: {result['run_time']:.1f} s\n")


def evaluate(msg, agents, round_count):
    env = HoldemEnv()
    env.set_agents(agents)
    run_with_msg(env, round_count, msg)
    env.debug_print_static()
