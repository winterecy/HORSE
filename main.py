import sys
import random
import threading
import json
import os
import requests
import zipfile
import shutil
import subprocess
import winreg
import pygame
import ctypes
import webbrowser

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox, QMessageBox, QAction,
    QSystemTrayIcon, QMenu, QFormLayout, QSlider, QFrame, QGroupBox, QScrollArea
)
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QObject, pyqtSignal, QSize
from pynput import keyboard as pynput_keyboard
from packaging.version import Version

CONFIG_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "overlay_config.json")
active_overlays = []

VERSION = "1.5.0"
UPDATE_URL = "https://raw.githubusercontent.com/winterecy/HORSE/refs/heads/master/latest.json"

pygame.mixer.init()

def apply_theme(app: QApplication):
    app.setStyle("Fusion")

    palette = QPalette()
    bg = QColor(18, 18, 20)
    panel = QColor(28, 28, 32)
    alt = QColor(22, 22, 26)
    text = QColor(235, 235, 240)
    muted = QColor(156, 163, 175)
    accent = QColor(99, 102, 241)
    # accent_hover = QColor(129, 140, 248)
    warn = QColor(239, 68, 68)
    # success = QColor(34, 197, 94)

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

    app.setStyleSheet("""
        QWidget { 
            background-color: #121214; 
            color: #EBEBF0; 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px; 
        }
        
        QLabel { color: #EBEBF0; }
        
        QGroupBox {
            border: 1px solid #2A2A30;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 18px;
            background-color: #16161A;
            font-weight: 600;
            font-size: 13px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 11px;
        }
        
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #16161A; 
            color: #EBEBF0; 
            border: 1.5px solid #2A2A30; 
            border-radius: 8px; 
            padding: 10px 12px;
            font-size: 13px;
        }
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { 
            border: 1.5px solid #6366F1; 
            background-color: #1A1A1E;
        }
        
        QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
            border-color: #3A3A40;
        }
        
        QPushButton {
            background-color: #1C1C20; 
            color: #EBEBF0; 
            border: 1.5px solid #2A2A30; 
            border-radius: 8px; 
            padding: 10px 16px; 
            font-weight: 600;
            font-size: 13px;
        }
        
        QPushButton:hover { 
            background-color: #222226; 
            border-color: #3A3A40;
        }
        
        QPushButton:pressed { 
            background-color: #18181C; 
            transform: scale(0.98);
        }
        
        QPushButton:default { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #6366F1, stop:1 #4F46E5);
            border: none; 
            color: #FFFFFF;
            font-weight: 700;
        }
        
        QPushButton:default:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #818CF8, stop:1 #6366F1);
        }
        
        QPushButton[warning="true"] {
            background-color: #991B1B;
            border-color: #B91C1C;
            color: #FEE2E2;
        }
        
        QPushButton[warning="true"]:hover {
            background-color: #B91C1C;
        }
        
        QPushButton[success="true"] {
            background-color: #166534;
            border-color: #22C55E;
            color: #D1FAE5;
        }
        
        QMenu { 
            background-color: #1C1C20; 
            color: #EBEBF0; 
            border: 1px solid #2A2A30;
            border-radius: 8px;
            padding: 4px;
        }
        
        QMenu::item { 
            padding: 8px 20px;
            border-radius: 6px;
        }
        
        QMenu::item:selected { 
            background-color: #6366F1; 
        }
        
        QToolTip { 
            background-color: #1C1C20; 
            color: #FFFFFF; 
            border: 1px solid #2A2A30;
            padding: 6px 10px;
            border-radius: 6px;
        }
        
        QSlider::groove:horizontal {
            border: none;
            height: 6px;
            background: #2A2A30;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #6366F1;
            border: none;
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #818CF8;
        }
        
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #6366F1, stop:1 #8B5CF6);
            border-radius: 3px;
        }
        
        QScrollBar:vertical { 
            background: #121214; 
            width: 12px; 
            margin: 0; 
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical { 
            background: #2A2A30; 
            min-height: 30px; 
            border-radius: 6px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover { 
            background: #3A3A40; 
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
            height: 0; 
        }
    """)

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
        QMessageBox.critical(None, "Update Failed", str(e))

