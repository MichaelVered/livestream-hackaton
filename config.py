"""
Configuration file for Gemini Live API integration
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google AI API Configuration
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")

# Camera Configuration
DEFAULT_CAMERA_INDEX = int(os.getenv("DEFAULT_CAMERA_INDEX", "0"))
DEFAULT_FRAME_INTERVAL = float(os.getenv("DEFAULT_FRAME_INTERVAL", "0.5"))  # seconds between frames sent to Gemini

# Video Configuration
DEFAULT_WIDTH = int(os.getenv("DEFAULT_WIDTH", "1280"))
DEFAULT_HEIGHT = int(os.getenv("DEFAULT_HEIGHT", "720"))
DEFAULT_FPS = int(os.getenv("DEFAULT_FPS", "30"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "85"))

# Display Configuration
MAX_DESCRIPTION_LINES = 5
FONT_SCALE = 0.7
FONT_THICKNESS = 2
