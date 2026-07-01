import os
import tempfile
import yt_dlp
import subprocess
from app.utils.logger import get_logger
from app import config

logger = get_logger(__name__)

def update_yt_dlp():
    """Forces an update of yt-dlp to the master branch to ensure latest fixes."""
    try:
        # Installing from master branch to get the very latest extractor patches
        subprocess.check_call(["pip", "install", "-U", "https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz"])
        logger.info("yt-dlp updated to master branch successfully.")
    except Exception as e:
        logger.warning(f"Could not update yt-dlp: {e}")

def download_video_audio(url: str) -> str:
    logger.info(f"Starting audio download for URL: {url}")
    update_yt_dlp()
    
    temp_dir = tempfile.gettempdir()
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'outtmpl': os.path.join(temp_dir, 'tg_audio_%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.instagram.com/',
    }
    
    # Добавляем прокси, если он задан
    if config.PROXY_URL:
        logger.info(f"Using proxy: {config.PROXY_URL}")
        ydl_opts['proxy'] = config.PROXY_URL
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Could not retrieve metadata.")
            
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return filename
            
            video_id = info.get('id')
            if video_id:
                for file in os.listdir(temp_dir):
                    if video_id in file and file.startswith('tg_audio_'):
                        return os.path.join(temp_dir, file)
            
            raise FileNotFoundError("Could not locate the downloaded file.")
            
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise RuntimeError(f"Ошибка загрузки (Instagram/YouTube). Проверьте прокси.")
