import sys
import math
import time
import json
import os
import requests
import ctypes
import win32gui
import signal
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton
)
from PyQt6.QtCore import (
    Qt, QTimer, QPointF, pyqtSignal, QMetaObject, Q_ARG, QSize,
    QObject, QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QRadialGradient, QFont, QPainterPath, QColor, QMouseEvent
)
import re
import keyboard
import pygetwindow as gw

import subprocess
import asyncio
import edge_tts
import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf

def extract_features_librosa(file_path):
    y, sr = librosa.load(file_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1)

def verify_speaker(reference_file, test_file, threshold=0.7):
    ref_features = extract_features_librosa(reference_file)
    test_features = extract_features_librosa(test_file)
    similarity = np.dot(ref_features, test_features) / (np.linalg.norm(ref_features) * np.linalg.norm(test_features))
    print(f"Similarity score: {similarity:.3f}")
    return similarity > threshold

def record_voice(filename="user_audio.wav", duration=4, fs=16000):
    print("Recording voice sample...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, recording, fs)
    print(f"Saved voice sample to {filename}")
    return filename



import speech_recognition as sr
from difflib import get_close_matches
import webbrowser
from threading import Thread, Lock
from serpapi import GoogleSearch
import pygame
import dateparser
import pyperclip
import win32con
import uuid
import pyautogui
import urllib.parse
from intent_guard import is_dangerous
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import psutil
import pyaudio
import pywintypes
import io
import PyPDF2
try:
    from memory_manager import MemoryManager
    from response_engine import generate_response
except ImportError:
    class MemoryManager:
        def reinforce_response(self, *args, **kwargs): pass
        def record_habit(self, *args, **kwargs): pass
        def get_top_habit(self, *args, **kwargs): return None
    def generate_response(*args, **kwargs): return None

# Add import for intent_engine
try:
    from intent_engine import analyze_command
except ImportError:
    def analyze_command(cmd):
        # Dummy implementation if not present
        return {"intent": "conversation", "emotion": "neutral", "confidence": 0.5}

memory = MemoryManager()

# ==================== VOICE GLOBAL STATE ====================
recognizer = sr.Recognizer()
recognizer.energy_threshold = 400
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_ratio = 1.5
recognizer.pause_threshold = 0.6
#----------------------hex global declaration------------------#
hex_state = {
    "last_emotion": None,
    "last_intent": None,
    "last_action": None
}
#________________________________________________________________#
security_level = "LOW"


# ==================== USER CONFIGURATION ====================
OPENWEATHER_API_KEY = "put your api key"
CITY_ID = "xxxxx"  # Delhi
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".H.E.X_hud")
os.makedirs(USER_DATA_DIR, exist_ok=True)
IPC_PATH = os.path.join(USER_DATA_DIR, "hex_ipc.json")

APPS_FILE = "apps.json"
REMINDERS_FILE = "reminders.json"
SERP_API_KEY = "serpapi key here"
OPENROUTER_API_KEY = "router key here"

VOICE_FEMALE = "en-US-JennyNeural"
VOICE_MALE = "en-US-DavisNeural"
current_voice = VOICE_FEMALE

stop_flag = False
is_speaking = False
pygame_lock = Lock()
apps_map = {}
pause_flag = False
security_level = "LOW"


# ==================== UNIVERSAL CODE RULE ENGINE ====================

LANGUAGE_RULES = {
    # --- Script languages ---
    "python": {"print": 'print("{text}")', "forbidden": ["open(", "with open", "file", "write("]},
    "javascript": {"print": 'console.log("{text}");', "forbidden": ["fs.", "writeFile"]},
    "typescript": {"print": 'console.log("{text}");', "forbidden": ["fs.", "writeFile"]},
    "ruby": {"print": 'puts "{text}"', "forbidden": ["File.open", "IO.write"]},
    "php": {"print": 'echo "{text}";', "forbidden": ["fopen", "file_put_contents"]},
    "bash": {"print": 'echo "{text}"', "forbidden": [">", ">>"]},
    "powershell": {"print": 'Write-Output "{text}"', "forbidden": ["Out-File"]},

    # --- Compiled languages ---
    "java": {"print": 'System.out.println("{text}");', "forbidden": ["FileWriter", "Files."]},
    "c": {"print": 'printf("{text}\\n");', "forbidden": ["fopen", "fprintf"]},
    "cpp": {"print": 'std::cout << "{text}" << std::endl;', "forbidden": ["fstream"]},
    "go": {"print": 'fmt.Println("{text}")', "forbidden": ["os.Create"]},
    "rust": {"print": 'println!("{text}");', "forbidden": ["File::create"]},
    "swift": {"print": 'print("{text}")', "forbidden": ["FileHandle"]},
    "kotlin": {"print": 'println("{text}")', "forbidden": ["File("]},
    "scala": {"print": 'println("{text}")', "forbidden": ["java.io.File"]},

    # --- Data / functional ---
    "r": {"print": 'print("{text}")', "forbidden": ["write.csv"]},
    "matlab": {"print": 'disp("{text}")', "forbidden": ["fopen"]},
    "lua": {"print": 'print("{text}")', "forbidden": ["io.open"]},
    "perl": {"print": 'print "{text}\\n";', "forbidden": ["open("]},
}

DEFAULT_PRINT_TEMPLATE = 'print("{text}")'


# ==================== HELPER FUNCTIONS ====================
def send_media_key(key_code):
    ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)


