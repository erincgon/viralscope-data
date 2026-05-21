"""Retry decorators with exponential backoff."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, TypeVar

from loguru import logger

from config.settings import get_settings

F = TypeVar("F", bound=Callable[..., Any])


def sync_retry(
    *,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    max_retries: int | None = None,
    delay: float | None = None,
    backoff: float | None = None,
) -> Callable[[F], F]:
    """Retry a synchronous function with exponential backoff."""
    settings = get_settings()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = max_retries or settings.scraping.max_retries
            wait = delay or settings.scraping.retry_delay
            factor = backoff or settings.scraping.retry_backoff
            last_error: Exception | None = None

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    if attempt == retries:
                        break
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{retries}): {exc}"
                    )
                    import time

                    time.sleep(wait)
                    wait *= factor

            raise last_error  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


def async_retry(
    *,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    max_retries: int | None = None,
    delay: float | None = None,
    backoff: float | None = None,
) -> Callable[[F], F]:
    """Retry an async function with exponential backoff."""
    settings = get_settings()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = max_retries or settings.scraping.max_retries
            wait = delay or settings.scraping.retry_delay
            factor = backoff or settings.scraping.retry_backoff
            last_error: Exception | None = None

            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    if attempt == retries:
                        break
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{retries}): {exc}"
                    )
                    await asyncio.sleep(wait)
                    wait *= factor

            raise last_error  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
