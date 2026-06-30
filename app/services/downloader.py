import os
import tempfile
import yt_dlp
from app.utils.logger import get_logger

logger = get_logger(__name__)

def download_video_audio(url: str) -> str:
    """Downloads the audio-only stream from a video URL (e.g., YouTube, TikTok, Reddit)
    using yt-dlp and saves it locally in a temporary directory.

    Args:
        url (str): The video webpage URL.

    Returns:
        str: Absolute path to the downloaded audio file.
    """
    logger.info(f"Starting audio download for URL: {url}")
    
    # Use standard system temp directory
    temp_dir = tempfile.gettempdir()
    
    # Configure yt-dlp to grab only the best audio stream
    # Specifying 'bestaudio[ext=m4a]/bestaudio' allows us to download pre-merged, 
    # single-stream M4A files directly, which does NOT require ffmpeg post-processing.
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': os.path.join(temp_dir, 'tg_audio_%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download file and extract details
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("yt-dlp could not retrieve video metadata.")
            
            # Predict output path
            filename = ydl.prepare_filename(info)
            
            # Verify if it exists
            if os.path.exists(filename):
                logger.info(f"Audio downloaded successfully: {filename}")
                return filename
            
            # Fallback search if the actual extension differed from the template prediction
            video_id = info.get('id')
            if video_id:
                for file in os.listdir(temp_dir):
                    if video_id in file and file.startswith('tg_audio_'):
                        found_path = os.path.join(temp_dir, file)
                        logger.info(f"Located downloaded audio file by matching ID: {found_path}")
                        return found_path
            
            raise FileNotFoundError(f"Could not locate the downloaded file: {filename}")
            
    except Exception as e:
        logger.error(f"Failed to download audio from {url}: {e}", exc_info=True)
        # Raise a user-friendly error to display in the bot chat
        raise RuntimeError(f"Ошибка при загрузке аудио по ссылке. Убедитесь, что видео доступно публично.")
