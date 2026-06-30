import sys
from app.config import validate_config
from app.utils.logger import setup_logger, get_logger
from app.bot import create_bot

def main() -> None:
    """TruthGuard application entry point."""
    # 1. Initialize logging
    setup_logger()
    logger = get_logger("main")
    logger.info("Initializing TruthGuard Telegram Bot...")

    # 2. Validate environment configuration
    try:
        validate_config()
        logger.info("Environment configuration validated successfully.")
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)

    # 3. Create bot application
    try:
        application = create_bot()
    except Exception as e:
        logger.critical(f"Failed to initialize the bot: {e}", exc_info=True)
        sys.exit(1)

    # 4. Start polling
    logger.info("Starting polling loop. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
