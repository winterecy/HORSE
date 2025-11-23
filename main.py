import sys
import random
import time
import threading
import json
import os
import keyboard
import pynput
import requests
import zipfile
import shutil
import subprocess
import winreg
import pygame
import ctypes
import webbrowser
import platform

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox, QMessageBox, QAction,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QObject, pyqtSignal
from pynput import keyboard as pynput_keyboard
from packaging.version import Version

CONFIG_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "overlay_config.json")
active_overlays = []

VERSION = "1.4.4"
UPDATE_URL = "https://raw.githubusercontent.com/winterecy/HORSE/refs/heads/master/latest.json"

pygame.mixer.init()

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_config_file():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_config_file(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")


def startup(name, path):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"the horse was not able to run on startup: {e}")


def update_check():
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            latest_info = response.json()
            latest_version = latest_info.get("version")
            download_url = latest_info.get("url")

            if latest_version and Version(latest_version) > Version(VERSION):
                reply = QMessageBox.question(None, "please update me",
                                             f"The HORSE is gungry and needs updated to version {latest_version}. install it please?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    download_update(download_url)
    except Exception as e:
        print(f"Update check failed: {e}")


def download_update(url):
    try:
        r = requests.get(url, stream=True)
        with open("update_temp.zip", "wb") as f:
            shutil.copyfileobj(r.raw, f)

        with zipfile.ZipFile("update_temp.zip", "r") as zip_ref:
            zip_ref.extractall("update_temp")

        shutil.copy("update_temp/HORSE.exe", "HORSE_NEW.exe")

        subprocess.Popen(["updater.exe"], shell=True)

        os.remove("update_temp.zip")
        shutil.rmtree("update_temp")
        sys.exit()

    except Exception as e:
        QMessageBox.critical(None, "FUCK", str(e))


def run_updater():
    updater_path = os.path.abspath("updater.exe")
    if not (os.path.exists(updater_path)):
        QMessageBox.warning(None, "???", "failed to find updater.exe")
        return

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        updater_path,
        None,
        None,
        1
    )
    sys.exit()

class FadingOverlay(QLabel):
    def __init__(self, image_path, duration, max_width, max_height):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self.duration = duration
        pixmap = QPixmap(image_path)

        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.setPixmap(pixmap)
        self.resize(pixmap.size())

        screens = QApplication.screens()
        screen = random.choice(screens)
        screen_geometry = screen.geometry()

        screen_width, screen_height = screen_geometry.width(), screen_geometry.height()
        img_width = pixmap.width()
        img_height = pixmap.height()

        x = random.randint(screen_geometry.x(), screen_geometry.x() + max(0, screen_width - img_width))
        y = random.randint(screen_geometry.y(), screen_geometry.y() + max(0, screen_height - img_height))
        self.move(QPoint(x, y))
        self.show()

        QTimer.singleShot(int(self.duration * 1000), self.fade_out)

    def fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.cleanup)
        self.anim.start()

    def cleanup(self):
        if self in active_overlays:
            active_overlays.remove(self)
        self.close()


class HotkeyListener(QObject):
    trigger = pyqtSignal()

    def __init__(self, hotkey):
        super().__init__()
        self.hotkey = hotkey
        self.listener = pynput_keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char == self.hotkey:
                self.trigger.emit()
        except:
            pass


class OverlayController(QObject):
    clear_overlays_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

