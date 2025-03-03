import json
from pathlib import Path
from typing import Any

from kitty.boss import Boss
from kitty.window import Window

STATE_PATH = Path.home() / ".config" / "kitty" / "state.json"


def update_state(boss: Boss, window: Window, is_window_start: bool = False) -> None:
    if not STATE_PATH.exists():
        return

    if "ask" in window.child.argv:
        return

    if "session_name" not in window.user_vars:
        if not is_window_start:
            return

        try:
            ls_output = boss.call_remote_control(
                window, ("ls", "--match", "var:session_name")
            )
            ls = json.loads(ls_output)  # type: ignore[arg-type]
            session_name = ls[0]["tabs"][0]["windows"][0]["user_vars"]["session_name"]
        except Exception:
            return

        boss.call_remote_control(
            window,
            (
                "set_user_vars",
                f"--match=id:{window.id}",
                f"session_name={session_name}",
            ),
        )

    session_name = window.user_vars["session_name"]

    ls = json.loads(
        boss.call_remote_control(window, ("ls",))  # type: ignore[arg-type]
    )  # , "--match", 'not cmdline:"ask"'))
    with open(STATE_PATH, "r") as file:
        state = json.load(file)

    for session in state:
        if session["session_name"] == session_name:
            session["tabs"] = ls[0]["tabs"]

    with open(STATE_PATH, "w") as file:
        json.dump(state, file, indent=4)


def on_resize(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # print(window.child.argv)
    # with this condition, the state update is done only on window start
    # print(data)
    if data["old_geometry"].xnum != 0 and data["old_geometry"].ynum != 0:
        return

    update_state(boss, window, is_window_start=True)


def on_cmd_startstop(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # print(data)
    update_state(boss, window)


def on_focus_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    print(data)
    # print(window.child.argv)
    update_state(boss, window)
