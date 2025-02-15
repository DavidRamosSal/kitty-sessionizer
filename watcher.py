import os
import json
from typing import Any

from kitty.boss import Boss
from kitty.window import Window


STATE_PATH = os.path.expanduser("~/.config/kitty/state.json")


def update_state(boss: Boss, window: Window) -> None:
    if not os.path.exists(STATE_PATH):
        return

    ls = json.loads(boss.call_remote_control(window, ("ls",)))
    user_vars = ls[0]["tabs"][0]["windows"][0]["user_vars"]

    if "session_name" not in user_vars:
        return

    with open(STATE_PATH, "r") as file:
        state = json.load(file)

    for idx, session in enumerate(state):
        if session["session_name"] == user_vars["session_name"]:
            state[idx]["tabs"] = ls[0]["tabs"]

    with open(STATE_PATH, "w") as file:
        json.dump(state, file, indent=4)


def on_resize(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # with this condition, the state update is done only on window start
    if data["old_geometry"].xnum != 0 and data["old_geometry"].ynum != 0:
        return

    update_state(boss, window)


def on_close(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    update_state(boss, window)


def on_cmd_startstop(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    update_state(boss, window)
