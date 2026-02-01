"""
Rate Limiter - Token bucket and sliding window rate limiting.

Provides rate limiting for AI provider API calls to prevent
hitting rate limits and manage costs.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging


logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(
        self,
        limit_name: str,
        retry_after: Optional[float] = None,
        message: Optional[str] = None
    ):
        self.limit_name = limit_name
        self.retry_after = retry_after
        msg = message or f"Rate limit '{limit_name}' exceeded"
        if retry_after:
            msg += f". Retry after {retry_after:.1f}s"
        super().__init__(msg)


class OverflowStrategy(Enum):
    """Strategy for handling requests when rate limit is exceeded."""
    REJECT = "reject"       # Reject immediately
    WAIT = "wait"           # Wait until capacity available
    QUEUE = "queue"         # Add to queue for later processing


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[float] = None
    requests_per_hour: Optional[float] = None
    requests_per_day: Optional[float] = None
    tokens_per_minute: Optional[int] = None
    tokens_per_day: Optional[int] = None
    max_concurrent: Optional[int] = None
    overflow_strategy: OverflowStrategy = OverflowStrategy.WAIT
    max_wait_time: float = 60.0  # Max seconds to wait when strategy is WAIT
    queue_size: int = 100        # Max queue size when strategy is QUEUE


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Attempt to acquire rate limit tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False if limit exceeded
        """
        pass

    @abstractmethod
    async def wait_and_acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until tokens available, then acquire.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait

        Returns:
            True if acquired, False if timeout
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        pass


class TokenBucketLimiter(RateLimiter):
    """
    Token bucket rate limiter.

    Tokens are added at a constant rate up to a maximum capacity.
    Each request consumes tokens.
    """

    def __init__(
        self,
        rate: float,           # Tokens per second
        capacity: float,       # Maximum bucket capacity
        name: str = "default"
    ):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
            name: Limiter name for logging
        """
        self.rate = rate
        self.capacity = capacity
        self.name = name
        self._tokens = capacity
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_update = now

    async def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire tokens immediately."""
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait_and_acquire(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """Wait until tokens available, then acquire."""
        start_time = time.monotonic()

        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                # Calculate wait time for tokens
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.rate

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            await asyncio.sleep(min(wait_time, 1.0))  # Check at least every second

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        self._refill()
        return {
            "name": self.name,
            "type": "token_bucket",
            "tokens_available": round(self._tokens, 2),
            "capacity": self.capacity,
            "rate_per_second": self.rate,
            "utilization": round(1 - (self._tokens / self.capacity), 2),
        }


class SlidingWindowLimiter(RateLimiter):
    """
    Sliding window rate limiter.

    Tracks requests in a time window and limits based on count.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        name: str = "default"
    ):
        """
        Initialize sliding window limiter.

        Args:
            limit: Maximum requests in window
            window_seconds: Window duration in seconds
            name: Limiter name for logging
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.name = name
        self._requests: List[float] = []  # Timestamps of requests
        self._lock = asyncio.Lock()

    def _cleanup(self) -> None:
        """Remove expired requests from window."""
        cutoff = time.monotonic() - self.window_seconds
        self._requests = [t for t in self._requests if t > cutoff]

    async def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire immediately."""
        async with self._lock:
            self._cleanup()
            if len(self._requests) + tokens <= self.limit:
                now = time.monotonic()
                for _ in range(tokens):
                    self._requests.append(now)
                return True
            return False

    async def wait_and_acquire(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """Wait until capacity available."""
        start_time = time.monotonic()

        while True:
            async with self._lock:
                self._cleanup()
                if len(self._requests) + tokens <= self.limit:
                    now = time.monotonic()
                    for _ in range(tokens):
                        self._requests.append(now)
                    return True

                # Calculate wait time until oldest request expires
                if self._requests:
                    oldest = self._requests[0]
                    wait_time = oldest + self.window_seconds - time.monotonic()
                else:
                    wait_time = 0.1

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            await asyncio.sleep(max(0.01, wait_time))

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        self._cleanup()
        return {
            "name": self.name,
            "type": "sliding_window",
            "current_count": len(self._requests),
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "utilization": round(len(self._requests) / self.limit, 2),
        }


class ConcurrencyLimiter:
    """
    Limits concurrent requests.

    Uses a semaphore to limit how many requests run simultaneously.
    """

    def __init__(self, max_concurrent: int, name: str = "default"):
        """
        Initialize concurrency limiter.

        Args:
            max_concurrent: Maximum concurrent requests
            name: Limiter name for logging
        """
        self.max_concurrent = max_concurrent
        self.name = name
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._current = 0
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        """Acquire semaphore."""
        await self._semaphore.acquire()
        async with self._lock:
            self._current += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release semaphore."""
        async with self._lock:
            self._current -= 1
        self._semaphore.release()

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "name": self.name,
            "type": "concurrency",
            "current": self._current,
            "max_concurrent": self.max_concurrent,
            "available": self.max_concurrent - self._current,
        }


class CompositeRateLimiter(RateLimiter):
    """
    Combines multiple rate limiters.

    All limiters must allow the request for it to proceed.
    """

    def __init__(self, limiters: List[RateLimiter], name: str = "composite"):
        """
        Initialize composite limiter.

        Args:
            limiters: List of rate limiters to combine
            name: Limiter name for logging
        """
        self.limiters = limiters
        self.name = name

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire from all limiters."""
        results = await asyncio.gather(
            *[limiter.acquire(tokens) for limiter in self.limiters]
        )
        return all(results)

    async def wait_and_acquire(
        self,
        tokens: int = 1,
        timeout: Optional[float] = None
    ) -> bool:
        """Wait and acquire from all limiters."""
        # Acquire from each limiter sequentially to avoid deadlocks
        for limiter in self.limiters:
            if not await limiter.wait_and_acquire(tokens, timeout):
                return False
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get status of all limiters."""
        return {
            "name": self.name,
            "type": "composite",
            "limiters": [limiter.get_status() for limiter in self.limiters],
        }


