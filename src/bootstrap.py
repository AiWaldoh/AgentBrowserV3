import os
import logging
from colorlog import ColoredFormatter
from dotenv import load_dotenv

load_dotenv()


class Config:
    SYSTEM_MESSAGE = "You are a helpful assistant."
    BOT_NAME = os.getenv("BOT_NAME")
    MODEL_NAME = os.getenv("MODEL_NAME")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    log_format = "\033[93m%(asctime)s\033[0m [\033[92m%(levelname)-5s\033[0m] \033[96m%(message)s\033[0m"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = ColoredFormatter(
        log_format,
        datefmt=date_format,
        reset=True,
        log_colors={},
        secondary_log_colors={},
        style="%",
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
