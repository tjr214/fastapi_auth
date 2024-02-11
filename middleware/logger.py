import time
from fastapi import Request
from log import get_logger

logger = get_logger(__name__)


async def log_middleware(request: Request, call_next):
    time_start = time.time()
    response = await call_next(request)
    time_end = time.time() - time_start

    log_dict = {
        "url": request.url.path,
        "method": request.method,
    }
    if request.query_params._dict:
        log_dict["query_params"] = request.query_params._dict
    log_dict["procces_time"] = time_end
    logger.info(log_dict, extra=log_dict)
    return response
