import time
from fastapi import Request
from backend.log import get_logger

logger = get_logger(__name__)


async def log_route(request: Request, call_next):
    time_start = time.time()
    response = await call_next(request)
    time_end = time.time() - time_start

    log_dict = {
        "url": request.url.path,
        "method": request.method,
    }
    if request.query_params._dict:
        log_dict["query_params"] = request.query_params._dict
    log_dict["time_to_complete"] = time_end
    logger.info(log_dict, extra=log_dict)
    return response
