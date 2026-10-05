"""
Rate Limiting, Concurrency Throttling, and Exponential Backoff for BioAge-X Integrations.
Prevents provider bans, avoids retry storms, and provides structured logging of API telemetry.
"""

import time
import random
import threading
from functools import wraps
from typing import Callable, Any, Optional, Dict, Tuple
from bioage.utils.logger import get_logger

logger = get_logger("bioage.integrations.rate_limit")


class RateLimiter:
    """Thread-safe rate limiter with minimum interval enforcement."""

    def __init__(self, requests_per_second: float = 3.0, provider_name: str = "generic"):
        self.interval = 1.0 / max(0.1, requests_per_second)
        self.provider_name = provider_name
        self.lock = threading.Lock()
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Blocks until the required interval has elapsed since the last request."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                time.sleep(sleep_time)
            self.last_request_time = time.time()


def retry_with_backoff(
    provider_name: str,
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504),
):
    """
    Decorator for biological API requests with exponential backoff and jitter.
    Never retries permanent client errors (400, 404, 422).
    Logs latency, attempt count, provider, and outcome without credential leakage.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempts = 0
            start_time = time.time()
            last_exception: Optional[Exception] = None

            while attempts <= max_retries:
                attempts += 1
                try:
                    res = func(*args, **kwargs)
                    latency_ms = round((time.time() - start_time) * 1000, 2)
                    logger.debug(
                        f"[{provider_name}] Success on attempt {attempts}/{max_retries + 1} "
                        f"in {latency_ms}ms"
                    )
                    return res
                except Exception as exc:
                    last_exception = exc
                    latency_ms = round((time.time() - start_time) * 1000, 2)

                    # Extract HTTP status code if available (e.g. from requests.HTTPError or httpx)
                    status_code = getattr(getattr(exc, "response", None), "status_code", None)

                    # Permanent client errors should NOT be retried
                    if status_code in (400, 404, 422):
                        logger.warning(
                            f"[{provider_name}] Non-retryable client error {status_code} "
                            f"on attempt {attempts}: {exc}"
                        )
                        raise exc

                    # If we exceeded retries, break
                    if attempts > max_retries:
                        logger.error(
                            f"[{provider_name}] Failed after {attempts} attempts ({latency_ms}ms total): {exc}"
                        )
                        break

                    # Compute backoff with jitter
                    delay = min(max_delay, base_delay * (backoff_factor ** (attempts - 1)))
                    jitter = random.uniform(0.8, 1.2)
                    actual_delay = delay * jitter

                    logger.warning(
                        f"[{provider_name}] Transient error on attempt {attempts} (status={status_code}): {exc}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )
                    time.sleep(actual_delay)

            if last_exception:
                raise last_exception

        return wrapper
    return decorator
