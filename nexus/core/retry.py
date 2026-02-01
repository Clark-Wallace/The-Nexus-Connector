"""
Retry Logic - Exponential backoff with jitter and circuit breaker.

Provides production-ready retry mechanisms for handling transient failures
when communicating with AI providers.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union
import logging


logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests flow through
    OPEN = "open"          # Failing, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0           # Initial delay in seconds
    max_delay: float = 60.0           # Maximum delay cap
    exponential_base: float = 2.0     # Multiplier for exponential backoff
    jitter: float = 0.1               # Random jitter factor (0-1)
    retryable_exceptions: tuple = (Exception,)  # Exceptions to retry on
    retryable_status_codes: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5        # Failures before opening circuit
    success_threshold: int = 2        # Successes in half-open before closing
    timeout: float = 30.0             # Seconds before trying half-open
    half_open_max_calls: int = 3      # Max concurrent calls in half-open


class CircuitBreaker:
    """
    Circuit breaker for preventing cascading failures.

    States:
    - CLOSED: Normal operation, tracking failures
    - OPEN: Blocking all requests, waiting for timeout
    - HALF_OPEN: Allowing limited requests to test recovery
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transition."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout:
                    return CircuitState.HALF_OPEN
        return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    async def can_execute(self) -> bool:
        """Check if a request can be executed."""
        async with self._lock:
            state = self.state

            if state == CircuitState.CLOSED:
                return True

            if state == CircuitState.OPEN:
                return False

            # Half-open: allow limited calls
            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return False

    async def record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._close()
                    logger.info(f"Circuit {self.name}: CLOSED (recovered)")
            else:
                # Reset failure count on success in closed state
                self._failure_count = 0

    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens the circuit
                self._open()
                logger.warning(f"Circuit {self.name}: OPEN (failed in half-open)")

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._open()
                    logger.warning(
                        f"Circuit {self.name}: OPEN "
                        f"(threshold {self.config.failure_threshold} reached)"
                    )

    def _open(self) -> None:
        """Transition to open state."""
        self._state = CircuitState.OPEN
        self._half_open_calls = 0
        self._success_count = 0

    def _close(self) -> None:
        """Transition to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self._close()
        self._last_failure_time = None

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time,
            "time_until_half_open": (
                max(0, self.config.timeout - (time.time() - self._last_failure_time))
                if self._state == CircuitState.OPEN and self._last_failure_time
                else None
            ),
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    def __init__(self, circuit_name: str, time_until_retry: Optional[float] = None):
        self.circuit_name = circuit_name
        self.time_until_retry = time_until_retry
        super().__init__(
            f"Circuit '{circuit_name}' is open. "
            f"Retry after {time_until_retry:.1f}s" if time_until_retry else ""
        )


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"All {attempts} retry attempts exhausted. Last error: {last_error}")


class RetryHandler:
    """
    Handles retry logic with exponential backoff and circuit breaker.

    Usage:
        handler = RetryHandler(config=RetryConfig(max_retries=3))
        result = await handler.execute(my_async_function, arg1, arg2)
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    ):
        """
        Initialize retry handler.

        Args:
            config: Retry configuration
            circuit_breaker: Optional circuit breaker
            on_retry: Callback called before each retry (attempt, error, delay)
        """
        self.config = config or RetryConfig()
        self.circuit_breaker = circuit_breaker
        self.on_retry = on_retry

    async def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func

        Raises:
            CircuitOpenError: If circuit breaker is open
            RetryExhaustedError: If all retries exhausted
        """
        # Check circuit breaker
        if self.circuit_breaker:
            if not await self.circuit_breaker.can_execute():
                status = self.circuit_breaker.get_status()
                raise CircuitOpenError(
                    self.circuit_breaker.name,
                    status.get("time_until_half_open")
                )

        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Record success
                if self.circuit_breaker:
                    await self.circuit_breaker.record_success()

                return result

            except self.config.retryable_exceptions as e:
                last_error = e

                # Record failure
                if self.circuit_breaker:
                    await self.circuit_breaker.record_failure(e)

                # Check if we should retry
                if attempt < self.config.max_retries:
                    delay = self.config.get_delay(attempt)

                    logger.debug(
                        f"Retry {attempt + 1}/{self.config.max_retries} "
                        f"after {delay:.2f}s: {e}"
                    )

                    # Call retry callback
                    if self.on_retry:
                        try:
                            self.on_retry(attempt + 1, e, delay)
                        except Exception:
                            pass

                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    raise RetryExhaustedError(attempt + 1, last_error)

        # Should not reach here, but just in case
        raise RetryExhaustedError(self.config.max_retries + 1, last_error)


def with_retry(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
):
    """
    Decorator to add retry logic to an async function.

    Usage:
        @with_retry(config=RetryConfig(max_retries=3))
        async def my_function():
            ...
    """
    handler = RetryHandler(config, circuit_breaker, on_retry)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await handler.execute(func, *args, **kwargs)
        return wrapper

    return decorator


# Pre-configured retry configs for common scenarios
RETRY_CONFIGS = {
    "aggressive": RetryConfig(
        max_retries=5,
        base_delay=0.5,
        max_delay=30.0,
        exponential_base=2.0,
    ),
    "standard": RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
    ),
    "conservative": RetryConfig(
        max_retries=2,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=3.0,
    ),
    "rate_limit": RetryConfig(
        max_retries=5,
        base_delay=5.0,
        max_delay=300.0,  # 5 minutes
        exponential_base=2.0,
        jitter=0.2,
    ),
}