def run_updater():
    updater_path = os.path.abspath("updater.exe")
    if not os.path.exists(updater_path):
        QMessageBox.warning(None, "Updater Missing", "Could not find updater.exe")
        return

    ctypes.windll.shell32.ShellExecuteW(None, "runas", updater_path, None, None, 1)
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
        self.setWindowTitle(f"HORSE Overlay Settings")
        self.setMinimumSize(600, 650)
        self.resize(720, 700)

        # main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # header
        header_layout = QHBoxLayout()
        title_label = QLabel("HORSE Overlay")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        version_label = QLabel(f"v{VERSION}")
        version_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(version_label)
        main_layout.addLayout(header_layout)

        # media group
        media_group = QGroupBox("Media Settings")
        media_layout = QVBoxLayout()
        media_layout.setSpacing(12)

        # image
        image_label = QLabel("Overlay Image")
        image_label.setStyleSheet("font-weight: 600; margin-bottom: 4px;")
        media_layout.addWidget(image_label)
        
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select an image file...")
        browse_button = QPushButton("Browse")
        browse_button.setMaximumWidth(100)
        browse_button.clicked.connect(self.browse_image)
        
        img_row = QHBoxLayout()
        img_row.addWidget(self.image_path_input)
        img_row.addWidget(browse_button)
        media_layout.addLayout(img_row)

        # sound
        sound_label = QLabel("Sound Effect (Optional)")
        sound_label.setStyleSheet("font-weight: 600; margin-top: 8px; margin-bottom: 4px;")
        media_layout.addWidget(sound_label)
        
        self.sound_path_input = QLineEdit()
        self.sound_path_input.setPlaceholderText("Select a sound file...")
        browse_sound_button = QPushButton("Browse")
        browse_sound_button.setMaximumWidth(100)
        browse_sound_button.clicked.connect(self.browse_sound)
        
        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_path_input)
        sound_row.addWidget(browse_sound_button)
        media_layout.addLayout(sound_row)

        media_group.setLayout(media_layout)
        main_layout.addWidget(media_group)

        # display settings group
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        display_layout.setSpacing(16)

        # duration
        duration_label = QLabel("Display Duration")
        duration_label.setStyleSheet("font-weight: 600; margin-bottom: 4px;")
        display_layout.addWidget(duration_label)
        
        duration_container = QHBoxLayout()
        self.duration_slider = QSlider(Qt.Horizontal)
        self.duration_slider.setRange(1, 600)
        self.duration_slider.setValue(50)
        self.duration_label = QLabel("5.0s")
        self.duration_label.setStyleSheet("font-weight: 700; color: #6366F1; min-width: 50px;")
        self.duration_slider.valueChanged.connect(self.update_duration_label)
        duration_container.addWidget(self.duration_slider)
        duration_container.addWidget(self.duration_label)
        display_layout.addLayout(duration_container)

        # size controls
        size_row = QHBoxLayout()
        size_row.setSpacing(12)
        
        width_container = QVBoxLayout()
        width_label = QLabel("Max Width")
        width_label.setStyleSheet("font-weight: 600; margin-bottom: 4px;")
        self.max_width_input = QSpinBox()
        self.max_width_input.setRange(10, 2000)
        self.max_width_input.setValue(300)
        self.max_width_input.setSuffix(" px")
        width_container.addWidget(width_label)
        width_container.addWidget(self.max_width_input)
        
        height_container = QVBoxLayout()
        height_label = QLabel("Max Height")
        height_label.setStyleSheet("font-weight: 600; margin-bottom: 4px;")
        self.max_height_input = QSpinBox()
        self.max_height_input.setRange(10, 2000)
        self.max_height_input.setValue(300)
        self.max_height_input.setSuffix(" px")
        height_container.addWidget(height_label)
        height_container.addWidget(self.max_height_input)
        
        size_row.addLayout(width_container)
        size_row.addLayout(height_container)
        display_layout.addLayout(size_row)

        display_group.setLayout(display_layout)
        main_layout.addWidget(display_group)

        # hotkey group
        hotkey_group = QGroupBox("Hotkey Configuration")
        hotkey_layout = QVBoxLayout()
        hotkey_layout.setSpacing(12)

        hotkey_info = QLabel("Press the Record button and then press your desired key")
        hotkey_info.setStyleSheet("color: #9CA3AF; font-size: 12px; margin-bottom: 4px;")
        hotkey_layout.addWidget(hotkey_info)

        hotkey_container = QHBoxLayout()
        hotkey_container.setSpacing(12)
        
        self.hotkey_display = QLabel("H")
        self.hotkey_display.setStyleSheet("""
            QLabel {
                border: 2px solid #6366F1;
                border-radius: 10px;
                padding: 16px 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #1C1C20, stop:1 #16161A);
                color: #6366F1;
                font-weight: 700;
                font-size: 18px;
                min-width: 80px;
            }
        """)
        self.hotkey_display.setAlignment(Qt.AlignCenter)
        
        hotkey_buttons = QVBoxLayout()
        hotkey_buttons.setSpacing(8)
        
        self.record_hotkey_btn = QPushButton("Record Hotkey")
        self.record_hotkey_btn.clicked.connect(self.start_hotkey_recording)
        
        self.clear_hotkey_btn = QPushButton("Clear")
        self.clear_hotkey_btn.clicked.connect(self.clear_hotkey)
        
        hotkey_buttons.addWidget(self.record_hotkey_btn)
        hotkey_buttons.addWidget(self.clear_hotkey_btn)
        
        hotkey_container.addWidget(self.hotkey_display)
        hotkey_container.addLayout(hotkey_buttons)
        hotkey_container.addStretch()
        hotkey_layout.addLayout(hotkey_container)

        hotkey_group.setLayout(hotkey_layout)
        main_layout.addWidget(hotkey_group)

        # preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(12)

        self.image_preview = QLabel()
        self.image_preview.setFixedSize(280, 200)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setStyleSheet("""
            border: 2px dashed #2A2A30; 
            border-radius: 12px; 
            background-color: #0E0E10;
            color: #6B7280;
        """)
        self.image_preview.setText("No image selected")
        preview_layout.addWidget(self.image_preview, 0, Qt.AlignCenter)
        self.image_path_input.textChanged.connect(self.update_image_preview)

        sound_controls = QHBoxLayout()
        self.play_btn = QPushButton("Play Sound")
        self.stop_btn = QPushButton("Stop")
        self.play_btn.clicked.connect(self.play_preview_sound)
        self.stop_btn.clicked.connect(self.stop_preview_sound)
        self.stop_btn.setEnabled(False)
        sound_controls.addWidget(self.play_btn)
        sound_controls.addWidget(self.stop_btn)
        preview_layout.addLayout(sound_controls)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # action buttons
        main_layout.addStretch()
        
        button_container = QHBoxLayout()
        button_container.setSpacing(12)
        
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_config)
        
        load_button = QPushButton("Load Configuration")
        load_button.clicked.connect(self.load_config)
        
        button_container.addWidget(save_button)
        button_container.addWidget(load_button)
        main_layout.addLayout(button_container)

        start_button = QPushButton("Start Overlay")
        start_button.setDefault(True)
        start_button.setMinimumHeight(48)
        start_button.clicked.connect(self.start_overlay)
        main_layout.addWidget(start_button)

        # im so gay
        flag_layout = QHBoxLayout()
        flag_layout.addStretch()
        flag_label = QLabel()
        flag_path = resource_path("lesbian_flag.png")
        flag_pixmap = QPixmap(flag_path)
        if not flag_pixmap.isNull():
            flag_pixmap = flag_pixmap.scaled(80, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            flag_label.setPixmap(flag_pixmap)
            flag_label.setStyleSheet("margin: 8px; opacity: 0.6;")
            flag_layout.addWidget(flag_label)
        main_layout.addLayout(flag_layout)

        scroll.setWidget(main_widget)
        
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(scroll)
        
        self.load_config()
        self.update_image_preview()

        self._preview_channel = None
        self._preview_sound = None
        self._hotkey_recording = False
        self._hotkey_listener = None
        self._current_hotkey = "h"

    def update_duration_label(self, value):
        duration = value / 10.0
        self.duration_label.setText(f"{duration:.1f}s")

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.image_path_input.setText(file_path)
            self.update_image_preview()

    def browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose Sound", "", "Audio Files (*.wav *.mp3 *.ogg)")
        if file_path:
            self.sound_path_input.setText(file_path)

    def update_image_preview(self):
        path = self.image_path_input.text().strip()
        if not path or not os.path.exists(path):
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("No image selected")
            return
        pix = QPixmap(path)
        if pix.isNull():
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("Invalid image file")
            return
        target = self.image_preview.size()
        scaled = pix.scaled(target.width() - 20, target.height() - 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_preview.setText("")
        self.image_preview.setPixmap(scaled)

    def play_preview_sound(self):
        path = self.sound_path_input.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "No Sound File", "Please select a valid sound file first.")
            return
        try:
            self.stop_preview_sound()
            self._preview_sound = pygame.mixer.Sound(path)
            self._preview_channel = self._preview_sound.play()
            self.stop_btn.setEnabled(True)
            self.play_btn.setEnabled(False)
            
            def check_finished():
                if self._preview_channel and not self._preview_channel.get_busy():
                    self.stop_btn.setEnabled(False)
                    self.play_btn.setEnabled(True)
                else:
                    QTimer.singleShot(100, check_finished)
            
            check_finished()
        except Exception as e:
            QMessageBox.warning(self, "Playback Error", f"Failed to play sound: {e}")

    def stop_preview_sound(self):
        try:
            if self._preview_channel is not None:
                self._preview_channel.stop()
            self._preview_channel = None
            self._preview_sound = None
        finally:
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(False)
                self.play_btn.setEnabled(True)

    def start_overlay(self):
        image_path = self.image_path_input.text()
        duration = self.duration_slider.value() / 10.0
        max_width = self.max_width_input.value()
        max_height = self.max_height_input.value()
        hotkey = self._current_hotkey.lower()

        if not image_path:
            QMessageBox.warning(self, "Missing Image", "Please select an image file before starting.")
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
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Config Saved")
        msg.setText("Settings saved successfully.")
        msg.exec_()

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
        self.record_hotkey_btn.setProperty("warning", "true")
        self.record_hotkey_btn.setStyle(self.record_hotkey_btn.style())
        self.hotkey_display.setText("Press a key...")
        self.hotkey_display.setStyleSheet("""
            QLabel {
                border: 2px solid #EF4444;
                border-radius: 10px;
                padding: 16px 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #1C1C20, stop:1 #16161A);
                color: #EF4444;
                font-weight: 700;
                font-size: 18px;
                min-width: 80px;
            }
        """)
        
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
        
        self.record_hotkey_btn.setText("Record Hotkey")
        self.record_hotkey_btn.setProperty("warning", None)
        self.record_hotkey_btn.setStyle(self.record_hotkey_btn.style())
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
        self.hotkey_display.setText(self._current_hotkey if self._current_hotkey else "None")
        self.hotkey_display.setStyleSheet("""
            QLabel {
                border: 2px solid #6366F1;
                border-radius: 10px;
                padding: 16px 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #1C1C20, stop:1 #16161A);
                color: #6366F1;
                font-weight: 700;
                font-size: 18px;
                min-width: 80px;
            }
        """)

    def clear_hotkey(self):
        """Clear the current hotkey."""
        self._current_hotkey = ""
        self.hotkey_display.setText("None")
        self.hotkey_display.setStyleSheet("""
            QLabel {
                border: 2px solid #6B7280;
                border-radius: 10px;
                padding: 16px 24px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #1C1C20, stop:1 #16161A);
                color: #6B7280;
                font-weight: 700;
                font-size: 18px;
                min-width: 80px;
            }
        """)
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
        if "Start Overlay" in btn.text():
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
