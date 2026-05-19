import logging
from functools import wraps
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


def safe_handler(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("Unhandled bot error in %s", func.__name__)
            return {"ok": False, "error": "internal_error"}

    return wrapper
