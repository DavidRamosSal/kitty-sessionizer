import argparse
import sys
import json
import subprocess
from typing import List
from pprint import pprint
from kitty.boss import Boss
from kittens.tui.handler import kitten_ui
from textual.app import App, ComposeResult
from textual.widgets import Input, Label, ListItem, ListView
from textual.containers import Vertical
from rapidfuzz import process, fuzz

parser = argparse.ArgumentParser()
parser.add_argument("--project_dir", dest="sessionizer", action="append")


# class SimpleTUI(
#     App[None]
# ):  # No additional state, so we use `None` as the type argument
#     text: str
#
#     def __init__(self, text: str) -> None:
#         super().__init__()
#         self.text = text  # Store the string to display
#
#     def compose(self) -> ComposeResult:
#         yield Vertical(Label(self.text))


class sessionizer(App[None]):
    project_dir: str

    def __init__(self, project_dir: str):
        super().__init__()
        self.project_dir = project_dir
        self.dirs: List[str] = []

    def list_directories(self) -> list[str]:
        """Uses `fd` to find directories inside the specified directory."""
        try:
            result = subprocess.run(
                ["fd", "--type", "d", "--max-depth", "1", ".", self.project_dir],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.splitlines()
        except FileNotFoundError:
            return ["Error: 'fd' is not installed."]
        except subprocess.CalledProcessError:
            return ["Error: Failed to list directories."]

    def compose(self) -> ComposeResult:
        self.dirs = self.list_directories()
        self.search_input = Input(placeholder="Type to fuzzy-search directories...")
        self.list_view = ListView(*(ListItem(Label(d)) for d in self.dirs))
        yield Vertical(
            Label(f"Directories in {self.project_dir}:"),
            self.search_input,
            self.list_view,
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Perform fuzzy matching using RapidFuzz whenever the user types.
        We match the query against all_dirs, then display the top results.
        """
        query = event.value.strip()

        if not query:
            filtered = self.dirs
        else:
            matches = process.extract(
                query,
                self.dirs,
                scorer=fuzz.ratio,
                limit=50,  # Max number of matches to return
                score_cutoff=10,  # Minimum score to include
            )
            filtered = [m[0] for m in matches]

        self.list_view.clear()
        for d in filtered:
            self.list_view.append(ListItem(Label(d)))

    def on_list_view_action(self, event: ListView.Selected) -> None:
        """
        Called when the user presses Enter (or Space) on a selected list item.
        Prints the directory and exits the app.
        """
        self.selected_directory = event.item
        print(f"Selected directory: {self.selected_directory}")
        self.exit()


@kitten_ui(allow_remote_control=True)
def main(args: list[str]) -> str:
    opts = parser.parse_args(args[1:])
    project_dir = str(opts.sessionizer[0])
    # this is the main entry point of the kitten, it will be executed in
    # the overlay window when the kitten is launched
    # answer = input("Enter some text: ")
    answer = "itworked"
    cp = main.remote_control(["ls"], capture_output=True)
    if cp.returncode != 0:
        sys.stderr.buffer.write(cp.stderr)
        raise SystemExit(cp.returncode)
    # output = json.loads(cp.stdout)
    # pprint(output)
    # whatever this function returns will be available in the
    # handle_result() function
    # print(sys.path)
    # SimpleTUI(str(cp.stdout)).run()
    sessionizer(project_dir).run()
    return answer


def handle_result(
    args: list[str], answer: str, target_window_id: int, boss: Boss
) -> None:
    # get the kitty window into which to paste answer
    print(args)
    print(sys.path)
    # print(answer)
    w = boss.window_id_map.get(target_window_id)
    # print(w)
    if w is not None:
        w.paste_text("worked")
