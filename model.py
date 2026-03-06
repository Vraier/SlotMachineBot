import itertools
import random

import matplotlib.pyplot as plt

ICON_NAMES = ["coin", "triple_coin", "clover", "2x", "snake", "net", "crown", "nothing"]

WHEEL_PROBABILITY = {
    "nothing": 0.27,
    "coin": 0.30,
    "snake": 0.10,
    "triple_coin": 0.10,
    "net": 0.04,
    "2x": 0.10,
    "clover": 0.01,
    "crown": 0.08,
}


def calculate_payout(state):
    counts = {icon: state.count(icon) for icon in ICON_NAMES}
    reward = 0

    if counts["crown"] == 4:
        reward += 100

    if counts["coin"] == 4:
        reward += 5
    elif counts["coin"] == 3:
        reward += 3

    if counts["triple_coin"] == 4:
        reward += 15
    elif counts["triple_coin"] == 3:
        reward += 9

    reward += counts["clover"] * 10

    if counts["snake"] > 0:
        if counts["net"] > 0:
            reward += counts["snake"] * 3
        else:
            reward = 0

    for _ in range(counts["2x"]):
        reward *= 2

    return reward


dp_memo = {}


def solve_dp(state, rerolls_left):
    if rerolls_left == 0:
        return calculate_payout(state), "stop"

    memo_key = (state, rerolls_left)
    if memo_key in dp_memo:
        return dp_memo[memo_key]

    best_value = calculate_payout(state)
    best_action = "stop"

    for wheel_idx in range(4):
        expected_value_of_reroll = -1.0  # Cost of rerolling

        for outcome_icon, probability in WHEEL_PROBABILITY.items():
            new_state = list(state)
            new_state[wheel_idx] = outcome_icon
            new_state = tuple(new_state)

            val_of_outcome, _ = solve_dp(new_state, rerolls_left - 1)
            expected_value_of_reroll += probability * val_of_outcome

        if expected_value_of_reroll > best_value:
            best_value = expected_value_of_reroll
            best_action = wheel_idx

    dp_memo[memo_key] = (best_value, best_action)
    return best_value, best_action


def exact_expected_value_of_game(k_rerolls):
    total_ev = 0.0
    icons = list(WHEEL_PROBABILITY.keys())

    for starting_state in itertools.product(icons, repeat=4):
        state_probability = 1.0
        for icon in starting_state:
            state_probability *= WHEEL_PROBABILITY[icon]

        ev, _ = solve_dp(starting_state, k_rerolls)

        total_ev += state_probability * ev

    return total_ev - 1.0  # minus cost of playing


def simulate_games(n_plays, k_rerolls):
    icons = list(WHEEL_PROBABILITY.keys())
    probs = list(WHEEL_PROBABILITY.values())

    total_net_reward = 0.0

    for _ in range(n_plays):
        state = list(random.choices(icons, weights=probs, k=4))
        rerolls_left = k_rerolls

        # Play the game optimally
        while rerolls_left > 0:
            _, action = solve_dp(tuple(state), rerolls_left)

            if action == "stop":
                break

            rerolls_left -= 1
            state[action] = random.choices(icons, weights=probs, k=1)[0]

        payout = calculate_payout(tuple(state))
        total_net_reward += payout - (k_rerolls - rerolls_left) - 1

    return total_net_reward / n_plays


if __name__ == "__main__":
    REROLLS = 5

    print(f"Calculating exact expected value for {REROLLS} rerolls...")
    exact_ev = exact_expected_value_of_game(REROLLS)
    print(f"Exact EV of a new game: {exact_ev:.4f} coins")

    N = 10000
    print(f"\nRunning simulation of {N} games...")
    sim_ev = simulate_games(N, REROLLS)
    print(f"Simulated Average Return: {sim_ev:.4f} coins")
