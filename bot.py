import os
import subprocess

import cv2
import numpy as np

ICON_NAMES = ["coin", "triple_coin", "clover", "2x", "snake", "net", "crown", "nothing"]

templates = {}
for name in ICON_NAMES:
    path = f"templates/{name}.png"
    if os.path.exists(path):
        templates[name] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        print(f"Warning: Template {path} not found!")

WHEEL_POSITIONS = [
    {"top": 602, "left": 903, "width": 172, "height": 248},
    {"top": 602, "left": 1100, "width": 172, "height": 248},
    {"top": 602, "left": 1305, "width": 172, "height": 248},
    {"top": 602, "left": 1500, "width": 172, "height": 248},
]


def capture_wayland_screen(monitor_name="DP-1"):
    try:
        result = subprocess.run(
            ["grim", "-o", monitor_name, "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        image_array = np.frombuffer(result.stdout, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except subprocess.CalledProcessError:
        return None


def get_slot_state():
    full_screen = capture_wayland_screen()
    if full_screen is None:
        return tuple(["error"] * 4)

    full_screen_gray = cv2.cvtColor(full_screen, cv2.COLOR_BGR2GRAY)
    current_state = []

    for wheel in WHEEL_POSITIONS:
        t, l = wheel["top"], wheel["left"]
        w, h = wheel["width"], wheel["height"]
        img_gray = full_screen_gray[t : t + h, l : l + w]

        best_match = "unknown"
        highest_confidence = 0.6  # only append if confidence is higher than 0.6

        for name, template in templates.items():
            if template is None:
                continue
            result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > highest_confidence:
                highest_confidence = max_val
                best_match = name

        current_state.append(best_match)

    return tuple(current_state)


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
    """Calculates the reward for a given terminal state."""
    counts = {icon: state.count(icon) for icon in ICON_NAMES}
    reward = 0

    if counts["crown"] == 4:
        reward += 100

    if counts["coin"] == 4:
        reward += 9
    elif counts["coin"] == 3:
        reward += 3

    if counts["triple_coin"] == 4:
        reward += 15
    elif counts["triple_coin"] == 3:
        reward += 9

    reward += counts["clover"] * 10

    if counts["snake"] > 0:
        reward = 0
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
        # Rerolling costs 1 coin upfront
        expected_value_of_reroll = -1.0

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


if __name__ == "__main__":
    state = ("coin", "coin", "triple_coin", "triple_coin")
    rerolls = 3
    print(f"Current State: {state}")

    expected_val, action = solve_dp(state, rerolls)

    print(f"Expected Return: {expected_val:.3f} coins")
    if action == "stop":
        print("Optimal Move: STOP PLAYING (Take the payout!)")
    else:
        print(f"Optimal Move: REROLL WHEEL {action + 1}")
