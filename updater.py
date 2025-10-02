import os
import sys
import shutil
import time
import subprocess
import ctypes

def show_warning():
    ctypes.windll.user32.MessageBoxW(
        0,
        "this program is only the HORSE updater and is not meant to be run directly.\n\n"
        "please run HORSE.exe instead.",
        "Updater",
        0x30  # MB_ICONWARNING
    )

def main():
    try:
        if not os.path.exists("HORSE_NEW.exe"):
            show_warning()
            return

        while "HORSE.exe" in os.popen("tasklist").read():
            time.sleep(1)

        shutil.move("HORSE_NEW.exe", "HORSE.exe")

        with open("update_complete.flag", "w") as f:
            f.write("update_complete")

        subprocess.Popen(["HORSE.exe"], shell=True)

    except Exception as e:
        with open("update_error.log", "w") as f:
            f.write(str(e))

if __name__ == "__main__":
    main()