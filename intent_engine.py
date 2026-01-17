
import re

def analyze_command(text: str):
    text = text.lower()

    # ---------------- INTENT ----------------
    if any(w in text for w in ["sad", "down", "depressed", "not feeling good"]):
        intent = "emotional_support"
        confidence = 0.9

    elif text.startswith("play"):
        intent = "play_music"
        confidence = 0.85

    elif text.startswith("open"):
        intent = "open_app"
        confidence = 0.8

    elif text.startswith(("what", "how", "why", "tell me")):
        intent = "search"
        confidence = 0.75

    else:
        intent = "conversation"
        confidence = 0.6

    # ---------------- EMOTION ----------------
    if re.search(r"\b(sad|upset|angry|tired|lonely)\b", text):
        emotion = "sad"
    elif re.search(r"\b(happy|great|excited)\b", text):
        emotion = "happy"
    else:
        emotion = "neutral"

    return {
        "intent": intent,
        "emotion": emotion,
        "confidence": confidence
    }
intent = "explain_topic"
action = "machine learning"
confidence = 0.92
