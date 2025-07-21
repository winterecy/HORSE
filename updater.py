import os
import sys
import shutil
import time
import subprocess

def main():
    try:
        while True:
            tasks = os.popen('tasklist').read()
            if "HORSE.exe" not in tasks:
                break
            time.sleep(1)
        
        shutil.move("HORSE_NEW.exe", "HORSE.exe")

        subprocess.Popen(["HORSE.exe"], shell=True)
    
    except Exception as e:
        with open("update_error.log", "w") as f:
            f.write(str(e))

if __name__ == "__main__":
    main()