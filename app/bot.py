from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app import config
from app.handlers import start_command, help_command, handle_text_message, error_handler
from app.services.gemini import GeminiService
from app.services.factcheck import FactCheckService
from app.utils.logger import get_logger

logger = get_logger(__name__)

def create_bot() -> Application:
    """Builds and configures the Telegram Bot application.

    Returns:
        Application: The configured python-telegram-bot Application instance.
    """
    logger.info("Initializing services...")
    
    # Initialize services
    gemini_service = GeminiService()
    factcheck_service = FactCheckService(gemini_service)
    
    logger.info("Building python-telegram-bot application...")
    
    # Build the application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Inject services into bot_data so handlers can access them
    application.bot_data["factcheck_service"] = factcheck_service
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Register error logger
    application.add_error_handler(error_handler)
    
    logger.info("Telegram Bot configuration completed.")
    return application
