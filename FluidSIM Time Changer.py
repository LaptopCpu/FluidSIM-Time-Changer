#V2 since I didn't calculate, that FluidSIM only starts the timer for the 30 Minutes, after you clicked on the "OK"-Button at the beginning of the program launching.
#Therefore this updated version automatically clicks the window for you and adjusts the time afterwards.

import os
import subprocess
import json
import time
import datetime
import sys
import ctypes

from ctypes import wintypes
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

def count_fluid_sim_windows():
    count = []
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            if "FluidSIM" in buff.value:
                count.append(hwnd)
        return True
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(foreach_window), 0)
    return len(count)

def set_windows_auto_time(enabled=True):
    val = 1 if enabled else 0
    sync_type = "NTP" if enabled else "NoSync"
    subprocess.run(["powershell", "-Command", f"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\W32Time\\TimeProviders\\NtpClient' -Name 'Enabled' -Value {val}"], capture_output=True)
    subprocess.run(["powershell", "-Command", f"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\W32Time\\Parameters' -Name 'Type' -Value '{sync_type}'"], capture_output=True)
    if enabled:
        subprocess.run(["powershell", "-Command", "Start-Service w32time"], capture_output=True)

def is_auto_time_enabled():
    cmd = "Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\W32Time\\TimeProviders\\NtpClient' -Name 'Enabled'"
    result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
    return "1" in result.stdout

def hide_console():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    if is_admin(): return True
    else:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

appdata_path = os.path.join(os.environ['APPDATA'], "FluidSIM_Bypass")
if not os.path.exists(appdata_path): os.makedirs(appdata_path)
CONFIG_FILE = os.path.join(appdata_path, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return None
    return None

def save_config(path, hours):
    config = {"path": path, "hours": hours}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(config, f, indent=4)
    return config

def set_system_time(target_time):
    ps_cmd = f"Set-Date -Date (Get-Date -Year {target_time.year} -Month {target_time.month} -Day {target_time.day} -Hour {target_time.hour} -Minute {target_time.minute})"
    return subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True).returncode == 0

def resync_time():
    commands = [
        "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\W32Time\\TimeProviders\\NtpClient' -Name 'Enabled' -Value 1",
        "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\W32Time\\Parameters' -Name 'Type' -Value 'NTP'",
        "net start w32time",
        "w32tm /resync /force"
    ]
    for cmd in commands:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)

def main():
    if not is_admin():
        run_as_admin()
        return

    TITLE_ART = r"""
#V2   ____            ______ _         _     _  _____ _____ __  __ 
     /    \          |  ____| |       (_)   | |/ ____|_  _ |  \/  |
    |  /|  |         | |__  | | _   _  _  __| | (___   | | | \  / |
    |   |  |         |  __| | || | | || |/ _` |\___ \  | | | |\/| |
     \____/          | |    | || |_| || | (_| |____) |_| |_| |  | |
                     |_|    |_| \__,_||_|\__,_|_____/|_____|_|  |_|
                                               
  _______ _                   _____ _                         
 |__   __(_)                 / ____| |                        
    | |   _ _ __ __    ___  | |    | |__   __ _ _ __   __ _  ___ _ __ 
    | |  | | '_ ` _ \ / _ \ | |    | '_ \ / _` | '_ \ / _` |/ _ \ '__|
    | |  | | | | | | |  __/ | |____| | | | (_| | | | | (_| |  __/ |    
    |_|  |_|_| |_| |_|\___|  \_____|_| |_|\__,_|_| |_|\__, |\___|_|    
                                                       __/ |           
                                                      |___/       
    """
    print(TITLE_ART)
    
    config = load_config()

    if not config:
        print("\n--- Ersteinrichtung ---")
        path = input("Pfad zu FluidSIM.exe einfügen: ").strip('"')
        try: hours = float(input("Gesamt-Laufzeit in Stunden: "))
        except: return
        config = save_config(path, hours)
    else:
        print(f"[INFO] Konfigurationsdatei: {CONFIG_FILE}")
        print(f"[INFO] Aktueller Pfad: {config['path']}")
        print(f"[INFO] Gesamt-Laufzeit: {config['hours']} Stunden")
        print("\nOptionen: [P] Pfad ändern | [Z] Zeit ändern | [Enter] FluidSIM starten")
        choice = input("\nDeine Wahl: ").strip().lower()
        if choice == 'p':
            config['path'] = input("Neuen Pfad einfügen: ").strip('"')
            save_config(config['path'], config['hours'])
            return main()
        elif choice == 'z':
            try:
                config['hours'] = float(input("Neue Gesamt-Laufzeit in Stunden: "))
                save_config(config['path'], config['hours'])
                return main()
            except: print("Ungültige Eingabe.")

    if not os.path.exists(config['path']):
        print(f"\n[FEHLER] FluidSIM nicht gefunden.")
        time.sleep(5)
        return

    offset_hours = float(config["hours"]) - 0.5
    back_dated_time = datetime.datetime.now() - datetime.timedelta(hours=offset_hours)

    print("\n[VORGANG] FluidSIM wird gestartet...")
    process = subprocess.Popen(f'"{config["path"]}"', shell=True)

    wait_time = 1
    for i in range(wait_time, 0, -1):
        print(f"\r[VORGANG] Initialisiere FluidSIM... Bitte warten ({i}s) ", end="")
        time.sleep(1)
    print("\n[OK] FluidSIM bereit.")

    print("[VORGANG] Schließe Demo-Meldung automatisch...")
    ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
    time.sleep(0.1)
    ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)

    hide_console()

    time.sleep(1)
    
    #hide_console() For debugging

    was_auto_time_enabled = is_auto_time_enabled()
    if was_auto_time_enabled:
        set_windows_auto_time(False)

    if set_system_time(back_dated_time):
        print("[OK] Zeit-Bypass erfolgreich aktiviert.")
        
        #hide_console() For debugging as well
        
        process.wait()

        if was_auto_time_enabled:
            set_windows_auto_time(True)
        resync_time()
        sys.exit()

if __name__ == "__main__":
    main()