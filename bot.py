import os
import subprocess
import time

import cv2
import numpy as np

from model import solve_dp

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

ARM_POSITION = {"x": 1750, "y": 650}


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
        highest_confidence = 0.6

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


def click_wheel(wheel_idx):
    """Calculates the center of a wheel and uses ydotool to click it."""
    wheel = WHEEL_POSITIONS[wheel_idx]

    center_x = wheel["left"] + (wheel["width"] // 2)
    center_y = wheel["top"] + (wheel["height"] // 2)

    print(f"Moving mouse to Wheel {wheel_idx + 1} at ({center_x}, {center_y})")

    subprocess.run(["ydotool", "mousemove", "-a", str(center_x), str(center_y)])
    time.sleep(0.1)
    subprocess.run(["ydotool", "click", "1"])


def pull_arm():
    """Moves the mouse to the arm and clicks it to start a new game."""
    print("Pulling the arm...")
    subprocess.run(
        ["ydotool", "mousemove", "-a", str(ARM_POSITION["x"]), str(ARM_POSITION["y"])]
    )
    time.sleep(0.1)
    subprocess.run(["ydotool", "click", "1"])


if __name__ == "__main__":
    # Configuration
    SPIN_ANIMATION_TIME = 2.5
    PAYOUT_ANIMATION_TIME = (
        3.0  # Time to wait for the score to tally before pulling arm again
    )
    MAX_REROLLS = 5

    print("Blue Prince Auto-Bot Initialized")
    print("--------------------------------")
    print("Press Ctrl+C in this terminal to stop the script.\n")

    input("Set up your game window, then press [Enter] to start the infinite loop...")

    while True:
        rerolls_left = MAX_REROLLS
        print("\n=== NEW GAME ===")
        pull_arm()

        # Wait for the initial 4 wheels to spin before taking the first screenshot
        print(f"Waiting {SPIN_ANIMATION_TIME}s for initial spin...")
        time.sleep(SPIN_ANIMATION_TIME)

        while rerolls_left > 0:
            current_state = get_slot_state()
            print(f"State: {current_state}")

            if "unknown" in current_state or "error" in current_state:
                print("Bad read. Trying again in 1 second...")
                time.sleep(1)
                continue

            expected_val, action = solve_dp(current_state, rerolls_left)
            print(f"Expected Return: {expected_val:.2f} | Rerolls left: {rerolls_left}")

            if action == "stop":
                print("Optimal Move: STOP. Taking the payout.")
                break
            else:
                print(f"Optimal Move: REROLL WHEEL {action + 1}.")
                click_wheel(action)
                rerolls_left -= 1

                print(f"Waiting {SPIN_ANIMATION_TIME}s for wheel to spin...")
                time.sleep(SPIN_ANIMATION_TIME)

        print("\nGame Finished.")
        print(f"Final state was: {current_state}")
        print(f"Waiting {PAYOUT_ANIMATION_TIME}s for payout to process...")
        time.sleep(PAYOUT_ANIMATION_TIME)
