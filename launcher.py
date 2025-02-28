import os
import subprocess
import json
import threading
import time
from pathlib import Path
import system

# Globals to track mode and system info
current_mode = "normal"
username = os.getlogin()
launcher_config = f"/home/{username}/.config/launcher.json"

COLOR_OK = (145, 238, 145)
COLOR_WARN = (255, 166, 0)
COLOR_ERR = (255, 0, 0)
COLOR_SOFT_RED = (248, 112, 112)
COLOR_AZURE = (97, 175, 191)

def classToColor (cl):
    if not cl: return (255, 255, 255)
    if cl == "ok-color": return COLOR_OK
    if cl == "warn-color": return COLOR_WARN
    if cl == "err-color": return COLOR_ERR
    if cl == "azure-color": return COLOR_AZURE
    # if cl == "fully": return (255, 255, 255)
    if cl == "nodata-color": return COLOR_SOFT_RED
    return (128, 128, 128)

def getColorCode (r, g, b):
    return f"\033[38;2;{r};{g};{b}m"
endColorCode = "\033[0m"

def colorize (txt, c, bold = False):
    c0 = getColorCode(*c)
    return f"{bold and '\033[1m' or ''} {c0}{txt}{endColorCode}"

# Function to get system info
def get_system_info():
    time_now = time.strftime("%Y-%m-%d %H:%M")
    brightness = system.get_brightness()
    # volume = system.get_volume()
    vol = system.get_volume_info()
    percentage, plugged, remaining = system.get_battery_state()
    remaining = f"󱧥 {time.strftime('%H:%M', time.gmtime(remaining))}" if not remaining == -2 else ''
    charging = '󰚥' if plugged else '󰚦'
    keyboard_layout = system.get_keyboard()
    #keyboard_layout = subprocess.getoutput("setxkbmap -query | grep layout | awk '{print $2}'")

    top_bar = f"󰥔 {time_now} | 󰌌 {keyboard_layout} | {vol['icon']} {vol['value']}%"
    if brightness is not None: tob_bar += f" | 󰃟 {brightness}%"
    if percentage: top_bar += f"| 󱐋 {percentage}% {remaining} {charging} "
    # top_bar += " | " + colorize("Prova", (150,180,160))

    met = system.get_meteo_info()
    color = (255, 255, 255)
    if met['text'][0] in ['C', 'M']: color = (253, 231, 76)
    elif met['text'][0] == 'R': color = (65, 171, 251)
    elif met['text'][0] == 'P': color = (128, 128, 128)
    top_bar += f' | {colorize(met['icon'] or met['text'], color, True)} {met['temp']}{met['temp_unit']}'
    # top_bar += f' | {colorize(met['text'], color)} {met['temp_unit']}'

    # top_bar += "\033[48;2;200;10;40mProva" # 48 per lo sfondo
    with open("/tmp/launcher_top_bar", "w") as f:
        f.write(top_bar)

def get_system_info_cycle():
    while True:
        get_system_info()
        time.sleep(0.5)

def run_fzf(options):
    fzf_command = (
        "fzf --header-lines=0 --no-info "
        "--preview 'while true; do echo \"$(cat /tmp/launcher_top_bar)\"; sleep 0.5; done;' "
        "--preview-window=up:1:follow:wrap:noinfo"
    )
    fzf_input = "\n".join(options)
    result = subprocess.run(fzf_command, input=fzf_input, text=True, shell=True, stdout=subprocess.PIPE)
    return result.stdout.strip()

def normal_mode():
    desktop_dirs = [
        "/usr/share/applications",
        f"/home/{username}/.local/share/applications",
        "/var/lib/flatpak/exports/share/applications",
        f"/home/{username}/.local/share/flatpak/exports/share/applications"
    ]
    desktop_files = [
        str(file) for dir_ in desktop_dirs for file in Path(dir_).glob("*.desktop") if file.is_file()
    ]

    options = []
    exec_map = {}

    for desktop_file in desktop_files:
        with open(desktop_file) as f:
            lines = f.readlines()
        name = next((line.split("=", 1)[1].strip() for line in lines if line.startswith("Name=")), "Unknown")
        exec_cmd = next((line.split("=", 1)[1].strip() for line in lines if line.startswith("Exec=")), "")

        # Handle placeholders in the Exec command
        exec_cmd = exec_cmd.replace("%u", "").replace("%U", "").replace("%f", "").replace("%F", "").strip()
        exec_cmd = exec_cmd.replace("@@u", "").replace("@@", "").strip()

        # Handle Flatpak apps
        if "flatpak run" in exec_cmd and not exec_cmd.startswith("/usr/bin/flatpak"):
            app_id = exec_cmd.split("flatpak run", 1)[-1].strip()
            exec_cmd = f"flatpak run {app_id}"

        if name and exec_cmd:
            options.append(name)
            exec_map[name] = exec_cmd

    options.extend([":w", ":d", ":q"])
    selection = run_fzf(options)

    if selection == ":w":
        window_mode()
    elif selection == ":d":
        dashboard_mode()
    elif selection == ":q":
        exit()
    elif selection in exec_map:
        process = subprocess.Popen(exec_map[selection], shell=True, start_new_session=True)
        # print(env)
        exit()

# Window mode: Focus a window
def window_mode():
    global current_mode
    current_mode = "window"

    window_data = subprocess.getoutput("niri msg windows")
    windows = window_data.split("\n\n")

    options = []
    window_map = {}

    for window in windows:
        lines = [line.strip() for line in window.split("\n") if line.strip()]
        window_id = next((line.split(" ", 2)[2].strip(":") for line in lines if line.startswith("Window ID")), None)
        title = next((line.split(": ", 1)[1] for line in lines if line.startswith("Title:")), None)
        title = title.replace('"', '')

        if window_id and title:
            options.append(title)
            window_map[title] = window_id

    options.extend([":n", ":d", ":q"])
    selection = run_fzf(options)

    if selection == ":n":
        normal_mode()
    elif selection == ":d":
        dashboard_mode()
    elif selection == ":q":
        exit()
    elif selection in window_map:
        window_id = window_map[selection]
        subprocess.run(f"niri msg action focus-window --id {window_id}", shell=True)
        exit()

# Dashboard mode: Launch configured apps
def dashboard_mode():
    global current_mode
    current_mode = "dashboard"

    if not Path(launcher_config).exists():
        print(f"Config file not found at {launcher_config}")
        exit()

    with open(launcher_config) as f:
        dashboards = json.load(f)

    options = [d["name"] for d in dashboards]
    exec_map = {d["name"]: d["exec"] for d in dashboards}

    options.extend([":n", ":w", ":q"])
    selection = run_fzf(options)

    if selection == ":n":
        normal_mode()
    elif selection == ":w":
        window_mode()
    elif selection == ":q":
        exit()
    elif selection in exec_map:
        subprocess.run(exec_map[selection], shell=True)
        dashboard_mode()

if True:
    # Start system info updater thread
    threading.Thread(target=get_system_info_cycle, daemon=True).start()

    # Start in normal mode
    normal_mode()
else:
    get_system_info()
    with open("/tmp/launcher_top_bar", "r") as f:
        print(f.readline())