class ProviderRateLimiter:
    """
    Rate limiter configured for AI providers.

    Combines request rate limiting, token limiting, and concurrency control.
    """

    # Default limits for known providers (conservative estimates)
    PROVIDER_DEFAULTS: Dict[str, RateLimitConfig] = {
        "openai": RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=90000,
            max_concurrent=10,
        ),
        "anthropic": RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=100000,
            max_concurrent=10,
        ),
        "google": RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=120000,
            max_concurrent=10,
        ),
        "deepseek": RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=100000,
            max_concurrent=10,
        ),
        "xai": RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=100000,
            max_concurrent=10,
        ),
        "ollama": RateLimitConfig(
            max_concurrent=1,  # Local models typically process one at a time
        ),
    }

    def __init__(
        self,
        provider: str,
        config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize provider rate limiter.

        Args:
            provider: Provider name (openai, anthropic, etc.)
            config: Custom config (uses defaults if None)
        """
        self.provider = provider.lower()
        self.config = config or self.PROVIDER_DEFAULTS.get(
            self.provider,
            RateLimitConfig(requests_per_minute=60, max_concurrent=10)
        )

        # Build limiters based on config
        self._limiters: List[RateLimiter] = []
        self._concurrency: Optional[ConcurrencyLimiter] = None
        self._token_limiter: Optional[TokenBucketLimiter] = None

        self._build_limiters()

    def _build_limiters(self) -> None:
        """Build rate limiters from config."""
        config = self.config

        # Request rate limiters
        if config.requests_per_second:
            self._limiters.append(TokenBucketLimiter(
                rate=config.requests_per_second,
                capacity=config.requests_per_second * 2,
                name=f"{self.provider}_rps"
            ))

        if config.requests_per_minute:
            self._limiters.append(SlidingWindowLimiter(
                limit=int(config.requests_per_minute),
                window_seconds=60,
                name=f"{self.provider}_rpm"
            ))

        if config.requests_per_hour:
            self._limiters.append(SlidingWindowLimiter(
                limit=int(config.requests_per_hour),
                window_seconds=3600,
                name=f"{self.provider}_rph"
            ))

        # Token rate limiter
        if config.tokens_per_minute:
            self._token_limiter = TokenBucketLimiter(
                rate=config.tokens_per_minute / 60,
                capacity=config.tokens_per_minute,
                name=f"{self.provider}_tpm"
            )

        # Concurrency limiter
        if config.max_concurrent:
            self._concurrency = ConcurrencyLimiter(
                max_concurrent=config.max_concurrent,
                name=f"{self.provider}_concurrent"
            )

    async def acquire_request(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.

        Args:
            timeout: Maximum wait time

        Returns:
            True if acquired, False if timeout/rejected
        """
        timeout = timeout or self.config.max_wait_time

        for limiter in self._limiters:
            if self.config.overflow_strategy == OverflowStrategy.REJECT:
                if not await limiter.acquire():
                    return False
            else:
                if not await limiter.wait_and_acquire(timeout=timeout):
                    return False

        return True

    async def acquire_tokens(
        self,
        token_count: int,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire token quota.

        Args:
            token_count: Number of tokens to acquire
            timeout: Maximum wait time

        Returns:
            True if acquired, False if timeout/rejected
        """
        if not self._token_limiter:
            return True

        timeout = timeout or self.config.max_wait_time

        if self.config.overflow_strategy == OverflowStrategy.REJECT:
            return await self._token_limiter.acquire(token_count)
        else:
            return await self._token_limiter.wait_and_acquire(token_count, timeout)

    def get_concurrency_context(self) -> Optional[ConcurrencyLimiter]:
        """Get concurrency limiter for use as context manager."""
        return self._concurrency

    def get_status(self) -> Dict[str, Any]:
        """Get status of all limiters."""
        status = {
            "provider": self.provider,
            "request_limiters": [l.get_status() for l in self._limiters],
        }

        if self._token_limiter:
            status["token_limiter"] = self._token_limiter.get_status()

        if self._concurrency:
            status["concurrency"] = self._concurrency.get_status()

        return status


class RateLimiterManager:
    """
    Manages rate limiters for multiple providers.
    """

    def __init__(self):
        self._limiters: Dict[str, ProviderRateLimiter] = {}

    def get_limiter(
        self,
        provider: str,
        config: Optional[RateLimitConfig] = None
    ) -> ProviderRateLimiter:
        """
        Get or create a rate limiter for a provider.

        Args:
            provider: Provider name
            config: Optional custom config

        Returns:
            ProviderRateLimiter instance
        """
        provider = provider.lower()

        if provider not in self._limiters:
            self._limiters[provider] = ProviderRateLimiter(provider, config)

        return self._limiters[provider]

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all limiters."""
        return {
            provider: limiter.get_status()
            for provider, limiter in self._limiters.items()
        }


# Global rate limiter manager
_manager = RateLimiterManager()


def get_rate_limiter(
    provider: str,
    config: Optional[RateLimitConfig] = None
) -> ProviderRateLimiter:
    """Get rate limiter for a provider."""
    return _manager.get_limiter(provider, config)
