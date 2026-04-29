import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

config = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "N8N_WEBHOOK_URL": os.getenv("N8N_WEBHOOK_URL"),
    "VIDEO_OUTPUT": os.path.join(os.getcwd(), "assets", "temp"),
    "TTS_VOICE": "en-US-Wavenet-D",
    "VIDEO_RESOLUTION": (1920, 1080),
    "FPS": 24,
    "PEXELS_API_KEY": os.getenv("PEXELS_API_KEY"),
    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
    "ELEVENLABS_VOICE_ID": os.getenv("ELEVENLABS_VOICE_ID"),  # Default to a popular voice
    "RUNWAY_API_KEY": os.getenv("RUNWAY_API_KEY"),
        }

