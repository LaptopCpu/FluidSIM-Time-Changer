import os
import subprocess
import json
import time
import datetime
import sys
import ctypes

def hide_console():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    else:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        return False if int(ret) > 32 else sys.exit()

appdata_path = os.path.join(os.environ['APPDATA'], "FluidSIM_Bypass")
if not os.path.exists(appdata_path):
    os.makedirs(appdata_path)

CONFIG_FILE = os.path.join(appdata_path, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_config(path, hours):
    config = {"path": path, "hours": hours}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    return config

def set_system_time(target_time):
    new_date_time = target_time.strftime("%m/%d/%Y %H:%M:%S")
    ps_cmd = f"Set-Date -Date '{new_date_time}'"
    return subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True).returncode == 0

def resync_time():
    commands = ["net start w32time", "w32tm /resync /force"]
    for cmd in commands:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)

def main():
    if not is_admin():
        run_as_admin()
        return

    TITLE_ART = r"""
      ____            ______ _         _     _  _____ _____ __  __ 
     /    \          |  ____| |       (_)   | |/ ____|_   _|  \/  |
    |  /|  |         | |__  | | _   _  _  __| | (___   | | | \  / |
    |   |  |         |  __| | || | | || |/ _` |\___ \  | | | |\/| |
     \____/          | |    | || |_| || | (_| |____) |_| |_| |  | |
                     |_|    |_| \__,_||_|\__,_|_____/|_____|_|  |_|
                                               
  _______ _                   _____ _                                    
 |__   __(_)                 / ____| |                                   
    | |   _ _ __ ___   ___  | |    | |__   __ _ _ __   __ _  ___ _ __ 
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
        try:
            hours = float(input("Gesamt-Laufzeit in Stunden: "))
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
        elif choice == 'z':
            try:
                config['hours'] = float(input("Neue Gesamt-Laufzeit in Stunden: "))
                save_config(config['path'], config['hours'])
            except:
                print("Ungültige Eingabe.")

    offset_hours = float(config["hours"]) - 0.5
    back_dated_time = datetime.datetime.now() - datetime.timedelta(hours=offset_hours)

    print("\nBitte warten...")
    
    if set_system_time(back_dated_time):
        if os.path.exists(config['path']):
            time.sleep(1)
            hide_console()
            process = subprocess.Popen(f'"{config["path"]}"', shell=True)
            process.wait()
            resync_time()
            sys.exit()
        else:
            print(f"\n[FEHLER] FluidSIM wurde nicht gefunden.")
            resync_time()
            time.sleep(5)
    else:
        print("\n[FEHLER] Systemzeit konnte nicht geändert werden.")
        time.sleep(5)

if __name__ == "__main__":
    main()