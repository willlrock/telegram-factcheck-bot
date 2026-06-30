import os
import re
import asyncio
import tempfile
from telegram import Update, constants
from telegram.ext import ContextTypes
from app.services.factcheck import FactCheckService
from app.services.downloader import download_video_audio
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Regular expression to identify HTTP/HTTPS links
URL_PATTERN = re.compile(r'https?://[^\s]+')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting message when the command /start is issued."""
    user = update.effective_user
    username = user.username if user else "Unknown"
    logger.info(f"User {user.id if user else 'N/A'} (@{username}) started the bot.")
    
    greeting = (
        f"Привет, {user.first_name if user else 'друг'}! 🛡️\n\n"
        "Я бот **TruthGuard** для фактчекинга.\n\n"
        "Я умею анализировать на достоверность:\n"
        "1. **Текстовые сообщения** (слухи, утверждения).\n"
        "2. **Ссылки на видео** (YouTube, TikTok и др.).\n"
        "3. **Голосовые и видеосообщения** (кружки), а также аудио- и видеофайлы.\n\n"
        "Просто напишите мне, пришлите ссылку или запишите голосовое сообщение!"
    )
    if update.message:
        await update.message.reply_text(greeting, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the command /help is issued."""
    help_text = (
        "🛡️ **Помощь TruthGuard**\n\n"
        "Вы можете прислать мне контент следующими способами:\n"
        "- 📝 **Текст**: Просто напишите утверждение (например, *«Правда ли, что бананы радиоактивны?»*).\n"
        "- 🔗 **Ссылка**: Отправьте ссылку на видео с YouTube или TikTok.\n"
        "- 🎙️ **Аудио/Голос**: Запишите голосовое сообщение или пришлите аудиофайл.\n"
        "- 🎥 **Видео/Кружок**: Отправьте видеосообщение или видеофайл.\n\n"
        "Я расшифрую аудио и пришлю структурированный анализ."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages by checking for links or running plain text analysis."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username if user else "Unknown"

    # Retrieve FactCheckService
    factcheck_service: FactCheckService = context.bot_data.get("factcheck_service")
    if not factcheck_service:
        logger.error("FactCheckService not found in bot_data.")
        await update.message.reply_text(
            "Внутренняя ошибка: служба фактчекинга недоступна. Пожалуйста, обратитесь к администратору."
        )
        return

    # Check if the text contains a URL link
    url_match = URL_PATTERN.search(text)
    if url_match:
        url = url_match.group(0)
        logger.info(f"Link detected in text from @{username}: {url}")
        
        status_msg = await update.message.reply_text(
            "🔎 Обнаружена ссылка! Скачиваю аудиодорожку для анализа...",
            reply_to_message_id=update.message.message_id
        )
        
        local_file = None
        try:
            # Trigger audio download action
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.RECORD_VOICE)
            # Run blocking download in a separate thread
            local_file = await asyncio.to_thread(download_video_audio, url)
            
            await status_msg.edit_text("⏳ Аудио успешно загружено. Отправляю в Gemini для расшифровки и фактчекинга...")
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
            
            # Run blocking API call in a separate thread
            verdict = await asyncio.to_thread(factcheck_service.check_media, local_file)
            
            await status_msg.delete()
            await update.message.reply_text(verdict, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error checking link {url}: {e}", exc_info=True)
            await status_msg.edit_text(
                f"❌ Не удалось проанализировать видео по ссылке.\n\n"
                f"Ошибка: {e}"
            )
        finally:
            if local_file and os.path.exists(local_file):
                try:
                    os.remove(local_file)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove local link file {local_file}: {cleanup_err}")
        return

    # If no URL, treat as plain text claim
    logger.info(f"Received plain text message from @{username}")
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

    try:
        # Run in thread to prevent blocking
        verdict = await asyncio.to_thread(factcheck_service.check_text, text)
        await update.message.reply_text(verdict, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling plain text: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при анализе вашего сообщения. Пожалуйста, попробуйте позже."
        )

async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming media (voice messages, audio files, videos, video notes)."""
    if not update.message:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    username = user.username if user else "Unknown"

    media_file = None
    media_type = ""

    # Identify media type
    if update.message.voice:
        media_file = update.message.voice
        media_type = "Голосовое сообщение"
    elif update.message.audio:
        media_file = update.message.audio
        media_type = "Аудиофайл"
    elif update.message.video:
        media_file = update.message.video
        media_type = "Видеофайл"
    elif update.message.video_note:
        media_file = update.message.video_note
        media_type = "Видеосообщение (кружок)"

    if not media_file:
        logger.warning("Media handler triggered but no supported media found.")
        return

    logger.info(f"Processing {media_type} from @{username}")

    status_msg = await update.message.reply_text(
        f"📥 Получено {media_type.lower()}! Скачиваю файл для анализа...",
        reply_to_message_id=update.message.message_id
    )

    local_file_path = None
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.RECORD_VOICE)
        telegram_file = await media_file.get_file()

        # Determine file extension based on path or type fallback
        tg_path = telegram_file.file_path or ""
        ext = os.path.splitext(tg_path)[1]
        if not ext:
            if update.message.voice:
                ext = ".ogg"
            elif update.message.audio:
                ext = ".mp3"
            else:
                ext = ".mp4"

        # Save temporarily
        temp_dir = tempfile.gettempdir()
        local_file_path = os.path.join(temp_dir, f"tg_media_{telegram_file.file_unique_id}{ext}")
        await telegram_file.download_to_drive(custom_path=local_file_path)

        await status_msg.edit_text("⏳ Медиафайл загружен. Отправляю в Gemini для расшифровки и фактчекинга...")
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

        factcheck_service: FactCheckService = context.bot_data.get("factcheck_service")
        if not factcheck_service:
            raise ValueError("FactCheckService not found in bot_data.")

        # Run analysis in thread
        verdict = await asyncio.to_thread(factcheck_service.check_media, local_file_path)

        await status_msg.delete()
        await update.message.reply_text(verdict, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error handling media message: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ Не удалось обработать {media_type.lower()}.\n\n"
            f"Ошибка: {e}"
        )
    finally:
        # Cleanup local file
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except Exception as cleanup_err:
                logger.warning(f"Failed to remove local file {local_file_path}: {cleanup_err}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs the error when handling an update."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

