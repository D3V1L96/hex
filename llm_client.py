import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("bro put your own key not mine")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")

        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, system, user):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "hex Voice Assistant"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528:free",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.5
        }

        response = requests.post(self.url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"].strip()
