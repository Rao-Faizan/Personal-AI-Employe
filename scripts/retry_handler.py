#!/usr/bin/env python3
"""
Retry Handler for AI Employee - Gold Tier

Provides exponential backoff retry logic for all external API calls
and browser automation operations. Apply with @with_retry decorator.

Usage:
    from scripts.retry_handler import with_retry

    @with_retry(max_attempts=3)
    def call_gmail_api():
        ...

    @with_retry(max_attempts=5, base_delay=2, max_delay=120)
    def send_email():
        ...
"""

import time
import logging
from functools import wraps
from typing import Tuple, Type

logger = logging.getLogger('RetryHandler')


# Errors that are safe to retry (transient failures)
TRANSIENT_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = TRANSIENT_ERRORS,
    on_retry=None
):
    """
    Decorator for exponential backoff retry logic.

    Args:
        max_attempts:          Total attempts (1 = no retry)
        base_delay:            Initial wait in seconds before first retry
        max_delay:             Cap on wait time between retries
        retryable_exceptions:  Exception types that trigger a retry
        on_retry:              Optional callback(attempt, delay, exc) for logging/alerting
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            f"[{func.__name__}] All {max_attempts} attempts failed. "
                            f"Last error: {exc}"
                        )
                        raise

                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{max_attempts} failed: {exc}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    if on_retry:
                        try:
                            on_retry(attempt, delay, exc)
                        except Exception:
                            pass
                    time.sleep(delay)
                except Exception as exc:
                    # Non-retryable error — fail immediately
                    logger.error(f"[{func.__name__}] Non-retryable error: {exc}")
                    raise
            raise last_exc  # should never reach here
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager version of retry logic.
    Useful when you need more control inside the retry loop.

    Usage:
        with RetryContext(max_attempts=3) as ctx:
            while ctx.should_try():
                try:
                    result = do_something()
                    ctx.succeeded()
                    break
                except ConnectionError as e:
                    ctx.failed(e)
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.attempt = 0
        self._done = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def should_try(self) -> bool:
        return not self._done and self.attempt < self.max_attempts

    def succeeded(self):
        self._done = True

    def failed(self, exc: Exception):
        self.attempt += 1
        if self.attempt >= self.max_attempts:
            logger.error(f"RetryContext: All {self.max_attempts} attempts failed. Last: {exc}")
            raise exc
        delay = min(self.base_delay * (2 ** (self.attempt - 1)), self.max_delay)
        logger.warning(f"RetryContext: Attempt {self.attempt} failed: {exc}. Retrying in {delay:.1f}s...")
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Pre-configured decorators for common use-cases in this project
# ---------------------------------------------------------------------------

def retry_api(func):
    """For Gmail, Odoo, and other HTTP API calls (3 attempts, 2s base delay)."""
    return with_retry(max_attempts=3, base_delay=2.0, max_delay=60.0)(func)


def retry_browser(func):
    """For Playwright browser actions (2 attempts, 5s base delay)."""
    return with_retry(max_attempts=2, base_delay=5.0, max_delay=30.0)(func)


def retry_file(func):
    """For file system operations (3 attempts, 0.5s base delay)."""
    return with_retry(max_attempts=3, base_delay=0.5, max_delay=5.0)(func)


if __name__ == "__main__":
    # Quick self-test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    call_count = 0

    @with_retry(max_attempts=3, base_delay=0.1)
    def flaky_function():
        global call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Simulated transient error on attempt {call_count}")
        return "success"

    result = flaky_function()
    print(f"[OK] retry_handler.py self-test passed. Result: {result} (took {call_count} attempts)")
