"""
Production Hardening Example - Enterprise-ready reliability features.

This example shows how to use Nexus's production hardening features:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Rate limiting
- Metrics collection
- Distributed tracing
"""

import asyncio
import os
from nexus import (
    NexusConnector,
    RetryConfig,
    CircuitBreaker,
    RETRY_CONFIGS,
    get_rate_limiter,
    NexusMetrics,
    get_metrics,
    get_tracer,
)
from nexus.core.retry import RetryHandler, CircuitBreakerConfig
from nexus.core.rate_limiter import RateLimitConfig, ProviderRateLimiter
from nexus.core.metrics import Tracer


async def example_1_retry_logic():
    """Example 1: Retry with exponential backoff."""
    print("=" * 60)
    print("Example 1: Retry Logic with Exponential Backoff")
    print("=" * 60)

    # Pre-configured retry strategies
    print("\nAvailable retry configs:")
    for name, config in RETRY_CONFIGS.items():
        print(f"  {name}:")
        print(f"    max_retries: {config.max_retries}")
        print(f"    base_delay: {config.base_delay}s")
        print(f"    max_delay: {config.max_delay}s")

    # Custom retry configuration
    custom_retry = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=0.1,  # ±10% randomness to prevent thundering herd
    )

    print(f"\nCustom config delays:")
    for attempt in range(custom_retry.max_retries + 1):
        delay = custom_retry.get_delay(attempt)
        print(f"  Attempt {attempt + 1}: ~{delay:.2f}s")

    # Using RetryHandler
    print("""
Usage with RetryHandler:

    handler = RetryHandler(config=RETRY_CONFIGS["standard"])

    async def my_api_call():
        return await make_request()

    result = await handler.execute(my_api_call)
""")

    # Using @with_retry decorator
    print("""
Usage with @with_retry decorator:

    from nexus.core.retry import with_retry

    @with_retry(config=RETRY_CONFIGS["aggressive"])
    async def fetch_data():
        return await api.get_data()
""")


async def example_2_circuit_breaker():
    """Example 2: Circuit breaker pattern."""
    print("\n" + "=" * 60)
    print("Example 2: Circuit Breaker Pattern")
    print("=" * 60)

    # Create a circuit breaker
    cb = CircuitBreaker(
        name="openai",
        config=CircuitBreakerConfig(
            failure_threshold=5,    # Open after 5 failures
            success_threshold=2,    # Close after 2 successes in half-open
            timeout=30.0,           # Try half-open after 30s
        )
    )

    print("\nCircuit breaker states:")
    print("  CLOSED:    Normal operation, tracking failures")
    print("  OPEN:      Blocking requests, waiting for timeout")
    print("  HALF_OPEN: Testing recovery with limited requests")

    print(f"\nInitial state: {cb.state.value}")

    # Simulate failures
    print("\nSimulating failures...")
    for i in range(5):
        await cb.record_failure(Exception(f"Error {i+1}"))
        print(f"  Failure {i+1}: state = {cb.state.value}")

    print(f"\nAfter 5 failures: {cb.state.value} (requests blocked!)")

    # Check if we can execute
    can_execute = await cb.can_execute()
    print(f"Can execute? {can_execute}")

    print("""
Usage with RetryHandler:

    handler = RetryHandler(
        config=RETRY_CONFIGS["standard"],
        circuit_breaker=CircuitBreaker("my_service"),
    )

    try:
        result = await handler.execute(risky_operation)
    except CircuitOpenError as e:
        print(f"Circuit open, retry after {e.time_until_retry}s")
""")


async def example_3_rate_limiting():
    """Example 3: Rate limiting."""
    print("\n" + "=" * 60)
    print("Example 3: Rate Limiting")
    print("=" * 60)

    # Get rate limiter for a provider (uses sensible defaults)
    limiter = get_rate_limiter("openai")

    print("\nDefault limits for OpenAI:")
    status = limiter.get_status()
    print(f"  Provider: {status['provider']}")
    for rl in status.get('request_limiters', []):
        print(f"  {rl['name']}: {rl.get('limit', 'N/A')} per window")
    if status.get('concurrency'):
        print(f"  Max concurrent: {status['concurrency']['max_concurrent']}")

    # Custom rate limit config
    custom_config = RateLimitConfig(
        requests_per_minute=30,     # 30 RPM
        tokens_per_minute=50000,    # 50K TPM
        max_concurrent=5,           # 5 concurrent requests
    )

    print(f"\nCustom config:")
    print(f"  requests_per_minute: {custom_config.requests_per_minute}")
    print(f"  tokens_per_minute: {custom_config.tokens_per_minute}")
    print(f"  max_concurrent: {custom_config.max_concurrent}")

    print("""
Usage:

    limiter = get_rate_limiter("anthropic")

    # Check if we can make a request
    if await limiter.acquire_request():
        response = await make_request()
        await limiter.acquire_tokens(response.token_count)
    else:
        print("Rate limited!")

    # Or wait for capacity
    await limiter.acquire_request(timeout=30)  # Wait up to 30s
""")


