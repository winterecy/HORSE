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
    QSystemTrayIcon, QMenu, QFormLayout, QSlider, QFrame
)
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QObject, pyqtSignal
from pynput import keyboard as pynput_keyboard
from packaging.version import Version

CONFIG_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "overlay_config.json")
active_overlays = []

VERSION = "1.4.3"
UPDATE_URL = "https://raw.githubusercontent.com/winterecy/HORSE/refs/heads/master/latest.json"

pygame.mixer.init()

def apply_theme(app: QApplication):
	app.setStyle("Fusion")

	palette = QPalette()
	bg = QColor(20, 22, 24)
	panel = QColor(32, 35, 38)
	alt = QColor(28, 30, 33)
	text = QColor(220, 220, 220)
	muted = QColor(170, 176, 182)
	accent = QColor(90, 157, 255)
	accent_hover = QColor(110, 172, 255)
	warn = QColor(255, 88, 88)

	palette.setColor(QPalette.Window, bg)
	palette.setColor(QPalette.WindowText, text)
	palette.setColor(QPalette.Base, alt)
	palette.setColor(QPalette.AlternateBase, panel)
	palette.setColor(QPalette.ToolTipBase, panel)
	palette.setColor(QPalette.ToolTipText, text)
	palette.setColor(QPalette.Text, text)
	palette.setColor(QPalette.Button, panel)
	palette.setColor(QPalette.ButtonText, text)
	palette.setColor(QPalette.BrightText, warn)
	palette.setColor(QPalette.Highlight, accent)
	palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
	palette.setColor(QPalette.PlaceholderText, muted)
	palette.setColor(QPalette.Disabled, QPalette.Text, muted)
	palette.setColor(QPalette.Disabled, QPalette.ButtonText, muted)

	app.setPalette(palette)

	app.setStyleSheet(
		"""
		QWidget { background-color: #141618; color: #DCDCDC; font-size: 13px; }
		QLabel { color: #DCDCDC; }
		QLineEdit, QSpinBox, QDoubleSpinBox {
			background-color: #1C1E21; color: #E6E6E6; border: 1px solid #2A2E33; border-radius: 6px; padding: 6px 8px;
		}
		QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #5A9DFF; }
		QPushButton {
			background-color: #262A2F; color: #E6E6E6; border: 1px solid #323840; border-radius: 8px; padding: 8px 12px; font-weight: 600;
		}
		QPushButton:hover { background-color: #2B3036; border-color: #3A424C; }
		QPushButton:pressed { background-color: #23272C; }
		QPushButton:default { background-color: #5A9DFF; border: none; color: #0E1113; }
		QPushButton:default:hover { background-color: #6EACFF; }
		QMenu { background-color: #1F2327; color: #E6E6E6; border: 1px solid #2A2E33; }
		QMenu::item { padding: 6px 18px; }
		QMenu::item:selected { background-color: #2A2F35; }
		QToolTip { background-color: #1F2327; color: #FFFFFF; border: 1px solid #2A2E33; }
		QScrollBar:vertical { background: #141618; width: 10px; margin: 0; }
		QScrollBar::handle:vertical { background: #2B3036; min-height: 20px; border-radius: 5px; }
		QScrollBar::handle:vertical:hover { background: #343A41; }
		QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
		"""
	)

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
        self.setMinimumSize(420, 420)
        self.resize(520, 520)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        left_col = QVBoxLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)

        self.image_path_input = QLineEdit("")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_image)
        img_row = QHBoxLayout()
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_button)
        form.addRow("Image On Press", img_row)

        self.sound_path_input = QLineEdit("")
        browse_sound_button = QPushButton("Browse")
        browse_sound_button.clicked.connect(self.browse_sound)
        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_path_input)
        sound_row.addWidget(browse_sound_button)
        form.addRow("Sound On Press (WAV/MP3)", sound_row)

        duration_container = QHBoxLayout()
        self.duration_slider = QSlider(Qt.Horizontal)
        self.duration_slider.setRange(1, 600)
        self.duration_slider.setValue(50)
        self.duration_slider.setTickPosition(QSlider.TicksBelow)
        self.duration_slider.setTickInterval(50)
        self.duration_label = QLabel("5.0s")
        self.duration_slider.valueChanged.connect(self.update_duration_label)
        duration_container.addWidget(self.duration_slider)
        duration_container.addWidget(self.duration_label)
        form.addRow("Duration (seconds)", duration_container)

        self.max_width_input = QSpinBox()
        self.max_width_input.setRange(10, 1000)
        self.max_width_input.setValue(300)
        form.addRow("Max Width", self.max_width_input)

        self.max_height_input = QSpinBox()
        self.max_height_input.setRange(10, 1000)
        self.max_height_input.setValue(300)
        form.addRow("Max Height", self.max_height_input)

        hotkey_container = QHBoxLayout()
        
        self.hotkey_display = QLabel("H")
        self.hotkey_display.setStyleSheet("""
            QLabel {
                border: 2px solid #5A9DFF;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #1C1E21;
                color: #5A9DFF;
                font-weight: bold;
                font-size: 14px;
                min-width: 60px;
            }
        """)
        self.hotkey_display.setAlignment(Qt.AlignCenter)
        
        self.record_hotkey_btn = QPushButton("Record")
        self.record_hotkey_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        self.record_hotkey_btn.clicked.connect(self.start_hotkey_recording)
        
        self.clear_hotkey_btn = QPushButton("Clear")
        self.clear_hotkey_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        self.clear_hotkey_btn.clicked.connect(self.clear_hotkey)
        
        hotkey_container.addWidget(self.hotkey_display)
        hotkey_container.addWidget(self.record_hotkey_btn)
        hotkey_container.addWidget(self.clear_hotkey_btn)
        
        form.addRow("Hotkey", hotkey_container)

        left_col.addLayout(form)

        button_row = QHBoxLayout()
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        button_row.addWidget(save_button)
        button_row.addWidget(load_button)
        left_col.addLayout(button_row)

        start_button = QPushButton("Start Overlay")
        start_button.clicked.connect(self.start_overlay)
        left_col.addWidget(start_button)
        left_col.addStretch(1)

        right_col = QVBoxLayout()
        preview_label = QLabel("Preview")
        right_col.addWidget(preview_label)

        self.image_preview = QLabel()
        self.image_preview.setFixedSize(200, 150)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("border: 1px solid #2A2E33; border-radius: 6px; background-color: #1C1E21;")
        right_col.addWidget(self.image_preview)
        self.image_path_input.textChanged.connect(self.update_image_preview)

        sound_controls = QHBoxLayout()
        self.play_btn = QPushButton("Play Sound")
        self.stop_btn = QPushButton("Stop")
        self.play_btn.clicked.connect(self.play_preview_sound)
        self.stop_btn.clicked.connect(self.stop_preview_sound)
        self.stop_btn.setEnabled(False)
        sound_controls.addWidget(self.play_btn)
        sound_controls.addWidget(self.stop_btn)
        right_col.addLayout(sound_controls)
        right_col.addStretch(1)

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
        right_col.addLayout(flag_layout)

        main_layout.addLayout(left_col, 2)
        main_layout.addLayout(right_col, 1)
        self.setLayout(main_layout)
        self.load_config()
        self.update_image_preview()

        # runtime handle for preview sound
        self._preview_channel = None
        self._preview_sound = None
        
        # hotkey recording state
        self._hotkey_recording = False
        self._hotkey_listener = None
        self._current_hotkey = "h"

    def update_duration_label(self, value):
        duration = value / 10.0
        self.duration_label.setText(f"{duration:.1f}s")

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            self.image_path_input.setText(file_path)
            self.update_image_preview()

    def browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Sound", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.sound_path_input.setText(file_path)

    def update_image_preview(self):
        path = self.image_path_input.text().strip()
        if not path or not os.path.exists(path):
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("No Image")
            return
        pix = QPixmap(path)
        if pix.isNull():
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("Invalid Image")
            return
        target = self.image_preview.size()
        scaled = pix.scaled(target.width(), target.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_preview.setText("")
        self.image_preview.setPixmap(scaled)

    def play_preview_sound(self):
        path = self.sound_path_input.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Sound", "Please select a valid sound file.")
            return
        try:
            self.stop_preview_sound()
            self._preview_sound = pygame.mixer.Sound(path)
            self._preview_channel = self._preview_sound.play()
            self.stop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Sound", f"Failed to play sound: {e}")

    def stop_preview_sound(self):
        try:
            if self._preview_channel is not None:
                self._preview_channel.stop()
            self._preview_channel = None
            self._preview_sound = None
        finally:
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(False)

    def start_overlay(self):
        image_path = self.image_path_input.text()
        duration = self.duration_slider.value() / 10.0
        max_width = self.max_width_input.value()
        max_height = self.max_height_input.value()
        hotkey = self._current_hotkey.lower()

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
            "duration": self.duration_slider.value() / 10.0,
            "max_width": self.max_width_input.value(),
            "max_height": self.max_height_input.value(),
            "hotkey": self._current_hotkey.lower()
        })
        save_config_file(config)
        QMessageBox.information(self, "Config Saved", "Settings saved successfully.")

    def load_config(self):
        config = load_config_file()
        self.image_path_input.setText(config.get("image_path", ""))
        self.sound_path_input.setText(config.get("sound_path", ""))
        duration_value = int(config.get("duration", 5.0) * 10)
        self.duration_slider.setValue(duration_value)
        self.update_duration_label(duration_value)
        self.max_width_input.setValue(config.get("max_width", 300))
        self.max_height_input.setValue(config.get("max_height", 300))
        hotkey = config.get("hotkey", "h")
        self._current_hotkey = hotkey.upper()
        self.update_hotkey_display()

    def start_hotkey_recording(self):
        """Start recording a new hotkey combination."""
        if self._hotkey_recording:
            self.stop_hotkey_recording()
            return
        
        self._hotkey_recording = True
        self.record_hotkey_btn.setText("Recording...")
        self.record_hotkey_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 12px;
                background-color: #FF5858;
                color: white;
            }
        """)
        self.hotkey_display.setText("Press keys...")
        
        self._hotkey_listener = pynput_keyboard.Listener(
            on_press=self.on_hotkey_record_press,
            on_release=self.on_hotkey_record_release
        )
        self._hotkey_listener.start()
        
        QTimer.singleShot(10000, self.stop_hotkey_recording)

    def stop_hotkey_recording(self):
        """Stop recording hotkey and update display."""
        self._hotkey_recording = False
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except:
                pass
            self._hotkey_listener = None
        
        self.record_hotkey_btn.setText("Record")
        self.record_hotkey_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                font-size: 12px;
            }
        """)
        self.update_hotkey_display()

    def on_hotkey_record_press(self, key):
        """Handle key press during hotkey recording."""
        if not self._hotkey_recording:
            return
        
        try:
            key_str = self.key_to_display_string(key)
            if key_str:
                self._current_hotkey = key_str
                self.update_hotkey_display()
                QTimer.singleShot(100, self.stop_hotkey_recording)
        except Exception as e:
            print(f"Hotkey recording error: {e}")

    def on_hotkey_record_release(self, key):
        """Handle key release during hotkey recording."""
        pass

    def key_to_display_string(self, key):
        """Convert pynput key to display string."""
        if hasattr(key, 'char') and key.char is not None:
            return key.char.upper()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            special_keys = {
                'space': 'SPACE',
                'enter': 'ENTER', 
                'tab': 'TAB',
                'esc': 'ESC',
                'backspace': 'BACKSPACE',
                'delete': 'DELETE',
                'up': '↑',
                'down': '↓', 
                'left': '←',
                'right': '→',
                'home': 'HOME',
                'end': 'END',
                'page_up': 'PG UP',
                'page_down': 'PG DN'
            }
            if name in special_keys:
                return special_keys[name]
            elif name.startswith('f') and len(name) <= 3:
                return name.upper()
            elif name.startswith('ctrl'):
                return 'CTRL'
            elif name.startswith('alt'):
                return 'ALT'
            elif name.startswith('shift'):
                return 'SHIFT'
            elif name.startswith('cmd') or name.startswith('super'):
                return 'CMD'
        return None

    def update_hotkey_display(self):
        """Update the hotkey display label."""
        self.hotkey_display.setText(self._current_hotkey)

    def clear_hotkey(self):
        """Clear the current hotkey."""
        self._current_hotkey = ""
        self.hotkey_display.setText("None")
        self.stop_hotkey_recording()

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
    apply_theme(app)
    
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
        duration = settings_window.duration_slider.value() / 10.0
        max_width = settings_window.max_width_input.value()
        max_height = settings_window.max_height_input.value()
        hotkey = settings_window._current_hotkey.lower()

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
        duration = config.get("duration", 5.0)
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
