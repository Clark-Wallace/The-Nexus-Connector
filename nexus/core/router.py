"""
Smart Router - Intelligent provider selection and fallback.

Provides:
- Task-based routing (code → Claude, math → GPT-4, etc.)
- Strategy-based selection (cost, quality, latency)
- Automatic fallback chains
- Load balancing across providers
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import logging
import re

from .base_connector import AIProvider


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies."""
    COST = "cost"           # Cheapest provider
    QUALITY = "quality"     # Best provider for task type
    LATENCY = "latency"     # Fastest provider
    FALLBACK = "fallback"   # Sequential fallback
    ROUND_ROBIN = "round_robin"  # Distribute evenly
    RANDOM = "random"       # Random selection
    ADAPTIVE = "adaptive"   # Learn from performance


@dataclass
class ProviderStats:
    """Performance statistics for a provider."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return float('inf')
        return self.total_latency_ms / self.successful_requests

    @property
    def avg_cost_per_request(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_cost / self.successful_requests

    def record_success(self, latency_ms: float, tokens: int, cost: float) -> None:
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.total_cost += cost
        self.consecutive_failures = 0

    def record_failure(self, error: str) -> None:
        self.total_requests += 1
        self.failed_requests += 1
        self.last_error = error
        self.last_error_time = time.time()
        self.consecutive_failures += 1


@dataclass
class ProviderConfig:
    """Configuration for a provider in the router."""
    provider: AIProvider
    api_key: str
    model: Optional[str] = None
    priority: int = 0  # Higher = preferred
    weight: float = 1.0  # For weighted random
    max_retries: int = 2
    timeout: float = 60.0
    enabled: bool = True
    tags: List[str] = field(default_factory=list)  # e.g., ["code", "fast", "cheap"]

    # Cost info (per 1M tokens)
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0


# Default cost estimates per provider (per 1M tokens, approximate)
DEFAULT_COSTS: Dict[AIProvider, Tuple[float, float]] = {
    AIProvider.OPENAI: (2.50, 10.00),      # GPT-4o
    AIProvider.ANTHROPIC: (3.00, 15.00),   # Claude 3.5 Sonnet
    AIProvider.GOOGLE: (0.075, 0.30),      # Gemini 1.5 Flash
    AIProvider.XAI: (2.00, 10.00),         # Grok
    AIProvider.DEEPSEEK: (0.14, 0.28),     # DeepSeek V3
    AIProvider.OLLAMA: (0.0, 0.0),         # Local, free
}

# Default quality ratings per task type
DEFAULT_QUALITY_RATINGS: Dict[str, Dict[AIProvider, float]] = {
    "code": {
        AIProvider.ANTHROPIC: 0.95,
        AIProvider.OPENAI: 0.90,
        AIProvider.DEEPSEEK: 0.88,
        AIProvider.GOOGLE: 0.80,
        AIProvider.XAI: 0.75,
        AIProvider.OLLAMA: 0.70,
    },
    "math": {
        AIProvider.OPENAI: 0.95,
        AIProvider.ANTHROPIC: 0.90,
        AIProvider.DEEPSEEK: 0.85,
        AIProvider.GOOGLE: 0.85,
        AIProvider.XAI: 0.75,
        AIProvider.OLLAMA: 0.65,
    },
    "creative": {
        AIProvider.ANTHROPIC: 0.95,
        AIProvider.OPENAI: 0.90,
        AIProvider.GOOGLE: 0.85,
        AIProvider.XAI: 0.80,
        AIProvider.DEEPSEEK: 0.70,
        AIProvider.OLLAMA: 0.65,
    },
    "analysis": {
        AIProvider.ANTHROPIC: 0.95,
        AIProvider.OPENAI: 0.92,
        AIProvider.GOOGLE: 0.85,
        AIProvider.DEEPSEEK: 0.80,
        AIProvider.XAI: 0.75,
        AIProvider.OLLAMA: 0.65,
    },
    "general": {
        AIProvider.OPENAI: 0.90,
        AIProvider.ANTHROPIC: 0.90,
        AIProvider.GOOGLE: 0.85,
        AIProvider.DEEPSEEK: 0.80,
        AIProvider.XAI: 0.80,
        AIProvider.OLLAMA: 0.70,
    },
}


class TaskClassifier:
    """Classifies tasks/prompts into categories for routing."""

    # Patterns for task classification
    PATTERNS: Dict[str, List[str]] = {
        "code": [
            r"\b(code|program|function|class|implement|debug|refactor|api|endpoint)\b",
            r"\b(python|javascript|typescript|java|rust|go|c\+\+|sql)\b",
            r"\b(bug|error|exception|fix|test|unittest)\b",
            r"```",  # Code blocks
        ],
        "math": [
            r"\b(calculate|compute|solve|equation|formula|math|algebra)\b",
            r"\b(derivative|integral|matrix|vector|probability|statistics)\b",
            r"[0-9]+\s*[\+\-\*\/\^]\s*[0-9]+",  # Math expressions
            r"\b(sum|product|average|mean|median|variance)\b",
        ],
        "creative": [
            r"\b(write|story|poem|creative|imagine|fiction|narrative)\b",
            r"\b(character|plot|scene|dialogue|setting)\b",
            r"\b(blog|article|essay|content)\b",
        ],
        "analysis": [
            r"\b(analyze|analysis|compare|contrast|evaluate|assess)\b",
            r"\b(pros|cons|advantages|disadvantages|tradeoffs)\b",
            r"\b(review|critique|examine|investigate)\b",
        ],
    }

    @classmethod
    def classify(cls, text: str) -> str:
        """
        Classify text into a task category.

        Returns one of: "code", "math", "creative", "analysis", "general"
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}

        for category, patterns in cls.PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches)
            scores[category] = score

        if not scores or max(scores.values()) == 0:
            return "general"

        return max(scores, key=scores.get)


