import os
import tempfile
import yt_dlp
import subprocess
from app.utils.logger import get_logger

logger = get_logger(__name__)

def update_yt_dlp():
    """Forces an update of yt-dlp to ensure latest extractors."""
    try:
        subprocess.check_call(["pip", "install", "-U", "yt-dlp"])
        logger.info("yt-dlp updated successfully.")
    except Exception as e:
        logger.warning(f"Could not update yt-dlp: {e}")

def download_video_audio(url: str) -> str:
    """Downloads the audio-only stream using yt-dlp with anti-bot measures."""
    logger.info(f"Starting audio download for URL: {url}")
    
    # Ensure yt-dlp is fresh
    update_yt_dlp()
    
    temp_dir = tempfile.gettempdir()
    
    # Configure yt-dlp with human-like headers
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': os.path.join(temp_dir, 'tg_audio_%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.instagram.com/',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Could not retrieve metadata.")
            
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return filename
            
            # Fallback search
            video_id = info.get('id')
            if video_id:
                for file in os.listdir(temp_dir):
                    if video_id in file and file.startswith('tg_audio_'):
                        return os.path.join(temp_dir, file)
            
            raise FileNotFoundError("Could not locate the downloaded file.")
            
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        # One-time retry after a forced update if it failed
        logger.info("Attempting one final retry after fresh update...")
        update_yt_dlp()
        raise RuntimeError(f"Ошибка загрузки. Видео может быть защищено или недоступно с сервера.")
