import argparse
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from kitty.boss import Boss

DB_PATH = Path.home() / ".local" / "share" / "kitty" / "state.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_name TEXT PRIMARY KEY,
                tabs TEXT
            )
        """)
        conn.commit()


def replicate_workspace(boss: Boss, tabs: List[Dict[str, Any]]) -> None:
    first_session_window = True
    first_tab_window = False
    focused_tab = None

    for tab in tabs:
        for window in tab.get("windows", []):
            window_type = "window"
            if first_session_window:
                window_type = "os-window"
                first_session_window = False
            elif first_tab_window:
                window_type = "tab"

            # cwd is overdefined in the ls output and the behaviour
            # inconsistent, in my testing this sort of works
            if window.get("foreground_processes") == []:
                cwd = window.get("cwd")
            else:
                cwd = window.get("foreground_processes")[0].get("cwd")

            # the command line status is also overdefined and the
            # behaviour inconsistent, in my testing this sort of works
            cmdline = None
            if window.get("foreground_processes") != []:
                joint_cmd_line = " ".join(
                    window.get("foreground_processes")[0].get("cmdline")
                )
                if window["last_reported_cmdline"] in joint_cmd_line:
                    cmdline = window.get("last_reported_cmdline").split()
                if "run-shell" in window.get("foreground_processes")[0].get("cmdline"):
                    cmdline = window.get("foreground_processes")[1].get("cmdline")

            envs = tuple(
                item
                for key, val in window.get("env", {}).items()
                for item in ("--env", f"{key}={val}")
            )
            vars = tuple(
                item
                for key, val in window.get("user_vars", {}).items()
                for item in ("--var", f"{key}={val}")
            )

            boss.call_remote_control(
                None,
                (
                    "launch",
                    "--type",
                    window_type,
                    "--cwd",
                    cwd,
                    *envs,
                    *vars,
                    "--hold",
                    *(cmdline or ()),
                ),
            )

            if first_tab_window:
                boss.call_remote_control(
                    None, ("goto-layout", tab.get("layout", "fat"))
                )
                first_tab_window = False

        if tab.get("is_focused"):
            focused_tab = tab["id"]

        first_tab_window = True

    if len(tabs) > 1:
        boss.call_remote_control(
            None,
            ("focus-tab", f"--match=id:{focused_tab}", "--no-response"),
        )
        # boss.call_remote_control(None, ("close-window", "--self"))


def main(args: List[str]) -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", dest="sessionizer", action="append")
    opts = parser.parse_args(args[1:])

    if not opts.sessionizer:
        return ""

    project_dir = Path(opts.sessionizer[0])
    if not project_dir.is_dir():
        return ""

    projects = [str(subdir) for subdir in project_dir.iterdir() if subdir.is_dir()]
    projects.sort()

    answer = subprocess.run(
        ["fzf"], input="\n".join(projects), text=True, capture_output=True
    )
    if answer.returncode != 0 or not answer.stdout.strip():
        return ""

    return answer.stdout.strip()


def handle_result(
    args: List[str], answer: str, target_window_id: int, boss: Boss
) -> None:
    if not answer:
        return

    project_path = Path(answer)
    w = boss.window_id_map.get(target_window_id)

    init_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tabs FROM sessions WHERE session_name = ?", (project_path.name,)
        )
        row = cursor.fetchone()

        if row:
            try:
                stored_tabs = json.loads(row[0])  # Ensure valid JSON
                replicate_workspace(boss, stored_tabs)
            except json.JSONDecodeError:
                print(
                    f"Error: Corrupt JSON in database for session {project_path.name}"
                )
                return

        else:
            new_window_id = boss.call_remote_control(
                None,
                (
                    "launch",
                    "--type",
                    "os-window",
                    "--cwd",
                    str(project_path),
                    "--var",
                    f"session_name={project_path.name}",
                ),
            )
            boss.call_remote_control(w, ("close-window", "--self"))

            ls_result = boss.call_remote_control(
                None, ("ls", f"--match=id:{new_window_id}")
            )
            try:
                kitty_ls = json.loads(ls_result)  # type: ignore[arg-type]
            except json.JSONDecodeError:
                print("Error: Invalid JSON from Kitty ls command")
                return

            cursor.execute(
                "INSERT INTO sessions (session_name, tabs) VALUES (?, ?)",
                (project_path.name, json.dumps(kitty_ls[0]["tabs"])),
            )
            conn.commit()

    boss.call_remote_control(w, ("close-window", "--self"))
