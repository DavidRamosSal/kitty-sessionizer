import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from kitty.boss import Boss

STATE_PATH = Path.home() / ".config" / "kitty" / "state.json"


def replicate_workspace(boss: Boss, tabs: List[Dict[str, Any]]) -> None:
    first_session_window = True
    first_tab_window = False
    for tab in tabs:
        for window in tab["windows"]:
            window_type = "window"

            if first_session_window:
                window_type = "os-window"
                first_session_window = False
            if first_tab_window:
                window_type = "tab"

            # this would allow to re run the commands on session resurrection
            # but the executables are not being recognized so better left out for now
            # cmdline = " ".join(
            #     f"{cmd}" for cmd in window["foreground_processes"][0]["cmdline"]
            # )
            envs = tuple(
                item
                for key, val in window["env"].items()
                for item in ("--env", f"{key}={val}")
            )
            vars = tuple(
                item
                for key, val in window["user_vars"].items()
                for item in ("--var", f"{key}={val}")
            )

            boss.call_remote_control(
                None,
                (
                    "launch",
                    "--type",
                    window_type,
                    "--cwd",
                    window["foreground_processes"][0]["cwd"],
                    *envs,
                    *vars,
                    "--hold",
                    # cmdline,
                ),
            )

            if first_tab_window:
                boss.call_remote_control(None, ("goto-layout", tab["layout"]))
                first_tab_window = False

        first_tab_window = True


def main(args: list[str]) -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", dest="sessionizer", action="append")

    opts = parser.parse_args(args[1:])
    project_dir = Path(opts.sessionizer[0])

    projects = [str(subdir) for subdir in project_dir.iterdir() if subdir.is_dir()]
    projects.sort()

    answer = subprocess.run(
        ["fzf"], input="\n".join(projects), text=True, capture_output=True
    )

    if answer.returncode != 0 or not answer.stdout.strip():
        return ""

    return answer.stdout.strip()


def handle_result(
    args: list[str], answer: str, target_window_id: int, boss: Boss
) -> None:
    if answer == "":
        return

    project_path = Path(answer)
    w = boss.window_id_map.get(target_window_id)

    if not STATE_PATH.exists():
        boss.call_remote_control(
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

        ls = json.loads(boss.call_remote_control(None, ("ls",)))

        state = [{"session_name": project_path.name, "tabs": ls[0]["tabs"]}]

        with open(STATE_PATH, "w") as file:
            json.dump(state, file, indent=4)
            return

    with open(STATE_PATH, "r") as file:
        state = json.load(file)

    sessions = [session["session_name"] for session in state]

    if project_path.name not in sessions:
        boss.call_remote_control(
            None,
            (
                "launch",
                "--type",
                "os-window",
                "--cwd",
                str(project_path),
                "--var",
                str(project_path.name),
            ),
        )
        boss.call_remote_control(w, ("close-window", "--self"))

        ls = json.loads(boss.call_remote_control(None, ("ls",)))

        state.append({"session_name": project_path.name, "tabs": ls[0]["tabs"]})

        with open(STATE_PATH, "w"):
            json.dump(state, file)
            return

    for idx, session in enumerate(sessions):
        if project_path.name == session:
            replicate_workspace(boss, state[idx]["tabs"])
            boss.call_remote_control(w, ("close-window", "--self"))