class Router:
    """
    Smart router for selecting AI providers.

    Supports multiple routing strategies and automatic fallback.
    """

    def __init__(
        self,
        providers: Optional[List[ProviderConfig]] = None,
        strategy: Union[RoutingStrategy, str] = RoutingStrategy.FALLBACK,
        routing_rules: Optional[Dict[str, str]] = None,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_timeout: float = 60.0,
    ):
        """
        Initialize the router.

        Args:
            providers: List of provider configurations
            strategy: Default routing strategy
            routing_rules: Task type → provider mapping
                          e.g., {"code": "anthropic", "math": "openai"}
            circuit_breaker_threshold: Consecutive failures before disabling provider
            circuit_breaker_timeout: Seconds before re-enabling failed provider
        """
        self._providers: Dict[AIProvider, ProviderConfig] = {}
        self._stats: Dict[AIProvider, ProviderStats] = {}
        self._round_robin_index = 0

        if isinstance(strategy, str):
            strategy = RoutingStrategy(strategy)
        self.strategy = strategy

        self.routing_rules = routing_rules or {}
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # Register providers
        if providers:
            for config in providers:
                self.add_provider(config)

    def add_provider(self, config: ProviderConfig) -> None:
        """Add a provider to the router."""
        # Set default costs if not specified
        if config.input_cost_per_million == 0.0 and config.provider in DEFAULT_COSTS:
            config.input_cost_per_million = DEFAULT_COSTS[config.provider][0]
            config.output_cost_per_million = DEFAULT_COSTS[config.provider][1]

        self._providers[config.provider] = config
        self._stats[config.provider] = ProviderStats()
        logger.debug(f"Added provider to router: {config.provider.value}")

    def remove_provider(self, provider: AIProvider) -> bool:
        """Remove a provider from the router."""
        if provider in self._providers:
            del self._providers[provider]
            del self._stats[provider]
            return True
        return False

    def get_available_providers(self) -> List[AIProvider]:
        """Get list of currently available providers."""
        available = []
        now = time.time()

        for provider, config in self._providers.items():
            if not config.enabled:
                continue

            stats = self._stats[provider]

            # Check circuit breaker
            if stats.consecutive_failures >= self.circuit_breaker_threshold:
                if stats.last_error_time:
                    time_since_error = now - stats.last_error_time
                    if time_since_error < self.circuit_breaker_timeout:
                        logger.debug(
                            f"Provider {provider.value} circuit breaker open "
                            f"({stats.consecutive_failures} failures)"
                        )
                        continue
                    else:
                        # Reset circuit breaker after timeout
                        stats.consecutive_failures = 0

            available.append(provider)

        return available

    def select_provider(
        self,
        message: Optional[str] = None,
        strategy: Optional[RoutingStrategy] = None,
        exclude: Optional[List[AIProvider]] = None,
    ) -> Optional[AIProvider]:
        """
        Select the best provider based on strategy.

        Args:
            message: The message/task (for task-based routing)
            strategy: Override the default strategy
            exclude: Providers to exclude from selection

        Returns:
            Selected provider or None if no provider available
        """
        strategy = strategy or self.strategy
        exclude = exclude or []

        available = [
            p for p in self.get_available_providers()
            if p not in exclude
        ]

        if not available:
            return None

        # Task-based routing takes precedence
        if message and self.routing_rules:
            task_type = TaskClassifier.classify(message)
            if task_type in self.routing_rules:
                preferred = self.routing_rules[task_type]
                # Convert string to AIProvider if needed
                if isinstance(preferred, str):
                    try:
                        preferred = AIProvider(preferred.lower())
                    except ValueError:
                        preferred = None

                if preferred and preferred in available:
                    logger.debug(f"Task-based routing: {task_type} → {preferred.value}")
                    return preferred

        # Apply strategy
        if strategy == RoutingStrategy.COST:
            return self._select_by_cost(available)
        elif strategy == RoutingStrategy.QUALITY:
            task_type = TaskClassifier.classify(message) if message else "general"
            return self._select_by_quality(available, task_type)
        elif strategy == RoutingStrategy.LATENCY:
            return self._select_by_latency(available)
        elif strategy == RoutingStrategy.FALLBACK:
            return self._select_by_priority(available)
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available)
        elif strategy == RoutingStrategy.RANDOM:
            return self._select_random(available)
        elif strategy == RoutingStrategy.ADAPTIVE:
            return self._select_adaptive(available, message)

        # Default to first available
        return available[0] if available else None

    def _select_by_cost(self, available: List[AIProvider]) -> AIProvider:
        """Select cheapest provider."""
        def cost_score(p: AIProvider) -> float:
            config = self._providers[p]
            # Average of input and output cost
            return (config.input_cost_per_million + config.output_cost_per_million) / 2

        return min(available, key=cost_score)

    def _select_by_quality(
        self,
        available: List[AIProvider],
        task_type: str
    ) -> AIProvider:
        """Select highest quality provider for task type."""
        ratings = DEFAULT_QUALITY_RATINGS.get(task_type, DEFAULT_QUALITY_RATINGS["general"])

        def quality_score(p: AIProvider) -> float:
            return ratings.get(p, 0.5)

        return max(available, key=quality_score)

    def _select_by_latency(self, available: List[AIProvider]) -> AIProvider:
        """Select fastest provider based on historical latency."""
        def latency_score(p: AIProvider) -> float:
            stats = self._stats[p]
            if stats.successful_requests == 0:
                return 1000.0  # Unknown, assume moderate
            return stats.avg_latency_ms

        return min(available, key=latency_score)

    def _select_by_priority(self, available: List[AIProvider]) -> AIProvider:
        """Select by configured priority (for fallback)."""
        def priority_score(p: AIProvider) -> int:
            return self._providers[p].priority

        return max(available, key=priority_score)

    def _select_round_robin(self, available: List[AIProvider]) -> AIProvider:
        """Select using round-robin."""
        # Sort for consistent ordering
        sorted_providers = sorted(available, key=lambda p: p.value)
        selected = sorted_providers[self._round_robin_index % len(sorted_providers)]
        self._round_robin_index += 1
        return selected

    def _select_random(self, available: List[AIProvider]) -> AIProvider:
        """Select randomly, optionally weighted."""
        weights = [self._providers[p].weight for p in available]
        return random.choices(available, weights=weights, k=1)[0]

    def _select_adaptive(
        self,
        available: List[AIProvider],
        message: Optional[str]
    ) -> AIProvider:
        """
        Adaptive selection based on multiple factors.

        Combines quality, cost, latency, and success rate.
        """
        task_type = TaskClassifier.classify(message) if message else "general"
        quality_ratings = DEFAULT_QUALITY_RATINGS.get(task_type, DEFAULT_QUALITY_RATINGS["general"])

        def adaptive_score(p: AIProvider) -> float:
            config = self._providers[p]
            stats = self._stats[p]

            # Quality (0-1)
            quality = quality_ratings.get(p, 0.5)

            # Cost efficiency (inverted, normalized to 0-1)
            max_cost = max(
                (c.input_cost_per_million + c.output_cost_per_million)
                for c in self._providers.values()
            ) or 1
            cost = (config.input_cost_per_million + config.output_cost_per_million) / 2
            cost_score = 1 - (cost / max_cost)

            # Latency (inverted, normalized)
            latency = stats.avg_latency_ms if stats.successful_requests > 0 else 1000
            latency_score = 1 / (1 + latency / 1000)

            # Success rate (0-1)
            success = stats.success_rate

            # Weighted combination
            return (
                quality * 0.35 +
                cost_score * 0.25 +
                latency_score * 0.20 +
                success * 0.20
            )

        return max(available, key=adaptive_score)

    def record_success(
        self,
        provider: AIProvider,
        latency_ms: float,
        tokens: int = 0,
        cost: float = 0.0
    ) -> None:
        """Record a successful request."""
        if provider in self._stats:
            self._stats[provider].record_success(latency_ms, tokens, cost)

    def record_failure(self, provider: AIProvider, error: str) -> None:
        """Record a failed request."""
        if provider in self._stats:
            self._stats[provider].record_failure(error)
            logger.warning(
                f"Provider {provider.value} failure recorded: {error} "
                f"(consecutive: {self._stats[provider].consecutive_failures})"
            )

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        return {
            provider.value: {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "success_rate": round(stats.success_rate, 3),
                "avg_latency_ms": round(stats.avg_latency_ms, 2),
                "total_cost": round(stats.total_cost, 4),
                "consecutive_failures": stats.consecutive_failures,
                "enabled": self._providers[provider].enabled,
            }
            for provider, stats in self._stats.items()
        }

    def get_fallback_order(
        self,
        message: Optional[str] = None,
        max_providers: int = 3
    ) -> List[AIProvider]:
        """
        Get ordered list of providers for fallback.

        Returns providers in order of preference, up to max_providers.
        """
        available = self.get_available_providers()
        if not available:
            return []

        # Start with selected provider
        primary = self.select_provider(message)
        if not primary:
            return []

        order = [primary]
        remaining = [p for p in available if p != primary]

        # Add remaining by priority
        remaining.sort(key=lambda p: self._providers[p].priority, reverse=True)
        order.extend(remaining[:max_providers - 1])

        return order[:max_providers]