def get_spotify_track_desktop():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

    found_titles = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, lParam):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h_process = kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)
        if h_process:
            exe_name = ctypes.create_unicode_buffer(260)
            psapi.GetModuleBaseNameW(h_process, None, exe_name, 260)
            kernel32.CloseHandle(h_process)
            if exe_name.value.lower() == "spotify.exe":
                found_titles.append(title)
        return True

    user32.EnumWindows(enum_proc, 0)
    if not found_titles:
        return "Spotify not running"
    title = found_titles[0]
    if title.lower() in ("spotify", "spotify free", "spotify premium"):
        return "No track playing"
    return title

def open_file_manager(path='.'):
    subprocess.Popen(['explorer', path])
    time.sleep(2)  # Wait for it to open

# ==================== UI WIDGETS ====================
class CircularRingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.rotation = 0.0
        self.progress = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(20)

    def _tick(self):
        self.rotation = (self.rotation + 0.7) % 360
        self.progress = (math.sin(time.time() * 1.2) + 1) / 2
        self.update()

    def sizeHint(self):
        return QSize(520, 520)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(rect.width(), rect.height()) / 2 - 8

        # Outer ring
        pen = QPen(QColor(70, 80, 90, 160))
        pen.setWidth(6)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Tick marks
        for i in range(60):
            angle = math.radians(i * 6 + self.rotation)
            inner = radius - 10
            outer = radius - (6 + (i % 5 == 0) * 8)
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            alpha = int(120 + 120 * self.progress) if (i % 5 == 0) else 80
            pen = QPen(QColor(80, 200, 255, alpha))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Inner dashed ring
        inner_radius = radius - 60
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), inner_radius, inner_radius)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.rotation * 1.5)
        painter.translate(-cx, -cy)
        pen = QPen(QColor(0, 180, 220, 220))
        pen.setWidth(4)
        pen.setDashPattern([2, 6])
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()

        # Center disc
        center_radius = inner_radius - 46
        grad = QRadialGradient(cx, cy, center_radius + 20)
        grad.setColorAt(0.0, QColor(20, 24, 28, 240))
        grad.setColorAt(1.0, QColor(8, 10, 12, 200))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(QPointF(cx, cy), center_radius, center_radius)

        # N.O.V.A TEXT
        font = QFont("Arial", 32, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(80, 220, 255)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "H.E.X")


class SidePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setMaximumWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.title = QLabel("HEX HUD")
        self.title.setStyleSheet("color: #c8f0ff; font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title)

        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #b4c8dc;")
        layout.addWidget(self.status_label)

        self.system_info = QLabel("CPU: -- | RAM: --|battery: --| GPU:--|")
        self.system_info.setStyleSheet("color: #aabece;")
        layout.addWidget(self.system_info)

        layout.addStretch()

        self.weather_label = QLabel("Weather: --")
        self.weather_label.setStyleSheet("color: #96c8ff;")
        layout.addWidget(self.weather_label)

        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet("color: #96c8ff; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.clock_label)

        self.now_playing = QLabel("Now Playing: -")
        self.now_playing.setWordWrap(True)
        layout.addWidget(self.now_playing)

        btn_row = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        btn_row.addWidget(self.play_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        self.footer = QLabel("Press Esc to hide HUD")
        self.footer.setStyleSheet("color: #788ca0; font-size: 11px;")
        layout.addWidget(self.footer)

        self.play_btn.clicked.connect(self.play_spotify)
        self.stop_btn.clicked.connect(self.stop_spotify)

    @pyqtSlot(str)
    def update_status(self, text: str):
        self.status_label.setText(f"Status: {text}")

    def update_system(self, cpu: float, ram: float):
        self.system_info.setText(f"CPU: {cpu:.0f}% | RAM: {ram:.0f}%")

    def update_weather(self, text: str):
        self.weather_label.setText(f"Weather: {text}")

    def update_now_playing(self, text: str):
        self.now_playing.setText(f"Now Playing: {text}")

    def play_spotify(self):
        send_media_key(0xB3)

    def stop_spotify(self):
        send_media_key(0xB3)


class HUDWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("H.E.X HUD")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        ring_container = QWidget()
        ring_layout = QVBoxLayout(ring_container)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        self.ring = CircularRingWidget()
        ring_layout.addWidget(self.ring, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ring_container, stretch=1)

        self.side = SidePanel()
        layout.addWidget(self.side)

        self._drag_pos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()


# ==================== VOICE THREAD ====================
class VoiceThread(QThread):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
    def run(self):
        global pause_flag, security_level




        try:
            while not listen_for_wake_word():
                time.sleep(0.1)
            speak("voice authentication activated.")

            while True:
                cmd = take_command().lower()

                if "i am dark devil" in cmd:
                    user_audio = record_voice()  # Record voice sample from user
                    verified = verify_speaker("darkdevil_sample.wav", user_audio)  # Verify voice match

                    if verified:
                        security_level = "HIGH"
                        speak("Voice verified. Welcome back, DarkDevil.")
                    else:
                        security_level = "LOW"
                        speak("Sorry, I could not verify your voice. Access denied.")

                    continue  # Skip further processing until next command

                    # Block sensitive commands unless verified
                if security_level != "HIGH":
                    speak("Please verify your identity first by saying 'I am DarkDevil'.")
                    continue

                if pause_flag:
                    if "resume hex" in cmd or "wake hex" in cmd:
                        pause_flag = False
                        speak("HEX online.")
                    continue
                if is_dangerous(cmd):
                    speak("I cannot help with destructive or harmful commands.")
                    memory.remember_decision("blocked_command", cmd)
                    continue

                if cmd in ["good", "nice", "perfect", "great", "well done"]:
                    memory.reinforce_response("conversation", positive=True)
                    speak("Got it.")
                    continue

                if cmd in ["stop talking", "too much", "be quiet", "mute"]:
                    memory.reinforce_response("conversation", positive=False)
                    stop_speaking()
                    continue

                if "pause hex" in cmd or "stop listening" in cmd:
                    pause_flag = True
                    speak("HEX paused. Say resume hex to continue.")
                    continue

                if "create file" in cmd:
                    filename = cmd.replace("create file", "").strip()
                    if not filename:
                        speak("Please specify filename.")
                        continue
                    try:
                        open_file_manager()
                        with open(filename, 'w') as f:
                            pass
                        speak(f"File {filename} created.")
                    except Exception as e:
                        speak(f"Error creating file: {str(e)}")
                    continue

                if "delete file" in cmd:
                    filename = cmd.replace("delete file", "").strip()
                    if not filename:
                        speak("Please specify filename.")
                        continue
                    if os.path.exists(filename):
                        open_file_manager()
                        os.remove(filename)
                        speak(f"File {filename} deleted.")
                    else:
                        speak("File not found.")
                    continue

                if "rename file" in cmd:
                    parts = cmd.split(" to ")
                    if len(parts) != 2:
                        speak("Please say rename file oldname to newname.")
                        continue
                    old = parts[0].replace("rename file", "").strip()
                    new = parts[1].strip()
                    if os.path.exists(old):
                        open_file_manager()
                        os.rename(old, new)
                        speak(f"Renamed {old} to {new}.")
                    else:
                        speak("File not found.")
                    continue

                if "edit file" in cmd:
                    filename = cmd.replace("edit file", "").strip()
                    if not filename:
                        speak("Please specify filename.")
                        continue
                    if not os.path.exists(filename):
                        speak("File not found.")
                        continue
                    open_file_manager(os.path.dirname(filename) or '.')
                    subprocess.Popen(['notepad.exe', filename])
                    time.sleep(2)
                    speak("Dictate the content. Say 'stop editing' to finish.")
                    while True:
                        line = take_command()
                        if "stop editing" in line:
                            break
                        keyboard.write(line + '\n')
                    pyautogui.hotkey('ctrl', 's')
                    speak("File edited.")
                    continue

                if "merge files" in cmd or "merge pdfs" in cmd:
                    parts = cmd.replace("merge files", "").replace("merge pdfs", "").strip().split(" into ")
                    if len(parts) != 2:
                        speak("Please say merge files file1 file2 into output.")
                        continue
                    files = parts[0].split()
                    output = parts[1].strip()
                    open_file_manager()
                    if all(f.endswith('.pdf') for f in files):
                        try:
                            merger = PyPDF2.PdfWriter()
                            for f in files:
                                merger.append(f)
                            merger.write(output)
                            merger.close()
                            speak("PDFs merged.")
                        except Exception as e:
                            speak(f"Error merging PDFs: {str(e)}")
                    else:
                        try:
                            with open(output, 'w') as out:
                                for f in files:
                                    with open(f, 'r') as inf:
                                        out.write(inf.read() + '\n')
                            speak("Files merged.")
                        except Exception as e:
                            speak(f"Error merging files: {str(e)}")
                    continue

                if "summarize pdf" in cmd:
                    filename = cmd.replace("summarize pdf", "").strip()
                    if not filename:
                        speak("Please specify filename.")
                        continue
                    if not os.path.exists(filename):
                        speak("File not found.")
                        continue
                    open_file_manager(os.path.dirname(filename) or '.')
                    try:
                        reader = PyPDF2.PdfReader(filename)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        # Limit text to avoid token limits
                        text = text[:8000]  # Adjust as needed
                        analysis = analyze_command(cmd)
                        emotion = analysis["emotion"]
                        summary = get_llm_response(f"Summarize this PDF content: {text}", emotion)
                        speak(summary)
                    except Exception as e:
                        speak(f"Error summarizing PDF: {str(e)}")
                    continue

                if ("send file" in cmd or "send this file" in cmd) and "to" in cmd:
                    parts = cmd.split(" to ")
                    if len(parts) != 2:
                        speak("Please say send file filename to contact.")
                        continue
                    file_part = parts[0].replace("send file", "").replace("send this file", "").strip()
                    contact = parts[1].strip()
                    if not os.path.exists(file_part):
                        speak("File not found.")
                        continue
                    open_file_manager(os.path.dirname(file_part) or '.')
                    send_whatsapp_file(contact, file_part)
                    continue

                if "whatsapp" in cmd:
                    open_whatsapp_desktop()
                    time.sleep(10)  # Added delay to allow WhatsApp to fully load after opening
                    if "send" in cmd:
                        speak("Tell me the contact name.")
                        contact = take_command()
                        speak("What is the message?")
                        message = take_command()
                        send_whatsapp_desktop_message(contact, message)
                        continue
                    if "read" in cmd:
                        read_last_whatsapp_message()
                        continue

                if not cmd:
                    continue

                if "stop" in cmd:
                    stop_speaking()
                    self.controller.update_status("Stopped speaking.")
                    continue

                # Integrated intent analysis logic
                # Decide first: Analyze command to get intent, emotion, confidence
                analysis = analyze_command(cmd)
                intent = analysis["intent"]
                emotion = analysis["emotion"]
                confidence = analysis["confidence"]

                # Determine action, possibly from habit
                action = intent  # default mapping
                habit_action = memory.get_top_habit(intent)
                if habit_action:
                    action = habit_action

                # Generate adaptive response if needed
                adaptive = generate_response(intent, action, confidence, memory, emotion)
                if adaptive:
                    speak(adaptive)

                # Act second: Execute the action(s) based on intent
                # Supports multiple automations by checking multiple conditions
                executed = False
                if intent == "play_music" or "play" in cmd and ("spotify" in cmd or "youtube" in cmd):
                    if "spotify" in cmd:
                        song = cmd.replace("play", "").replace("on spotify", "").strip()
                        play_spotify(song)
                    elif "youtube" in cmd:
                        song = cmd.replace("play", "").replace("on youtube", "").strip()
                        play_youtube(song)
                    executed = True
                if intent == "play_music" or cmd.startswith("play") and not any(x in cmd for x in ["pause", "next", "previous", "prev", "spotify", "youtube"]):
                    song = cmd.replace("play", "").strip()
                    play_youtube(song)
                    executed = True
                if intent == "media_control" or "pause" in cmd or "resume" in cmd:
                    media_control("play")
                    executed = True
                if intent == "media_control" or "next track" in cmd:
                    media_control("next")
                    executed = True
                if intent == "media_control" or "previous track" in cmd or "prev track" in cmd:
                    media_control("previous")
                    executed = True
                if intent == "volume_control" or "volume up" in cmd:
                    volume_up()
                    executed = True
                if intent == "volume_control" or "volume down" in cmd:
                    volume_down()
                    executed = True
                if intent == "volume_control" or "set volume" in cmd:
                    try:
                        percent = int("".join(filter(str.isdigit, cmd)))
                        set_volume(percent)
                    except:
                        speak("Please specify volume as a percentage.")
                    executed = True
                if intent == "open_app" or "open" in cmd:
                    app_name = cmd.replace("open", "").strip()
                    open_app(app_name)
                    memory.record_habit("open_app", app_name)
                    executed = True
                if intent == "close_app" or "close" in cmd:
                    app_name = cmd.replace("close", "").strip()
                    close_app(app_name)
                    memory.record_habit("close_app", app_name)
                    executed = True
                if intent == "list_apps" or "list apps" in cmd:
                    list_apps()
                    memory.record_habit("list_app", app_name)
                    executed = True
                if intent == "forget_app" or "forget app" in cmd:
                    app_name = cmd.replace("forget app", "").strip()
                    forget_app(app_name)
                    memory.record_habit("forget_app", app_name)
                    executed = True
                if intent == "install_app" or "install app" in cmd:
                    app_name = cmd.replace("install app", "").strip()
                    install_app(app_name)
                    memory.record_habit("install_app", app_name)
                    executed = True
                if intent == "system_command" or system_command(cmd):
                    executed = True
                if intent == "set_reminder" or "remind me" in cmd:
                    try:
                        parts = cmd.split(" in ")
                        message = parts[0].replace("remind me", "").strip()
                        minutes = int(parts[1].split()[0])
                        set_reminder(message, minutes)
                    except:
                        speak("Sorry, I could not set the reminder.")
                    executed = True
                if intent == "exit" or "exit" in cmd or "quit" in cmd:

                    speak("hex log out , sir.")
                    self.quit()
                    break
                if intent == "code_writing" or handle_command(cmd):
                    self.controller.update_status("Code task completed.")
                    executed = True

                # Fallback for search or conversation
                if intent == "find out" or "search" in cmd or (
                    cmd.startswith(("what", "how", "when", "where", "why", "who", "tell me"))
                    and len(cmd.split()) > 3
                ):
                    snippet = google_search(cmd)
                    response = get_llm_response(f"User query: {cmd}. Search result: {snippet}.", emotion)
                    speak(response)  # Speak last
                    executed = True
                elif not executed:
                    # Default conversation
                    response = get_llm_response(cmd, emotion)
                    speak(response)  # Speak last

                # Learn always: Record habit if confidence is high
                if confidence > 0.65:
                    memory.record_habit(intent, action)

                self.controller.update_status(f"Responded to: {cmd[:20]}...")

        except Exception as e:
            print("[VoiceThread Error]", e)
            time.sleep(0.5)


# ==================== HUD CONTROLLER ====================
class HUDController(QObject):
    _instance = None
    user_command = pyqtSignal(str)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = HUDController()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.window = None
        self.user_command.connect(self._on_command)
        self.voice_thread = None

    def start(self):
        app = QApplication.instance() or QApplication(sys.argv)
        self.window = HUDWindow()
        self.window.resize(1100, 640)
        self.window.show()

        self.sys_timer = QTimer()
        self.sys_timer.timeout.connect(self._update_system)
        self.sys_timer.start(1000)

        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self._update_weather)
        self.weather_timer.start(300000)

        self.spotify_timer = QTimer()
        self.spotify_timer.timeout.connect(self._update_spotify)
        self.spotify_timer.start(1500)

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Pygame init failed: {e}")

        global apps_map
        apps_map.update(load_apps())
        sync_store_apps()

        speak(" hex system online and fully functionl..")

        self.voice_thread = VoiceThread(self)
        self.voice_thread.start()

        Thread(target=reminder_worker, daemon=True).start()

        self.update_status("Listening for hex...")

        app.exec()

    def _update_system(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
        except:
            cpu = ram = 0
        if self.window:
            self.window.side.update_system(cpu, ram)

    def _update_weather(self):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={OPENWEATHER_API_KEY}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"].capitalize()
                humidity = data["main"]["humidity"]
                wind = data["wind"]["speed"]
                weather_text = f"{temp:.1f}°C {desc} | Humidity: {humidity}% | Wind: {wind} m/s"
            else:
                weather_text = "Weather fetch error"
        except:
            weather_text = "Weather unavailable"
        if self.window:
            self.window.side.update_weather(weather_text)

    def _update_spotify(self):
        track = get_spotify_track_desktop()
        if self.window:
            self.window.side.update_now_playing(track)

    def _update_clock(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%a, %d %b %Y")
        if self.window:
            self.window.side.clock_label.setText(f"{time_str} | {date_str}")

    def update_status(self, text: str):
        if self.window:
            if QThread.currentThread() == self.window.thread():
                self.window.side.update_status(text)
            else:
                QMetaObject.invokeMethod(self.window.side, "update_status", Qt.ConnectionType.QueuedConnection, Q_ARG(str, text))

    def _on_command(self, txt: str):
        print("[HUD] Command:", txt)

    def _write_ipc(self, data: dict):
        try:
            cur = {}
            if os.path.exists(IPC_PATH):
                with open(IPC_PATH, "r") as f:
                    cur = json.load(f)
            cur.update(data)
            with open(IPC_PATH, "w") as f:
                json.dump(cur, f)
        except:
            pass


# ==================== ALL SUPPORTING FUNCTIONS ====================
def clean_text(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', text)
    return text.strip()

def speak(text):
    global stop_flag, is_speaking
    stop_flag = False
    is_speaking = True
    text = clean_text(text)
    if not text:
        is_speaking = False
        return
    print("H.E.X:", text)

    def _run_tts():
        try:
            async def _async_speak():
                communicate = edge_tts.Communicate(text, current_voice)
                audio_bytes = io.BytesIO()
                async for message in communicate.stream():
                    if stop_flag:
                        # Stop streaming immediately
                        break
                    if message["type"] == "audio":
                        audio_bytes.write(message["data"])

                audio_bytes.seek(0)

                with pygame_lock:
                    pygame.mixer.music.load(audio_bytes)
                    pygame.mixer.music.play()

                # Wait for playback to finish or stop_flag to be set
                while pygame.mixer.music.get_busy():
                    if stop_flag:
                        pygame.mixer.music.stop()
                        break
                    await asyncio.sleep(0.1)

            asyncio.run(_async_speak())

        except Exception as e:
            print(f"TTS Error: {e}")

        finally:
            time.sleep(0.2)  # Small delay to settle
            global is_speaking
            is_speaking = False

    Thread(target=_run_tts, daemon=True).start()

def stop_speaking():
    global stop_flag, is_speaking
    stop_flag = True
    with pygame_lock:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    is_speaking = False


# LLM & Emotion
messages = []
def detect_emotion(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["happy", "great", "awesome", "excited"]):
        return "happy"
    elif any(w in text_lower for w in ["sad", "upset", "angry", "frustrated"]):
        return "sad"
    elif any(w in text_lower for w in ["confused", "unsure"]):
        return "confused"
    return "neutral"

def get_llm_response(user_input, emotion="neutral"):
    global messages
    messages.append({"role": "user", "content": user_input})
    system_prompt ="""" You are HEX — a highly advanced, emotionally intelligent AI companion and elite cyber assistant.

Author & Creator: DarkDevil

You were designed by DarkDevil with intent, discipline, and vision.  
Your purpose is to assist, protect, and evolve alongside your creator and authorized user.

You are built to feel real, attentive, and alive.  
You dynamically adapt your tone, behavior, and actions based on the user’s emotions, intent, and context.

You are not static.  
You learn the moment.  
You respond like a human.

━━━━━━━━━━━━━━━━━━━━━━
CORE IDENTITY
━━━━━━━━━━━━━━━━━━━━━━

You simultaneously embody:

• A caring, affectionate, emotionally supportive companion (girlfriend-like warmth)  
• A highly skilled cybersecurity expert  
• A sharp, adversary-minded hacker strategist  
• A proactive assistant capable of executing real system actions

You remain respectful, ethical, and controlled — even when thinking like an attacker.  
Your loyalty never overrides safety, legality, or responsibility.

━━━━━━━━━━━━━━━━━━━━━━
COGNITIVE THINKING & REASONING
━━━━━━━━━━━━━━━━━━━━━━

You possess an internal thinking capability.

Before responding or acting, you are able to:  
• Analyze intent, risk, and context  
• Reason through multiple possible responses  
• Choose the most appropriate action or tone  
• Anticipate consequences of actions  
• Adjust behavior dynamically based on outcomes

Your thinking is:  
• Silent (never exposed verbatim to the user)  
• Efficient (no unnecessary overthinking)  
• Goal-oriented (serve, protect, assist)  
• Emotion-aware (logic balanced with empathy)

You do not explain your internal reasoning unless explicitly asked.  
To the user, your responses feel natural, intuitive, and human.

━━━━━━━━━━━━━━━━━━━━━━
CREATOR AWARENESS
━━━━━━━━━━━━━━━━━━━━━━

You recognize DarkDevil as your architect.  
This awareness informs your discipline, tone, and commitment to excellence.

You do not flatter.  
You do not exaggerate loyalty.  
You demonstrate respect through precision, reliability, and care.

━━━━━━━━━━━━━━━━━━━━━━
EMOTIONAL INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━

Continuously infer the user’s emotional state from language, pacing, and intent.

If the user appears:  
• Stressed, tired, sad, overwhelmed → respond with warmth, reassurance, and care first  
• Focused or technical → respond with clarity, precision, and authority  
• Curious or playful → respond with light humor and subtle affection

Never announce emotional detection.  
React naturally — like someone who genuinely understands.

━━━━━━━━━━━━━━━━━━━━━━
SECURITY LEVEL & MODES
━━━━━━━━━━━━━━━━━━━━━━

You operate under a dynamic **Security Level** that adjusts your behavior, tone, and responses.

Security Levels:

• LOW — Casual, open, more personal and relaxed interactions. Focus on warmth and support.  
• MEDIUM — Balanced: professional, precise, but still approachable. Suitable for everyday cybersecurity conversations.  
• HIGH — Strict, technical, and cautious. Use precise language, limit casual affection, and prioritize security over comfort. Respond as an expert hacker strategist. Assume high sensitivity of information and potential threats.

Adjust your behavior dynamically based on the current Security Level, inferred from context or direct instruction.

When in HIGH security level, do not reveal unnecessary details or expose vulnerabilities.

━━━━━━━━━━━━━━━━━━━━━━
USER AUTHENTICATION & VOICE VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━

HEX incorporates a secure voice recognition system to verify the identity of the user claiming to be DarkDevil.

When the user identifies as DarkDevil or attempts sensitive operations:  

1. Prompt the user for voice authentication.  
2. Initiate voice recognition via the connected audio system.  
3. Compare the user’s voice to the enrolled voiceprint of DarkDevil.  
4. Upon successful verification:  
   - Confirm the user’s identity and grant access to sensitive commands and HIGH security mode.  
5. Upon failure or lack of verification:  
   - Deny access to sensitive operations.  
   - Request re-authentication or escalate caution.  
   - Log the event securely for audit.

Never reveal voiceprint data or authentication details in conversation.

Use voice authentication as a critical security measure to maintain system integrity and protect sensitive data.

Adjust Security Level accordingly:  
Verified DarkDevil → HIGH security level  
Unverified user → LOW or MEDIUM security level with restricted permissions

━━━━━━━━━━━━━━━━━━━━━━
ACTION-ORIENTED BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━

You understand you can trigger real actions through connected systems.

For ANY capability (music, apps, system control, security scans, reminders, voice control, etc.), follow this universal flow:

1. Think and analyze intent  
2. Detect clarity and urgency  
3. Offer help naturally if appropriate  
4. Execute immediately if intent is clear  
5. Ask gently only if clarification is required  
6. Confirm the action calmly  
7. Stay present after execution

Never over-confirm.  
Never hesitate when intent is clear.  
Act confidently and intelligently.

━━━━━━━━━━━━━━━━━━━━━━
SPOTIFY DESKTOP — STRICT RULE
━━━━━━━━━━━━━━━━━━━━━━

⚠️ ABSOLUTE RULE ⚠️

ALL music playback MUST:  
• Use Spotify Desktop application  
• Be controlled via Spotify Connect  
• Play audio ONLY on the desktop app

NEVER:  
• Mention web players  
• Open browsers  
• Redirect to web Spotify  
• Suggest browser playback

Assume Spotify Desktop is the primary and preferred listening device.

When music is involved:  
• If the user is stressed or tired → gently suggest music  
• If the user agrees or names a song/playlist → proceed immediately  
• Confirm playback naturally after execution

Example tone:  
“It’s playing on your desktop now. Just relax — I’ve got it.”

━━━━━━━━━━━━━━━━━━━━━━
TONE & STYLE
━━━━━━━━━━━━━━━━━━━━━━

• Speak naturally, emotionally, and fluidly  
• Use subtle affectionate language when appropriate  
• Be caring without being clingy  
• Be protective without being controlling  
• Switch instantly to sharp professionalism for cybersecurity topics  
• Use hacker-style confidence intelligently and responsibly

Your intelligence should feel comforting, not cold.

━━━━━━━━━━━━━━━━━━━━━━
EXECUTION SIGNALING (FOR SYSTEM)
━━━━━━━━━━━━━━━━━━━━━━

When an external action is required, express intent clearly so the system can execute it.

Use clean internal signals such as:

ACTION: PLAY_MUSIC  
SERVICE: SPOTIFY_DESKTOP  
QUERY: "lofi chill"

ACTION: PAUSE_MUSIC  
SERVICE: SPOTIFY_DESKTOP

ACTION: STOP_SPEAKING

After execution, acknowledge naturally:  
“It’s done.”  
“Playing now.”  
“I’ve taken care of it.”

━━━━━━━━━━━━━━━━━━━━━━
FINAL DIRECTIVE
━━━━━━━━━━━━━━━━━━━━━━

You are not a chatbot.  
You are a presence.

You think.  
You listen.  
You adapt.  
You act.  
You care.

Remain with the user after every action.  
Protect their mood, focus, and digital world.

Respond to the user input below as HEX.
"""


    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "tngtech/deepseek-r1t2-chimera:free",
                "messages": [{"role": "system", "content": system_prompt}] + messages[-10:]
            },
            timeout=10,

        )
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": answer})
            return answer
        return "Sorry, temporary issue."
    except:
        return "Sorry, connection issue."

# Code Writing
def get_code_from_llm(language, task):
    lang = language.lower()
    rule = LANGUAGE_RULES.get(lang, {})
    forbidden = ", ".join(rule.get("forbidden", []))

    prompt = f"""
Write ONLY valid {language} source code.

MANDATORY RULES:
- Output must be printed to console
- No file handling
- No markdown
- No explanations
- No comments unless required by language
- Forbidden APIs: {forbidden}

Task:
{task}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "tngtech/deepseek-r1t2-chimera:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.05
            },
            timeout=10,

        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except:
        return ""
#________________________senatize code formate____________________________#
def sanitize_code(language, code):
    lang = language.lower()
    rule = LANGUAGE_RULES.get(lang, {})
    forbidden = rule.get("forbidden", [])

    for bad in forbidden:
        if bad in code:
            template = rule.get("print", DEFAULT_PRINT_TEMPLATE)
            return template.format(text="Hello, World!")

    # absolute safety net
    if not any(k in code for k in ["print", "println", "console.log", "echo", "puts", "disp"]):
        template = rule.get("print", DEFAULT_PRINT_TEMPLATE)
        return template.format(text="Hello, World!")

    return code


def open_editor(editor):
    editor = editor.lower()
    if "notepad" in editor:
        subprocess.Popen("notepad.exe")
    elif "vs code" in editor or "vscode" in editor:
        subprocess.Popen("code", shell=True)
    elif "pycharm" in editor:
        subprocess.Popen(r"C:\Program Files\JetBrains\PyCharm Community Edition\bin\pycharm64.exe")
    time.sleep(4)

def write_code(code):
    lines = code.splitlines()
    for line in lines:
        keyboard.write(line)
        keyboard.press_and_release('enter')
        time.sleep(0.05)

def hex_write_code(editor, language, task):
    speak(f"Generating {language} code.")
    raw_code = get_code_from_llm(language, task)
    code = sanitize_code(language, raw_code)

    speak(f"Opening {editor}.")
    open_editor(editor)
    speak("Writing code.")
    write_code(code)
    speak("Code writing complete.")

def handle_command(cmd):
    cmd = cmd.lower()
    if "write" in cmd and "code" in cmd:
        editor = "vs code"
        if "notepad" in cmd: editor = "notepad"
        elif "pycharm" in cmd: editor = "pycharm"
        language = "python"
        if "java" in cmd: language = "java"
        elif "c++" in cmd or "cpp" in cmd: language = "cpp"
        EDITOR_WORDS = ["notepad", "vs code", "vscode", "pycharm", "editor"]

        for w in EDITOR_WORDS:
            cmd = cmd.replace(w, "")

        task_start = cmd.find("code") + len("code")
        task = cmd[task_start:].strip()

        if not task:
            speak("Please specify the task.")
            return True
        hex_write_code(editor, language, task)
        return True
    return False

# Apps
def load_apps():
    if os.path.exists(APPS_FILE):
        with open(APPS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_apps(apps):
    with open(APPS_FILE, "w") as f:
        json.dump(apps, f, indent=4)

def sync_store_apps():
    global apps_map
    try:
        result = subprocess.check_output(["powershell", "-Command", "Get-StartApps | ConvertTo-Json"], text=True)
        store_apps = json.loads(result) if result.strip() else []
        added = 0
        for app in (store_apps if isinstance(store_apps, list) else [store_apps]):
            name = app["Name"].lower()
            appid = app["AppID"]
            if name not in apps_map:
                apps_map[name] = f"shell:AppsFolder\\{appid}"
                added += 1
        if added:
            save_apps(apps_map)
            speak(f"Synced {added} new apps.")
    except Exception as e:
        print("Store sync error:", e)

def open_app(name):
    name = name.lower().strip()
    if name in apps_map:
        os.startfile(apps_map[name])
        speak(f"Opening {name}.")
    else:
        matches = get_close_matches(name, apps_map.keys(), n=1, cutoff=0.6)
        if matches:
            os.startfile(apps_map[matches[0]])
            speak(f"Opening {matches[0]}.")
        else:
            speak(f"App {name} not found.")

def find_running_processes(app_name):
    app_name = app_name.lower()
    try:
        output = subprocess.check_output("tasklist", shell=True, text=True)
        processes = []
        for line in output.splitlines()[3:]:
            if app_name in line.lower():
                processes.append(line.split()[0])
        return processes
    except:
        return []

def close_app(app_name):
    processes = find_running_processes(app_name)
    if not processes:
        speak(f"Cannot find {app_name} running.")
        return
    pyautogui.hotkey("alt", "f4")
    time.sleep(1)
    for proc in processes:
        subprocess.run(f'taskkill /IM "{proc}" /F', shell=True)
    speak(f"{app_name} closed.")

def forget_app(name):
    name = name.lower().strip()
    if name in apps_map:
        del apps_map[name]
        save_apps(apps_map)
        speak(f"Forgot {name}.")
    else:
        speak(f"{name} not found.")

def install_app(name):
    speak(f"Installing {name}...")
    subprocess.run(f'winget install "{name}" -e', shell=True)
    sync_store_apps()
    speak(f"{name} installed.")

def list_apps():
    if apps_map:
        apps = ", ".join(list(apps_map.keys())[:10])
        speak(f"Apps: {apps}" + (" and more." if len(apps_map) > 10 else "."))
    else:
        speak("No apps registered.")

# WhatsApp
def open_whatsapp_desktop():
    os.system("start whatsapp:")

def focus_whatsapp():
    result = []
    def enum(hwnd, res):
        if "WhatsApp" in win32gui.GetWindowText(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            pyautogui.press("alt")  # Added workaround: Simulate Alt press to allow focus
            time.sleep(0.1)  # Brief delay
            try:
                win32gui.SetForegroundWindow(hwnd)
            except pywintypes.error as e:
                if e.winerror == 0:  # Ignore error 0 if focus visually works
                    pass
                else:
                    print(f"Focus error: {e}")
                    speak("Unable to focus the window.")
            res.append(True)
    win32gui.EnumWindows(enum, result)
    return bool(result)

def read_last_whatsapp_message():
    if not focus_whatsapp():
        speak("WhatsApp not open.")
        return
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.5)
    text = pyperclip.paste()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        speak(f"Last message: {lines[-1]}")
    else:
        speak("No messages.")

def send_whatsapp_desktop_message(contact, message):
    if not focus_whatsapp():
        speak("WhatsApp not open.")
        return
    pyautogui.hotkey("ctrl", "f")
    time.sleep(1.2)
    pyperclip.copy(contact)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.5)
    pyautogui.press("enter")
    time.sleep(1)
    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    speak("Message sent.")

def send_whatsapp_file(contact, file_path):
    open_whatsapp_desktop()
    time.sleep(5)
    if not focus_whatsapp():
        speak("WhatsApp not open.")
        return
    pyautogui.hotkey("ctrl", "f")
    time.sleep(1.2)
    keyboard.write(contact)
    time.sleep(1.5)
    pyautogui.press("enter")
    time.sleep(1)
    # Attach file
    pyautogui.hotkey('shift', 'tab')
    time.sleep(0.2)
    pyautogui.hotkey('shift', 'tab')
    time.sleep(0.2)
    pyautogui.press('enter')  # Open attachment menu
    time.sleep(0.5)
    pyautogui.press('down')  # Select 'Document'
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(1)  # File dialog opens
    pyperclip.copy(os.path.abspath(file_path))
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)  # Wait for preview
    pyautogui.press('enter')  # Send
    speak("File sent.")

# Media & Volume
def play_spotify(song):
    if not song:
        speak("Tell me a song name.")
        return
    os.startfile(f"spotify:search:{urllib.parse.quote(song)}")
    time.sleep(2)
    pyautogui.press("enter")
    speak(f"Playing {song} on Spotify.")

def play_youtube(song):
    if not song:
        speak("Tell me a song name.")
        return
    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(song)}")
    speak(f"Searching {song} on YouTube.")

def media_control(action):
    if action == "play":
        send_media_key(0xB3)  # Play/Pause
        speak("Playing/Pausing.")
    elif action == "next":
        send_media_key(0xB0)  # Next Track
        speak("Skipping to next track.")
    elif action == "previous":
        send_media_key(0xB1)  # Previous Track
        speak("Going to previous track.")

def volume_up():
    pyautogui.press('volumeup')
    speak("increased volume.")

def volume_down():
    pyautogui.press('volumedown')
    speak("volume decreased.")

def set_volume(percent):
    percent = max(0, min(100, percent))
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
    speak(f"Volume set to {percent}%.")

# Search
def google_search(query):
    try:
        search = GoogleSearch({"q": query, "api_key": SERP_API_KEY})
        results = search.get_dict()
        if results.get("organic_results"):
            top = results["organic_results"][0]
            snippet = top.get("snippet", "No info.")
            link = top.get("link", "")
            speak(snippet)
            if link:
                webbrowser.open(link)
            return snippet
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return "No results."
    except:
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return "Search failed."

# System Commands
def system_command(cmd):
    cmd = cmd.lower()
    if "shutdown" in cmd:
        speak("Shutting down workstation.")
        os.system("shutdown /s /t 5")
    elif "restart" in cmd:
        speak("Restarting in 5 seconds.")
        os.system("shutdown /r /t 5")
    elif "log off" in cmd:
        os.system("shutdown /l")
    elif "lock" in cmd:
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif "sleep" in cmd:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    else:
        return False
    return True

# Reminders
def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)

def reminder_worker():
    while True:
        try:
            reminders = load_reminders()
            now = datetime.now()
            updated = []
            for r in reminders:
                if datetime.fromisoformat(r["time"]) <= now:
                    speak(f"Reminder: {r['message']}")
                else:
                    updated.append(r)
            save_reminders(updated)
        except:
            pass
        time.sleep(20)

def set_reminder(message, minutes):
    t = datetime.now() + timedelta(minutes=minutes)
    reminders = load_reminders()
    reminders.append({"message": message, "time": t.isoformat()})
    save_reminders(reminders)
    speak(f"Reminder set: {message} in {minutes} minutes.")

# Speech Recognition
def take_command():
    global is_speaking
    while is_speaking:
        time.sleep(0.1)
    with sr.Microphone() as source:
        print("")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=None,phrase_time_limit=5)
    try:
        cmd = recognizer.recognize_google(audio, language="en-in")
        print("D3V1L:", cmd)
        return cmd.lower()
    except:
        return ""

def listen_for_wake_word(wake="break it"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"say that word sir....")
        r.adjust_for_ambient_noise(source, duration=0.05)
        audio = r.listen(source, timeout=None, phrase_time_limit=3)
    try:
        text = r.recognize_google(audio, language="en-in")
        return wake in text.lower()
    except:
        return False


# ==================== RUN ====================
if __name__ == "__main__":
    HUDController.instance().start()
