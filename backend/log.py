import sys
import os
import logging
from logging import Logger
from logging.handlers import SysLogHandler
import socket

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


# Get sysenvs
LOG_LEVEL = int(os.getenv("LOG_LEVEL"))
PAPERTRAIL_HOST = str(os.getenv("PAPERTRAIL_HOST"))
PAPERTRAIL_PORT = int(os.getenv("PAPERTRAIL_PORT"))
LOGGER_ROOT_NAME = str(os.getenv("LOGGER_ROOT_NAME"))

# Create formatters
formatter = logging.Formatter(
    fmt="%(asctime)s (%(levelname)s) %(name)s [%(funcName)s, %(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
papertrail_formatter = logging.Formatter(
    fmt="%(asctime)s (%(hostname)s) %(name)s [%(funcName)s, %(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create handlers
io_stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("logs/debug.log")
papertrail_handler = SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT))
papertrail_handler.addFilter(ContextFilter())

# Format handlers
io_stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
papertrail_handler.setFormatter(papertrail_formatter)


# Get logger
def get_logger(name: str) -> Logger:
    logger = logging.getLogger(f"""{LOGGER_ROOT_NAME}.{name}""")
    # Add the handlers to the logger
    logger.handlers = [
        # io_stream_handler,
        file_handler,
        papertrail_handler,
    ]
    # Set log-level
    logger.setLevel(LOG_LEVEL)
    return logger