def create_router_from_env(
    strategy: Union[RoutingStrategy, str] = RoutingStrategy.FALLBACK,
    routing_rules: Optional[Dict[str, str]] = None,
) -> Router:
    """
    Create a router from environment variables.

    Looks for API keys in standard environment variables:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - GOOGLE_API_KEY
    - XAI_API_KEY
    - DEEPSEEK_API_KEY

    Args:
        strategy: Routing strategy to use
        routing_rules: Optional task → provider mapping

    Returns:
        Configured Router instance
    """
    import os

    router = Router(strategy=strategy, routing_rules=routing_rules)

    # Map of provider to env var and default model
    provider_env_map: Dict[AIProvider, Tuple[str, str]] = {
        AIProvider.OPENAI: ("OPENAI_API_KEY", "gpt-4o"),
        AIProvider.ANTHROPIC: ("ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"),
        AIProvider.GOOGLE: ("GOOGLE_API_KEY", "gemini-1.5-flash"),
        AIProvider.XAI: ("XAI_API_KEY", "grok-2"),
        AIProvider.DEEPSEEK: ("DEEPSEEK_API_KEY", "deepseek-chat"),
    }

    # Priority order (higher = try first in fallback)
    priorities = {
        AIProvider.ANTHROPIC: 100,
        AIProvider.OPENAI: 90,
        AIProvider.DEEPSEEK: 80,
        AIProvider.GOOGLE: 70,
        AIProvider.XAI: 60,
    }

    for provider, (env_var, default_model) in provider_env_map.items():
        api_key = os.getenv(env_var)
        if api_key:
            router.add_provider(ProviderConfig(
                provider=provider,
                api_key=api_key,
                model=default_model,
                priority=priorities.get(provider, 0),
            ))
            logger.info(f"Added provider from env: {provider.value}")

    return router
