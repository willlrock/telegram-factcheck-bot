import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PROXY_URL = os.getenv("PROXY_URL") # Добавлено
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def validate_config() -> None:
    """Validates that all required environment variables are set and not placeholders."""
    missing = []
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.strip() == "your_telegram_bot_token_here":
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "your_gemini_api_key_here":
        missing.append("GEMINI_API_KEY")
    
    if missing:
        raise ValueError(
            f"Missing or invalid required environment variables: {', '.join(missing)}. "
            "Please check your .env file or environment configuration."
        )
