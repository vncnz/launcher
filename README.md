# Launcher
This is my quick and dirty fzf based keyboard application launcher, dashboard, and window switcher. It was designed to work with the niri wayland compositor.

## Requirements:
 - niri, window switching and keyboard language display depend on the niri compositor and use `niri msg`
 - alacritty, alacritty is used as the terminal emulator and is started by `start.py` with the launcher running (you _could_ use another terminal emulator, but you will need to change `start.py`)
 - pactl, for displaying the volume
 - python-psutil, for showing battery information in the header bar
 - fzf, for the whole program to even work

## How to use:
 -  Add the following rule to your niri config file:
	```
	window-rule {
		match title="alacritty launcher"
		open-focused true
		open-floating true
	}
	```
 - Add a binding somewhere in your niri config to start the `python start.py`
 - Customize the entries in your dashboard using ~/.config/launcher.json it should look this way:
 ```
 [
 	{
 		"name": "name of the entry",
      		"exec": "command to execute"
    	}
 ]
 ```
 - The launcher starts in normal mode. You can switch to dashboard mode by selecting the entry `:d`, using `:w` will switch you to window mode
 - In any mode you can exit the launcher `:q` or return to normal mode with `:n`.
 - Pressing Esc selecting a entry in normal or window mode or defocusing the window will close it

## How it works
 - In normal mode .desktop files will be parsed from all of the usual locations, their name will be displayed, when selected the binary defined in their Exec field will be executed
 - In window mode the launcher will get all open windows using `niri msg windows` and will switch to the selected one with `niri msg action focus-window --id <id>`
 - In dashboard mode your entries will be parsed and the `exec` field of the selected one will be executed. You should either use a TUI or a shell in your exec field.
