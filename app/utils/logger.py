import logging
import sys
from app import config

def setup_logger() -> None:
    """Configures the root logger based on application configuration."""
    log_level_name = config.LOG_LEVEL
    # Fallback to INFO if the provided log level name is invalid
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Output to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.setLevel(log_level)
    
    # Clear any pre-existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)
        
    root.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """Helper to return a logger for a specific module."""
    return logging.getLogger(name)
