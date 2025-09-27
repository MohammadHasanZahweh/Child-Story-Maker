import os
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE = "https://api.openai.com/v1"

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing. Put it in .env")

async def synthesize_tts(text: str, *, voice: str = "verse", fmt: str = "mp3") -> bytes:
    """
    Convert text -> speech using OpenAI TTS (gpt-4o-mini-tts).
    Returns raw audio bytes (MP3 by default).
    """
    # gentle pacing for kids: add a period if missing and normalize whitespace
    t = " ".join(text.strip().split())
    if not t.endswith((".", "!", "?")):
        t += "."
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    body = {"model": "gpt-4o-mini-tts", "voice": voice, "input": t, "format": fmt}
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OPENAI_BASE}/audio/speech", json=body, headers=headers)
        r.raise_for_status()
        return r.content  # binary audio
