from telegram import Update, constants
from telegram.ext import ContextTypes
from app.services.factcheck import FactCheckService
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting message when the command /start is issued."""
    user = update.effective_user
    username = user.username if user else "Unknown"
    logger.info(f"User {user.id if user else 'N/A'} (@{username}) started the bot.")
    
    greeting = (
        f"Привет, {user.first_name if user else 'друг'}! 🛡️\n\n"
        "Я бот **TruthGuard** для фактчекинга.\n\n"
        "Отправьте мне любое новостное сообщение, слух, цитату или утверждение, "
        "и я проанализирую его на достоверность с помощью ИИ Gemini.\n\n"
        "Просто напишите или перешлите мне текст для проверки!"
    )
    if update.message:
        await update.message.reply_text(greeting, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the command /help is issued."""
    help_text = (
        "🛡️ **Помощь TruthGuard**\n\n"
        "Чтобы проверить утверждение на достоверность, просто пришлите мне текстовое сообщение.\n\n"
        "**Примеры для проверки:**\n"
        "- *Земля плоская.*\n"
        "- *Витамин C полностью предотвращает простуду.*\n"
        "- *Правда ли, что бананы радиоактивны?*\n\n"
        "Я проанализирую текст и выдам структурированный разбор с вердиктом."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages by passing them to the FactCheckService."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username if user else "Unknown"

    logger.info(f"Received text message from {user.id if user else 'N/A'} (@{username})")

    # Send typing action to Telegram
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

    # Retrieve FactCheckService from bot_data
    factcheck_service: FactCheckService = context.bot_data.get("factcheck_service")
    if not factcheck_service:
        logger.error("FactCheckService not found in bot_data.")
        await update.message.reply_text(
            "Внутренняя ошибка: служба фактчекинга недоступна. Пожалуйста, обратитесь к администратору."
        )
        return

    try:
        # Run factcheck via the service
        verdict = factcheck_service.check_text(text)
        
        # Send the response back to user
        await update.message.reply_text(verdict, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при анализе вашего сообщения. Пожалуйста, попробуйте позже."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs the error when handling an update."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)
