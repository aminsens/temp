"""
API configuration for OpenRouter + Gemma 4 31B.
"""

import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "google/gemma-4-31b-it:free"