def start_delete_listener(controller: "OverlayController"):
    def on_press(key):
        if key == pynput_keyboard.Key.delete:
            controller.clear_overlays_signal.emit()

    listener = pynput_keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Overlay Settings - v{VERSION}")
        self.setFixedSize(420, 420)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        self.image_path_input = QLineEdit("")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_image)
        img_row = QHBoxLayout()
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_button)
        main_layout.addLayout(img_row)
        main_layout.addWidget(QLabel("Image On Press"))

        self.sound_path_input = QLineEdit("")
        browse_sound_button = QPushButton("Browse")
        browse_sound_button.clicked.connect(self.browse_sound)
        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_path_input)
        sound_row.addWidget(browse_sound_button)
        main_layout.addLayout(sound_row)
        main_layout.addWidget(QLabel("Sound On Press (WAV/MP3)"))

        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0.1, 60.0)
        self.duration_input.setSingleStep(0.1)
        self.duration_input.setDecimals(2)
        self.duration_input.setValue(5.0)
        main_layout.addWidget(QLabel("Duration (seconds)"))
        main_layout.addWidget(self.duration_input)

        self.max_width_input = QSpinBox()
        self.max_width_input.setRange(10, 1000)
        self.max_width_input.setValue(300)

        self.max_height_input = QSpinBox()
        self.max_height_input.setRange(10, 1000)
        self.max_height_input.setValue(300)

        main_layout.addWidget(QLabel("Max Width"))
        main_layout.addWidget(self.max_width_input)
        main_layout.addWidget(QLabel("Max Height"))
        main_layout.addWidget(self.max_height_input)

        self.hotkey_input = QLineEdit("h")
        main_layout.addWidget(QLabel("Hotkey"))
        main_layout.addWidget(self.hotkey_input)

        button_row = QHBoxLayout()
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        button_row.addWidget(save_button)
        button_row.addWidget(load_button)
        main_layout.addLayout(button_row)

        start_button = QPushButton("Start Overlay")
        start_button.clicked.connect(self.start_overlay)
        main_layout.addWidget(start_button)

        flag_layout = QHBoxLayout()
        flag_layout.addStretch(1)


        flag_label = QLabel()
        
        flag_path = resource_path("lesbian_flag.png")
        flag_pixmap = QPixmap(flag_path)
        print(flag_pixmap.isNull())
        if not flag_pixmap.isNull():
            flag_pixmap = flag_pixmap.scaled(64, 40, 
                                             Qt.AspectRatioMode.KeepAspectRatio, 
                                             Qt.TransformationMode.SmoothTransformation)
            flag_label.setPixmap(flag_pixmap)
        flag_layout.addWidget(flag_label)
        main_layout.addLayout(flag_layout)

        self.setLayout(main_layout)
        self.load_config()

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            self.image_path_input.setText(file_path)

    def browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Sound", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.sound_path_input.setText(file_path)

    def start_overlay(self):
        image_path = self.image_path_input.text()
        duration = self.duration_input.value()
        max_width = self.max_width_input.value()
        max_height = self.max_height_input.value()
        hotkey = self.hotkey_input.text().strip().lower()

        if not image_path:
            QMessageBox.warning(self, "Missing Image", "Please select an image.")
            return

        self.hide()
        self.overlay_app = OverlayApp(image_path, duration, max_width, max_height, hotkey)
        self.overlay_app.run()

    def save_config(self):
        config = load_config_file()
        config.update({
            "image_path": self.image_path_input.text(),
            "sound_path": self.sound_path_input.text(),
            "duration": self.duration_input.value(),
            "max_width": self.max_width_input.value(),
            "max_height": self.max_height_input.value(),
            "hotkey": self.hotkey_input.text().strip().lower()
        })
        save_config_file(config)
        QMessageBox.information(self, "Config Saved", "Settings saved successfully.")

    def load_config(self):
        config = load_config_file()
        self.image_path_input.setText(config.get("image_path", ""))
        self.sound_path_input.setText(config.get("sound_path", ""))
        self.duration_input.setValue(config.get("duration", 5))
        self.max_width_input.setValue(config.get("max_width", 300))
        self.max_height_input.setValue(config.get("max_height", 300))
        self.hotkey_input.setText(config.get("hotkey", "h"))

class OverlayApp:
    def __init__(self, image_path, duration, max_width, max_height, hotkey, sound_path=""):
        self.image_path = image_path
        self.duration = duration
        self.max_width = max_width
        self.max_height = max_height
        self.hotkey = hotkey
        self.sound_path = sound_path
        self.listener = None

    def run(self):
        if self.listener:
            try:
                self.listener.listener.stop()
            except Exception as e:
                print(f"this program fucking sucks (listener stop failed): {e}")
            self.listener = None

        self.listener = HotkeyListener(self.hotkey)
        self.listener.trigger.connect(self.show_overlay)

    def show_overlay(self):
        overlay = FadingOverlay(self.image_path, self.duration, self.max_width, self.max_height)
        active_overlays.append(overlay)
        if self.sound_path and self.sound_path != "" and os.path.exists(self.sound_path):
            threading.Thread(target=self.play_sound, args=(self.sound_path,), daemon=True).start()

    def play_sound(self, path):
        try:
            sound = pygame.mixer.Sound(path)
            sound.play()
        except Exception as e:
            print(f"fuck you pygame: {e}")


