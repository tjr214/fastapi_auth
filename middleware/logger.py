import sys
import time
import os
import logging
from logging.handlers import SysLogHandler
import socket

from fastapi import Request


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

# Get logger
logger = logging.getLogger(LOGGER_ROOT_NAME)

# Create formatters
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s: %(message)s - %(filename)s (%(funcName)s, %(lineno)d)",
    datefmt="%Y-%m-%d %H:%M:%S"
)
remote_formatter = logging.Formatter(
    fmt="%(asctime)s - %(hostname)s %(name)s: %(message)s - %(filename)s (%(funcName)s, %(lineno)d)",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create handlers
io_stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("server.log")
papertrail_handler = SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT))
papertrail_handler.addFilter(ContextFilter())

# Format handlers
io_stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
papertrail_handler.setFormatter(remote_formatter)

# Add the handlers to the logger
logger.handlers = [
    io_stream_handler,
    file_handler,
    papertrail_handler,
]

# Set log-level
logger.setLevel(LOG_LEVEL)


async def log_middleware(request: Request, call_next):
    time_start = time.time()
    response = await call_next(request)
    time_end = time.time() - time_start

    log_dict = {
        "url": request.url.path,
        "method": request.method,
        "procces_time": time_end
    }
    logger.info(log_dict, extra=log_dict)
    return response