async def example_4_metrics():
    """Example 4: Metrics collection."""
    print("\n" + "=" * 60)
    print("Example 4: Metrics Collection")
    print("=" * 60)

    metrics = get_metrics()

    # Record some metrics
    await metrics.record_request(
        provider="openai",
        model="gpt-4o",
        success=True,
        duration_seconds=1.5,
        input_tokens=100,
        output_tokens=500,
        cost=0.01,
    )

    await metrics.record_request(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        success=True,
        duration_seconds=2.0,
        input_tokens=150,
        output_tokens=800,
        cost=0.02,
    )

    await metrics.record_tool_call(
        tool_name="create_file",
        success=True,
        duration_seconds=0.1,
    )

    # Get Prometheus-formatted metrics
    print("\nPrometheus metrics (sample):")
    prometheus_output = metrics.get_prometheus_metrics()
    # Print first 30 lines
    lines = prometheus_output.split('\n')[:30]
    for line in lines:
        print(f"  {line}")
    if len(prometheus_output.split('\n')) > 30:
        print("  ...")

    print("""
FastAPI integration:

    from fastapi import FastAPI
    from nexus.core.metrics import create_metrics_endpoint, get_metrics

    app = FastAPI()
    metrics = get_metrics()

    @app.get("/metrics")
    async def metrics_endpoint():
        return PlainTextResponse(metrics.get_prometheus_metrics())
""")


async def example_5_tracing():
    """Example 5: Distributed tracing."""
    print("\n" + "=" * 60)
    print("Example 5: Distributed Tracing")
    print("=" * 60)

    tracer = get_tracer("nexus-example")

    # Record traces
    async with tracer.start_span("process_request", {"user_id": "123"}) as span:
        span.add_event("started_processing")

        # Nested span
        async with tracer.start_span("call_ai_provider", {"provider": "openai"}) as child:
            await asyncio.sleep(0.1)  # Simulate work
            child.set_attribute("tokens", 500)

        span.add_event("completed_processing")

    # Get span info
    print("\nSpan structure:")
    print("""
    process_request (parent span)
    ├── attributes: {user_id: "123", service.name: "nexus-example"}
    ├── events: [started_processing, completed_processing]
    └── call_ai_provider (child span)
        └── attributes: {provider: "openai", tokens: 500}
""")

    print("""
Usage:

    tracer = get_tracer("my-service")

    async with tracer.start_span("my_operation") as span:
        span.set_attribute("key", "value")
        span.add_event("checkpoint")

        # Nested operations create child spans
        async with tracer.start_span("sub_operation"):
            await do_work()
""")


async def example_6_redis_sessions():
    """Example 6: Redis distributed sessions."""
    print("\n" + "=" * 60)
    print("Example 6: Redis Distributed Sessions")
    print("=" * 60)

    print("""
For distributed deployments, use Redis for session storage:

    from nexus.web import RedisSessionStore, create_session_store

    # Create Redis session store
    store = RedisSessionStore(
        redis_url="redis://localhost:6379",
        prefix="nexus:session:",
        default_ttl=86400,  # 24 hours
        max_sessions_per_user=10,
    )

    # Or use factory function
    store = create_session_store(
        backend="redis",
        redis_url="redis://localhost:6379",
    )

    # Use with WebConnector
    async with store:
        session = await store.create_session(
            session_id="sess_123",
            provider="openai",
            model="gpt-4o",
            user_id="user_456",
        )

        # Add messages
        await store.add_message(session.session_id, {
            "role": "user",
            "content": "Hello!"
        })

        # Get session
        session = await store.get_session("sess_123")

        # List user's sessions
        sessions = await store.list_sessions(user_id="user_456")

Features:
- Distributed storage across multiple instances
- Automatic session expiration (TTL)
- Session locking for concurrent access
- Pub/sub for session events
- Max sessions per user enforcement
""")


async def example_7_full_production_setup():
    """Example 7: Full production setup."""
    print("\n" + "=" * 60)
    print("Example 7: Full Production Setup")
    print("=" * 60)

    print("""
Complete production configuration:

    from nexus import (
        NexusConnector,
        RETRY_CONFIGS,
        get_rate_limiter,
        get_metrics,
    )
    from nexus.core.retry import CircuitBreaker

    # Set up monitoring
    metrics = get_metrics()

    # Set up circuit breaker
    circuit_breaker = CircuitBreaker("openai")

    # Set up rate limiter
    rate_limiter = get_rate_limiter("openai")

    # Create connector with all features
    connector = NexusConnector(
        router="auto",               # Smart routing
        fallback_enabled=True,       # Auto-fallback
        on_error=lambda e: metrics.record_error(str(e)),
    )

    # Wrap requests with production hardening
    async def production_request(message: str):
        # Check rate limit
        if not await rate_limiter.acquire_request(timeout=30):
            raise RateLimitExceeded("openai")

        # Check circuit breaker
        if not await circuit_breaker.can_execute():
            raise CircuitOpenError("openai")

        start = time.time()
        try:
            response = await connector.send_message(message)

            # Record success
            await circuit_breaker.record_success()
            await metrics.record_request(
                provider=response["provider"],
                model=connector.connector.model,
                success=True,
                duration_seconds=time.time() - start,
                input_tokens=response["usage"].get("input_tokens", 0),
                output_tokens=response["usage"].get("output_tokens", 0),
            )

            return response

        except Exception as e:
            await circuit_breaker.record_failure(str(e))
            await metrics.record_request(
                provider="openai",
                model="unknown",
                success=False,
                duration_seconds=time.time() - start,
            )
            raise
""")


async def main():
    """Run all examples."""
    print("Nexus Production Hardening Examples")
    print("====================================")
    print()
    print("Production features for enterprise reliability:")
    print("  - Retry with exponential backoff + jitter")
    print("  - Circuit breaker to prevent cascade failures")
    print("  - Rate limiting (requests + tokens)")
    print("  - Prometheus metrics")
    print("  - Distributed tracing")
    print("  - Redis distributed sessions")
    print()

    await example_1_retry_logic()
    await example_2_circuit_breaker()
    await example_3_rate_limiting()
    await example_4_metrics()
    await example_5_tracing()
    await example_6_redis_sessions()
    await example_7_full_production_setup()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