def main():
    app = QApplication(sys.argv)
    
    update_flag_file = "update_complete.flag"
    if os.path.exists(update_flag_file):
        os.remove(update_flag_file)
    else:
        update_check()

    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    startup("HORSE", exe_path)

    config = load_config_file()

    if "open_yurion" not in config:
        reply = QMessageBox.question(
            None,
            "yurion.top",
            "the horse REALLY likes https://yurion.top ... can she open it on startup?",
            QMessageBox.Yes | QMessageBox.No
        )
        config["open_yurion"] = (reply == QMessageBox.Yes)
        save_config_file(config)
    
    
    # i love you emily
    pc_name = os.getenv("COMPUTERNAME") or platform.node()
    
    if pc_name == "DESKTOP-MRFAJ19":
            QMessageBox.information(
            None,
            "i love you",
            "i love you emily",
            QMessageBox.Ok
        )
    
    # billie
    if pc_name == "BB_Dawnstar":
        webbrowser.open("https://hl2x.com/cat")

        
    if pc_name == "BB-Evocity":
        webbrowser.open("https://hl2x.com/cat")
    
    # a6
    if pc_name == "DESKTOP-HARLVRB":
        QMessageBox.information(
            webbrowser.open("https://a6hawk.com/kill/kill.webm")
        )

    if config.get("open_yurion", False):
        webbrowser.open("https://yurion.top")

    icon_path = resource_path("horse_button.png")
    icon = QIcon(icon_path)
    if icon.isNull():
        print("Tray icon failed to load. Check path:", icon_path)

    tray_icon = QSystemTrayIcon(icon, parent=app)
    tray_menu = QMenu()
    tray_icon.setVisible(True)

    overlay_app = OverlayApp("", 0, 0, 0, "")
    settings_window = SettingsWindow()

    def start_overlay():
        image_path = settings_window.image_path_input.text()
        sound_path = settings_window.sound_path_input.text()
        duration = settings_window.duration_input.value()
        max_width = settings_window.max_width_input.value()
        max_height = settings_window.max_height_input.value()
        hotkey = settings_window.hotkey_input.text().strip().lower()

        if not image_path:
            QMessageBox.warning(settings_window, "Missing Image", "Please select an image.")
            return

        overlay_app.image_path = image_path
        overlay_app.sound_path = sound_path
        overlay_app.duration = duration
        overlay_app.max_width = max_width
        overlay_app.max_height = max_height
        overlay_app.hotkey = hotkey
        overlay_app.run()
        settings_window.hide()

    for btn in settings_window.findChildren(QPushButton):
        if btn.text() == "Start Overlay":
            btn.clicked.disconnect()
            btn.clicked.connect(start_overlay)

    open_settings_action = QAction("Open Settings")
    open_settings_action.triggered.connect(settings_window.show)

    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)

    tray_menu.addAction(open_settings_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    controller = OverlayController()

    def clear_overlays():
        for overlay in list(active_overlays):
            overlay.close()
            if overlay in active_overlays:
                active_overlays.remove(overlay)

    controller.clear_overlays_signal.connect(clear_overlays)
    start_delete_listener(controller)

    try:
        image_path = config.get("image_path", "")
        sound_path = config.get("sound_path", "")
        duration = config.get("duration", 5)
        max_width = config.get("max_width", 300)
        max_height = config.get("max_height", 300)
        hotkey = config.get("hotkey", "h").strip().lower()

        if image_path:
            overlay_app = OverlayApp(image_path, duration, max_width, max_height, hotkey, sound_path)
            overlay_app.run()
        else:
            settings_window.show()
    except Exception as e:
        print(f"Failed to load config: {e}")
        settings_window.show()


    sys.exit(app.exec())


if __name__ == "__main__":
    main()
