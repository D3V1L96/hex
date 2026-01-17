# HEX Voice Assistant

HEX (Heuristic Exploitation Engine) is a custom-built, Python-based voice assistant designed for **desktop automation, conversational interaction, and system-level assistance**. It is engineered to behave like a calm, professional technical partner rather than a generic chatbot.

HEX focuses on **clarity, intent, and real-world usability**, with special attention to speech handling, responsiveness, and modular design.

---

## 🔹 Core Philosophy

* HEX is **not** a chatbot.
* HEX behaves like an **experienced technical assistant**.
* Intent matters more than exact wording.
* Minimal noise, maximum signal.
* Designed for real systems, not demos.

---

## 🔹 Key Features

* 🎙️ **Speech Recognition** (continuous listening)
* 🔊 **Text-to-Speech (TTS)** with natural voice output
* 🧠 **LLM-powered responses** (OpenRouter / LLM API based)
* 🛑 **Speech interruption & stop control**
* 🎧 **Mic & speaker state coordination** (prevents overlap)
* 🖥️ **Windows auto-launch support** via `.bat` file
* 🧩 **Modular Python architecture** (safe to extend)

---

## 🔹 System Architecture Overview

HEX is composed of multiple logical layers:

```
User Voice
   ↓
Speech Recognition Layer
   ↓
Intent Processing
   ↓
LLM Response Engine
   ↓
Text Cleanup & Control Logic
   ↓
Text-to-Speech Output
```

Each layer is isolated to prevent cascading failures and to allow future upgrades.

---

## 🔹 Technology Stack

* **Language:** Python 3.x
* **Speech Recognition:** `speech_recognition`
* **Text-to-Speech:** `edge-tts`
* **Async Handling:** `asyncio`, threading
* **LLM Provider:** OpenRouter-compatible APIs
* **OS Target:** Windows (primary)

---

## 🔹 Project Structure (Example)

```
HEX/
│
├── main.py                  # Entry point
├── speak.py                 # TTS logic
├── listen.py                # Speech recognition logic
├── llm.py                   # LLM request handling
├── control.py               # Stop flags & state control
├── utils.py                 # Text cleaning & helpers
├── launch_hex.bat           # Windows auto-launch file
├── requirements.txt
└── README.md
```

---

## 🔹 Speech Control Logic

HEX is designed to **avoid self-interruption bugs**, which are common in voice assistants.

Key principles:

* When HEX is speaking, mic input is **temporarily paused**.
* A global `is_speaking` flag coordinates TTS and mic access.
* A `stop_flag` allows speech to be interrupted safely.
* No forced blocking calls that freeze the system.

This ensures:

* No echo loops
* No accidental self-triggering
* Clean user experience

---





## 🔹 Configuration

Typical configurable parameters:

* LLM temperature
* Max tokens
* Voice selection
* Microphone index
* Wake word (optional)

These should be kept in a **config section or file**, not hard-coded.

---

## 🔹 Error Handling Strategy

HEX follows a **fail-soft** approach:

* Speech errors do not crash the system
* LLM failures return fallback responses
* Audio stream issues reset cleanly
* All critical blocks are wrapped in `try/except`

This makes HEX stable for long-running sessions.

---

## 🔹 Security Considerations

* API keys are never hard-coded
* Environment variables are recommended
* No automatic system-destructive commands
* No silent background privilege escalation

HEX is built to assist, not exploit.

---

## 🔹 Future Improvements (Planned)

* Wake-word detection (offline)
* Memory persistence
* Task automation modules
* Plugin system
* Mobile companion support

---

## 🔹 Usage Disclaimer

HEX is a **personal assistant framework**.

You are responsible for:

* How it is extended
* What permissions it is given
* How it interacts with your system

Use responsibly.

---

## 🔹 Author

Developed and maintained by **d3v1l**
Cyber Security Engineer | Ethical Hacker

---

## 🔹 Identity Statement

> *HEX does not speak to impress. It speaks to be useful.*
