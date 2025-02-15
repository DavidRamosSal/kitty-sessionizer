import os
from pathlib import Path
import argparse
import sys
import json
import subprocess
from typing import List
from pprint import pprint
from kitty.boss import Boss
from kittens.tui.handler import kitten_ui


STATE_PATH = os.path.expanduser("~/.config/kitty/state.json")


# @kitten_ui(allow_remote_control=True)
def main(args: list[str]) -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_dir", dest="sessionizer", action="append")

    opts = parser.parse_args(args[1:])
    project_dir = str(opts.sessionizer[0])

    p = Path(project_dir)
    projects = [str(subdir) for subdir in p.iterdir() if subdir.is_dir()]
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

    if not os.path.exists(STATE_PATH):
        # here goes a plain os window in the new cwd
        boss.call_remote_control(
            None, ("launch", "--type", "os-window", "--cwd", answer)
        )
