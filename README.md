# kitty-sessionizer
Custom kitten that helps you manage workspaces by offering a simple TUI project selector and session persistence (only tabs and very simple pane layouts for now).

## Installation
Ensure you have [fzf](https://github.com/junegunn/fzf) installed for the TUI.

Then clone the repo into your kitty configuration directory (assuming `~/config/kitty/` here, adjust if necessary):
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
