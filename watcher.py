import json
from pathlib import Path
from typing import Any

from kitty.boss import Boss
from kitty.window import Window

STATE_PATH = Path.home() / ".config" / "kitty" / "state.json"


def update_state(boss: Boss, window: Window, is_window_start: bool = False) -> None:
    if not STATE_PATH.exists():
        return

    ls = json.loads(boss.call_remote_control(window, ("ls",)))

    all_user_vars = [tab["windows"][0]["user_vars"] for tab in ls[0]["tabs"]]
    session_name = next(
        (
            user_vars["session_name"]
            for user_vars in all_user_vars
            if "session_name" in user_vars
        ),
        None,
    )

    if session_name is None:
        return

    # hacky way to set the session_name user variable on new windows that are opened interactively
    if is_window_start:
        boss.call_remote_control(
            window,
            (
                "set_user_vars",
                f"--match=id:{window.id}",
                f"session_name={session_name}",
            ),
        )
        ls = json.loads(boss.call_remote_control(window, ("ls",)))

        for tab in ls[0]["tabs"]:
            for wndow in tab["windows"]:
                if "kitten ask" in " ".join(wndow["cmdline"]):
                    return

    with open(STATE_PATH, "r") as file:
        state = json.load(file)

    for idx, session in enumerate(state):
        if session["session_name"] == session_name:
            state[idx]["tabs"] = ls[0]["tabs"]

    with open(STATE_PATH, "w") as file:
        json.dump(state, file, indent=4)


def on_resize(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # with this condition, the state update is done only on window start
    if data["old_geometry"].xnum != 0 and data["old_geometry"].ynum != 0:
        return

    update_state(boss, window, is_window_start=True)


def on_cmd_startstop(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    update_state(boss, window)
