# kitty-sessionizer
Custom kitten that helps you manage workspaces by offering a simple TUI project selector and local session resurrection of:
- tabs
- simple layouts
- commands running
- last focused tab

Session state is a stored in a sqlite database (located at `~/.local/share/kitty/state.db`), that you can freely query, back-up and restore in new systems.

## Demo
![](demo.gif?)

## Installation
Ensure you have [fzf](https://github.com/junegunn/fzf) installed for the TUI.

Then clone the repo into your kitty configuration directory (assuming `~/.config/kitty/` here, adjust if necessary):
```
git clone https://github.com/DavidRamosSal/kitty-sessionizer.git ~/.config/kitty/sessionizer
```

## Set up
Create a shortcut in your configuration file to launch the project selector TUI and set the path to the directory where your projects are (only one source is handled for now, assuming `$HOME/projects/` here, be sure to adjust to your case):
```
# ~/.config/kitty/kitty.conf

map ctrl+k kitten sessionizer/sessionizer.py --project_dir $HOME/projects
```

Finally add the global watcher to your configuration file (this is necessary to keep track of the terminal layout)

```
# ~/.config/kitty/kitty.conf

watcher sessionizer/watcher.py
```

## Limitations
- It only works locally.
- Window size is not restored.
- Complex layouts (anything more than some tabs and panes without bias) will not be reproduced accurately.
- Scroll history is not being saved (might try to implement)

