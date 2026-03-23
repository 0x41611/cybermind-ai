"""
CyberMind AI - Logger
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from config import config


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "\033[36m%(asctime)s\033[0m \033[32m%(name)s\033[0m %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    ))

    # File handler
    log_dir = config.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"cybermind_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s: %(message)s"
    ))

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger


# Default logger
logger = get_logger("cybermind")
