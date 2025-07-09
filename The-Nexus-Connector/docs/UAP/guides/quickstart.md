# Quick Start Guide

Get up and running with the UAP Framework in minutes! This guide will walk you through installation, basic setup, and your first multi-agent workflow.

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install uap-framework
```

### Option 2: Install from Source

```bash
git clone https://github.com/your-org/uap-framework.git
cd uap-framework
pip install -e .
```

### Verify Installation

```bash
python -c "import uap_core; print('UAP Framework installed successfully!')"
```

## Basic Setup

### 1. Create Your First Agent

Let's start by creating a simple text generation agent using OpenAI:

```python
# my_first_agent.py
import asyncio
from uap_core.models import Task, TaskType
from uap_orchestration.registry import MemoryAgentRegistry
from uap_orchestration.router import TaskRouter
from uap_orchestration.discovery import AgentDiscovery
from uap_adapters.openai_adapter import OpenAIAdapter

async def main():
    # Initialize the framework components
    registry = MemoryAgentRegistry()
    discovery = AgentDiscovery(registry)
    router = TaskRouter(registry=registry, discovery=discovery)
    
    # Create and register an OpenAI agent
    openai_agent = OpenAIAdapter(
        agent_id="gpt-4-assistant",
        api_key="your-openai-api-key",  # Replace with your API key
        model="gpt-4"
    )
    
    # Register the agent
    await registry.register_agent(openai_agent.get_agent_info())
    
    # Create a simple task
    task = Task(
        id="hello-world-task",
        type=TaskType.TEXT_GENERATION,
        prompt="Write a friendly greeting for a new user of the UAP Framework"
    )
    
    # Execute the task
    result = await router.route_task(task)
    
    # Print the result
    print(f"Agent: {result.agent_id}")
    print(f"Output: {result.output}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Cost: ${result.cost:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Run Your First Agent

```bash
python my_first_agent.py
```

Expected output:
```
Agent: gpt-4-assistant
Output: Welcome to the UAP Framework! We're excited to help you orchestrate powerful AI agents...
Duration: 2.34s
Cost: $0.0023
```

## Multiple Agents

### Adding More Agents

```python
# multi_agent_example.py
import asyncio
from uap_core.models import Task, TaskType
from uap_orchestration.registry import MemoryAgentRegistry
from uap_orchestration.router import TaskRouter, RoutingStrategy
from uap_orchestration.discovery import AgentDiscovery
from uap_adapters.openai_adapter import OpenAIAdapter
from uap_adapters.claude_adapter import ClaudeAdapter

async def setup_agents():
    # Initialize framework
    registry = MemoryAgentRegistry()
    discovery = AgentDiscovery(registry)
    router = TaskRouter(
        registry=registry, 
        discovery=discovery,
        strategy=RoutingStrategy.BEST_MATCH  # Use best matching agent
    )
    
    # Add OpenAI agent (good for general tasks)
    openai_agent = OpenAIAdapter(
        agent_id="gpt-4-general",
        api_key="your-openai-api-key",
        model="gpt-4"
    )
    await registry.register_agent(openai_agent.get_agent_info())
    
    # Add Claude agent (good for analysis and reasoning)
    claude_agent = ClaudeAdapter(
        agent_id="claude-analyst",
        api_key="your-anthropic-api-key",
        model="claude-3-sonnet-20240229"
    )
    await registry.register_agent(claude_agent.get_agent_info())
    
    return router

async def main():
    router = await setup_agents()
    
    # Create different types of tasks
    tasks = [
        Task(
            id="creative-task",
            type=TaskType.CREATIVE_WRITING,
            prompt="Write a short story about AI agents working together"
        ),
        Task(
            id="analysis-task",
            type=TaskType.DATA_ANALYSIS,
            prompt="Analyze the benefits of multi-agent systems in AI"
        ),
        Task(
            id="code-task",
            type=TaskType.CODE_GENERATION,
            prompt="Write a Python function to calculate fibonacci numbers"
        )
    ]
    
    # Execute tasks and see which agent handles each
    for task in tasks:
        result = await router.route_task(task)
        print(f"\nTask: {task.id}")
        print(f"Handled by: {result.agent_id}")
        print(f"Output preview: {result.output[:100]}...")
        print(f"Duration: {result.duration:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

## Your First Workflow

### Creating a Multi-Step Workflow

```python
# workflow_example.py
import asyncio
from uap_orchestration.workflows import WorkflowBuilder, WorkflowEngine
from uap_orchestration.registry import MemoryAgentRegistry
from uap_orchestration.router import TaskRouter
from uap_orchestration.discovery import AgentDiscovery
from uap_adapters.openai_adapter import OpenAIAdapter

async def create_blog_post_workflow():
    # Setup framework
    registry = MemoryAgentRegistry()
    discovery = AgentDiscovery(registry)
    router = TaskRouter(registry=registry, discovery=discovery)
    workflow_engine = WorkflowEngine(registry, router)
    
    # Add an agent
    agent = OpenAIAdapter(
        agent_id="content-creator",
        api_key="your-openai-api-key",
        model="gpt-4"
    )
    await registry.register_agent(agent.get_agent_info())
    
    # Define the workflow
    workflow = (WorkflowBuilder()
        .set_name("Blog Post Creation")
        .set_description("Create a complete blog post from a topic")
        
        # Step 1: Research the topic
        .add_step(
            name="research",
            task_template={
                "type": "research",
                "prompt": "Research the topic '{topic}' and provide key points and insights"
            }
        )
        
        # Step 2: Create an outline
        .add_step(
            name="outline",
            task_template={
                "type": "text_generation",
                "prompt": "Create a detailed blog post outline based on this research: ${step_research.result.output}"
            },
            dependencies=["research"]  # Wait for research to complete
        )
        
        # Step 3: Write the introduction
        .add_step(
            name="introduction",
            task_template={
                "type": "creative_writing",
                "prompt": "Write an engaging introduction for a blog post with this outline: ${step_outline.result.output}"
            },
            dependencies=["outline"]
        )
        
        # Step 4: Write the main content
        .add_step(
            name="main_content",
            task_template={
                "type": "creative_writing",
                "prompt": "Write the main content sections based on this outline: ${step_outline.result.output}"
            },
            dependencies=["outline"]
        )
        
        # Step 5: Write the conclusion (depends on both intro and main content)
        .add_step(
            name="conclusion",
            task_template={
                "type": "creative_writing",
                "prompt": "Write a compelling conclusion that ties together the introduction and main content:\n\nIntro: ${step_introduction.result.output}\n\nMain: ${step_main_content.result.output}"
            },
            dependencies=["introduction", "main_content"]
        )
        
        .build())
    
    return workflow_engine, workflow

async def main():
    workflow_engine, workflow = await create_blog_post_workflow()
    
    # Set the topic for the blog post
    workflow.context["topic"] = "The Future of AI in Healthcare"
    
    # Execute the workflow
    print("Starting blog post creation workflow...")
    workflow_id = await workflow_engine.execute_workflow(workflow)
    
    # Wait for completion
    while not workflow.is_complete() and not workflow.has_failed():
        await asyncio.sleep(1)
        print(f"Workflow status: {workflow.status.value}")
    
    # Print results
    if workflow.is_complete():
        print("\n🎉 Blog post created successfully!")
        print("\n" + "="*50)
        
        for step in workflow.steps:
            if step.result and step.result.output:
                print(f"\n## {step.name.title()}")
                print("-" * 30)
                print(step.result.output)
    else:
        print(f"❌ Workflow failed: {workflow.status}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Monitoring Your Agents

### Basic Monitoring Setup

```python
# monitoring_example.py
import asyncio
from uap_monitor.monitor import AgentMonitor, SystemMonitor
from uap_monitor.metrics import MetricsCollector
from uap_orchestration.registry import MemoryAgentRegistry
from uap_adapters.openai_adapter import OpenAIAdapter

async def setup_monitoring():
    # Initialize components
    registry = MemoryAgentRegistry()
    metrics_collector = MetricsCollector()
    
    # Create monitors
    agent_monitor = AgentMonitor(registry, metrics_collector)
    system_monitor = SystemMonitor(metrics_collector)
    
    # Add an agent to monitor
    agent = OpenAIAdapter(
        agent_id="monitored-agent",
        api_key="your-openai-api-key",
        model="gpt-3.5-turbo"
    )
    await registry.register_agent(agent.get_agent_info())
    
    # Start monitoring
    await agent_monitor.start()
    await system_monitor.start()
    
    return agent_monitor, system_monitor, metrics_collector

async def main():
    agent_monitor, system_monitor, metrics_collector = await setup_monitoring()
    
    try:
        # Let monitoring run for a bit
        print("Monitoring started. Collecting metrics for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get some metrics
        recent_metrics = await metrics_collector.get_recent_metrics(limit=10)
        print(f"\nCollected {len(recent_metrics)} metrics")
        
        # Get agent metrics
        agent_metrics = await agent_monitor.get_all_agent_metrics()
        for agent_id, metrics in agent_metrics.items():
            print(f"\nAgent {agent_id}:")
            print(f"  Status: {metrics.get('status', 'unknown')}")
            print(f"  Tasks completed: {metrics.get('tasks_completed', 0)}")
            print(f"  Average response time: {metrics.get('avg_response_time', 0):.2f}s")
        
        # Get system metrics
        system_metrics = await system_monitor.get_system_metrics()
        print(f"\nSystem Metrics:")
        print(f"  CPU Usage: {system_metrics.get('cpu_percent', 0):.1f}%")
        print(f"  Memory Usage: {system_metrics.get('memory_percent', 0):.1f}%")
        
    finally:
        # Clean up
        await agent_monitor.stop()
        await system_monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Environment Variables

Create a `.env` file for your API keys:

```bash
# .env
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here

# Optional: Redis for production
REDIS_URL=redis://localhost:6379/0

# Optional: Database for persistence
DATABASE_URL=postgresql://user:password@localhost:5432/uap_db
```

### Configuration File

Create a `config.yaml` file:

```yaml
# config.yaml
agents:
  timeout: 300  # 5 minutes
  max_concurrent: 10
  retry_attempts: 3

routing:
  strategy: "best_match"  # round_robin, least_loaded, best_match, cost_optimized
  load_balancing: true

monitoring:
  enabled: true
  metrics_interval: 60  # seconds
  health_check_interval: 30

logging:
  level: "INFO"
  format: "json"
  file: "uap.log"

security:
  rate_limit: 100  # requests per minute
  require_auth: false  # Set to true for production
```

### Using Configuration

```python
# config_example.py
import asyncio
from uap_core.config import ConfigManager
from uap_orchestration.registry import MemoryAgentRegistry
from uap_orchestration.router import TaskRouter

async def main():
    # Load configuration
    config = ConfigManager()
    config.load_from_file("config.yaml")
    config.load_from_env()  # Load from environment variables
    
    # Use configuration
    timeout = config.get_int("agents.timeout", 300)
    strategy = config.get("routing.strategy", "round_robin")
    
    print(f"Agent timeout: {timeout}s")
    print(f"Routing strategy: {strategy}")
    
    # Initialize components with configuration
    registry = MemoryAgentRegistry()
    router = TaskRouter(
        registry=registry,
        timeout=timeout,
        strategy=strategy
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Your Setup

### Run the Test Suite

```bash
# Run all tests
python -m pytest tests/

# Run specific test types
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/examples/      # Example workflows

# Run with coverage
python -m pytest tests/ --cov=uap_core --cov=uap_orchestration
```

### Performance Testing

```python
# performance_test.py
import asyncio
import time
from uap_core.models import Task, TaskType
from uap_orchestration.registry import MemoryAgentRegistry
from uap_orchestration.router import TaskRouter
from uap_adapters.openai_adapter import OpenAIAdapter

async def performance_test():
    # Setup
    registry = MemoryAgentRegistry()
    router = TaskRouter(registry=registry)
    
    # Add multiple agents for load balancing
    for i in range(3):
        agent = OpenAIAdapter(
            agent_id=f"perf-agent-{i}",
            api_key="your-openai-api-key",
            model="gpt-3.5-turbo"
        )
        await registry.register_agent(agent.get_agent_info())
    
    # Create test tasks
    tasks = [
        Task(
            id=f"perf-task-{i}",
            type=TaskType.TEXT_GENERATION,
            prompt=f"Generate a short message #{i}"
        )
        for i in range(10)
    ]
    
    # Measure performance
    start_time = time.time()
    
    # Execute tasks concurrently
    results = await asyncio.gather(*[
        router.route_task(task) for task in tasks
    ])
    
    end_time = time.time()
    
    # Calculate metrics
    total_time = end_time - start_time
    successful_tasks = sum(1 for r in results if r.status.value == "success")
    throughput = len(tasks) / total_time
    
    print(f"Performance Test Results:")
    print(f"  Total tasks: {len(tasks)}")
    print(f"  Successful: {successful_tasks}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {throughput:.2f} tasks/second")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

## Next Steps

### 1. Explore Advanced Features

- **Security**: Set up authentication and authorization
- **Workflows**: Create complex multi-agent workflows
- **Monitoring**: Set up comprehensive monitoring and alerting
- **Optimization**: Use the agent optimizer for performance learning

### 2. Production Deployment

- Follow the [Production Deployment Guide](../deployment/production.md)
- Set up proper monitoring and logging
- Configure security and authentication
- Implement backup and recovery procedures

### 3. Custom Integrations

- Build custom agent adapters for your AI services
- Create custom routing strategies
- Implement custom metrics and monitoring

### 4. Community and Support

- Check out the [examples directory](../examples/) for more use cases
- Read the [API documentation](../api/) for detailed reference
- Join our community discussions
- Contribute to the project

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Make sure UAP is installed
pip install uap-framework

# Check Python path
python -c "import sys; print(sys.path)"
```

**API Key Issues:**
```python
# Verify your API keys
import openai
openai.api_key = "your-key"
print(openai.Model.list())  # Should list available models
```

**Connection Issues:**
```bash
# Check Redis connection (if using)
redis-cli ping

# Check database connection (if using)
psql -h localhost -U username -d database_name
```

**Performance Issues:**
- Start with fewer concurrent tasks
- Use appropriate agent timeouts
- Monitor system resources
- Check network connectivity to AI services

### Getting Help

- **Documentation**: Check the [full documentation](../README.md)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/your-org/uap-framework/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/your-org/uap-framework/discussions)
- **Email**: Contact support@uap-framework.org

Congratulations! You now have a working UAP Framework setup. Start building amazing multi-agent applications! 🚀

