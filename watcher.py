import sqlite3
import json
from pathlib import Path
from typing import Any

from kitty.boss import Boss
from kitty.window import Window

DB_PATH = Path.home() / ".local" / "share" / "kitty" / "state.db"

IGNORE_LIST = {
    "ls",
    "cd",
    "pwd",
    "echo",
    "cat",
    "head",
    "tail",
    "touch",
    "clear",
    "less",
    "more",
    "man",
    "grep",
    "sed",
    "awk",
    "sort",
    "uniq",
    "wc",
    "rm",
    "mv",
    "cp",
    "chmod",
    "chown",
    "ln",
    "true",
    "false",
    "test",
    "which",
    "type",
    "alias",
    "bg",
    "fg",
    "jobs",
    "kill",
    "ps",
    "whoami",
    "id",
    "date",
    "uptime",
    "sleep",
    "git",
}


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent directory exists
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")  # Enable WAL for concurrency
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_name TEXT PRIMARY KEY,
                tabs TEXT
            )
        """)
        conn.commit()


init_db()


def update_state(boss: Boss, window: Window, is_window_start: bool = False) -> None:
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
            session_name = (
                ls[0]
                .get("tabs")[0]
                .get("windows")[0]
                .get("user_vars")
                .get("session_name")
            )
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

    ls_result = boss.call_remote_control(window, ("ls",))

    if not ls_result:
        return

    try:
        kitty_ls = json.loads(ls_result)  # type: ignore[arg-type]
    except json.JSONDecodeError:
        print("Error: Failed to parse Kitty ls output as JSON.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE session_name = ?", (session_name,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE sessions SET tabs = ? WHERE session_name = ?",
                (json.dumps(kitty_ls[0].get("tabs")), session_name),
            )
        else:
            cursor.execute(
                "INSERT INTO sessions (session_name, tabs) VALUES (?, ?)",
                (session_name, json.dumps(kitty_ls[0].get("tabs"))),
            )
        conn.commit()


def on_resize(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # with this condition, the state update is done only on window start
    if data["old_geometry"].xnum == 0 and data["old_geometry"].ynum == 0:
        update_state(boss, window, is_window_start=True)


def on_cmd_startstop(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # ignore cmd stop events
    if not data.get("is_start"):
        return
    # little hack to keep the execution of ephemeral commands snappy
    if data.get("cmdline") in IGNORE_LIST:
        return
    update_state(boss, window)


def on_focus_change(boss: Boss, window: Window, data: dict[str, Any]) -> None:
    # two events get executed when changing focus, ignore one
    if not data.get("focused"):
        return
    update_state(boss, window)
