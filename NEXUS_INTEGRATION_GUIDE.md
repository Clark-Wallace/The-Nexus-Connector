# The Nexus Connector Integration Guide
*Universal AI Integration for Any Project - Updated v0.2.0*

## What is The Nexus Connector?

The Nexus Connector is a production-ready universal AI interface that transforms any AI provider (OpenAI, Anthropic, Google, xAI, DeepSeek, Ollama) into stateful, autonomous CLI tools with persistent sessions. It's designed to integrate seamlessly into existing projects without disrupting your current workflow.

## Quick Start (5 Minutes)

### For New Projects

```bash
# Create new project
mkdir my-ai-project && cd my-ai-project

# Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install The Nexus Connector
pip install git+https://github.com/Clark-Wallace/The-Nexus-Connector.git

# Create your first autonomous AI script
cat > main.py << 'EOF'
import asyncio
import os
from nexus import NexusConnector, AIProvider

async def main():
    # Create autonomous AI agent
    connector = NexusConnector(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        workspace="./output",
        auto_execute=True,
        max_iterations=10
    )
    
    # Give it a complex task
    task = """
    Create a Python web scraper that:
    1. Fetches data from a public API
    2. Processes and cleans the data
    3. Saves results to both JSON and CSV
    4. Includes comprehensive error handling
    5. Add logging and progress tracking
    """
    
    result = await connector.execute_task(task)
    
    print(f"✅ Task completed: {result.success}")
    print(f"📁 Files created: {', '.join(result.files_created)}")
    print(f"💰 Total cost: ${connector.total_cost:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Set your API key and run
export ANTHROPIC_API_KEY="your-api-key-here"
python main.py
```

### For Existing Projects

```bash
# Navigate to your existing project
cd /path/to/your/existing/project

# Install The Nexus Connector
pip install git+https://github.com/Clark-Wallace/The-Nexus-Connector.git

# Add to requirements.txt
echo "git+https://github.com/Clark-Wallace/The-Nexus-Connector.git" >> requirements.txt
```

## Core Integration Patterns

### 1. Basic AI Assistant Module

Create `ai_assistant.py` in your project:

```python
import os
import asyncio
from typing import Dict, Any, Optional
from nexus import NexusConnector, AIProvider, TaskResult

class ProjectAI:
    """AI assistant for your project with production-ready features"""
    
    def __init__(self, provider: AIProvider = AIProvider.ANTHROPIC):
        self.connector = NexusConnector(
            provider=provider,
            api_key=self._get_api_key(provider),
            workspace="./ai_output",
            auto_execute=True,
            max_iterations=10,
            verbose=True,
            safe_mode=True  # Confirms destructive operations
        )
    
    def _get_api_key(self, provider: AIProvider) -> str:
        """Get API key for provider from environment"""
        key_map = {
            AIProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            AIProvider.OPENAI: "OPENAI_API_KEY",
            AIProvider.GOOGLE: "GOOGLE_API_KEY",
            AIProvider.XAI: "XAI_API_KEY",
            AIProvider.DEEPSEEK: "DEEPSEEK_API_KEY"
        }
        return os.getenv(key_map[provider])
    
    async def analyze_codebase(self, focus_area: Optional[str] = None) -> TaskResult:
        """Comprehensive codebase analysis"""
        task = f"""
        Perform a comprehensive analysis of this codebase:
        
        1. **Code Quality Assessment**
           - Identify potential bugs and security issues
           - Check code style and consistency
           - Find dead code and unused imports
        
        2. **Performance Analysis**
           - Identify performance bottlenecks
           - Suggest optimization opportunities
           - Analyze memory usage patterns
        
        3. **Architecture Review**
           - Assess overall structure and design patterns
           - Identify coupling and cohesion issues
           - Suggest architectural improvements
        
        4. **Documentation Gap Analysis**
           - Find undocumented functions and classes
           - Identify missing docstrings
           - Suggest README improvements
        
        {f"5. **Focus Area: {focus_area}**" if focus_area else ""}
        
        Create a comprehensive report with actionable recommendations.
        """
        return await self.connector.execute_task(task)
    
    async def generate_tests(self, file_or_module: str) -> TaskResult:
        """Generate comprehensive test suite"""
        task = f"""
        Create a comprehensive test suite for {file_or_module}:
        
        1. **Unit Tests**
           - Test all public methods and functions
           - Include edge cases and error conditions
           - Mock external dependencies
        
        2. **Integration Tests**
           - Test component interactions
           - Test API endpoints if applicable
           - Test database operations if applicable
        
        3. **Test Infrastructure**
           - Set up proper test fixtures
           - Configure test database/environment
           - Add test utilities and helpers
        
        4. **Test Coverage**
           - Aim for 90%+ code coverage
           - Focus on critical business logic
           - Document any intentionally untested code
        
        Use the appropriate testing framework for this project.
        """
        return await self.connector.execute_task(task)
    
    async def refactor_code(self, target: str, requirements: str) -> TaskResult:
        """Intelligent code refactoring"""
        task = f"""
        Refactor {target} with these requirements:
        {requirements}
        
        Guidelines:
        1. **Preserve Functionality** - Maintain all existing behavior
        2. **Improve Structure** - Apply SOLID principles and clean code practices
        3. **Enhance Readability** - Use clear variable names and add documentation
        4. **Add Error Handling** - Implement robust error handling and logging
        5. **Maintain Compatibility** - Ensure backward compatibility where possible
        6. **Add Type Hints** - Include comprehensive type annotations
        
        Create before/after comparisons and explain all changes.
        """
        return await self.connector.execute_task(task)
    
    async def create_documentation(self, doc_type: str = "comprehensive") -> TaskResult:
        """Generate project documentation"""
        templates = {
            "api": "Create API documentation with endpoints, parameters, and examples",
            "user": "Create user-facing documentation with tutorials and guides",
            "developer": "Create developer documentation with setup and contribution guides",
            "comprehensive": """
            Create comprehensive project documentation:
            
            1. **README.md** - Project overview, installation, and quick start
            2. **API Documentation** - Detailed API reference with examples
            3. **User Guide** - Step-by-step tutorials and common use cases
            4. **Developer Guide** - Setup, contribution guidelines, and architecture
            5. **Deployment Guide** - Production deployment instructions
            6. **Troubleshooting** - Common issues and solutions
            """
        }
        
        task = templates.get(doc_type, templates["comprehensive"])
        return await self.connector.execute_task(task)
    
    async def optimize_performance(self, target_area: Optional[str] = None) -> TaskResult:
        """Performance optimization analysis and implementation"""
        task = f"""
        Analyze and optimize performance for this project:
        
        1. **Profiling**
           - Identify CPU and memory bottlenecks
           - Analyze database query performance
           - Check I/O operations efficiency
        
        2. **Optimization Strategies**
           - Implement caching where appropriate
           - Optimize database queries and indexes
           - Improve algorithm efficiency
           - Add async/await where beneficial
        
        3. **Monitoring Setup**
           - Add performance metrics collection
           - Implement health checks
           - Set up alerting for performance issues
        
        {f"4. **Focus on: {target_area}**" if target_area else ""}
        
        Provide before/after performance comparisons and monitoring setup.
        """
        return await self.connector.execute_task(task)
```

### 2. Web Application Integration

```python
# web_ai.py - FastAPI/Flask integration
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ai_assistant import ProjectAI
import asyncio

app = FastAPI(title="AI-Enhanced Web App")
ai_assistant = ProjectAI()

class CodeAnalysisRequest(BaseModel):
    focus_area: str = None
    file_path: str = None

class TaskRequest(BaseModel):
    description: str
    priority: str = "normal"

@app.post("/ai/analyze")
async def analyze_code(request: CodeAnalysisRequest):
    """AI-powered code analysis endpoint"""
    try:
        if request.file_path:
            result = await ai_assistant.generate_tests(request.file_path)
        else:
            result = await ai_assistant.analyze_codebase(request.focus_area)
        
        return {
            "success": result.success,
            "files_created": result.files_created,
            "summary": result.output,
            "cost": f"${ai_assistant.connector.total_cost:.4f}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/task")
async def execute_ai_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Execute custom AI task"""
    async def run_task():
        return await ai_assistant.connector.execute_task(request.description)
    
    # For long-running tasks, use background processing
    if request.priority == "background":
        background_tasks.add_task(run_task)
        return {"message": "Task started in background"}
    else:
        result = await run_task()
        return {"success": result.success, "output": result.output}

# Built-in web server mode (alternative approach)
from nexus.web import WebConnector

async def start_ai_web_server():
    """Use Nexus's built-in web server"""
    web_connector = WebConnector(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        port=8000
    )
    await web_connector.start_server()

# Run with: asyncio.run(start_ai_web_server())
```

### 3. CLI Application Enhancement

```python
# cli_ai.py - Click/Typer integration
import click
import asyncio
from rich.console import Console
from rich.progress import Progress
from ai_assistant import ProjectAI

console = Console()
ai = ProjectAI()

@click.group()
def cli():
    """Your existing CLI enhanced with AI superpowers"""
    pass

@cli.command()
@click.option('--focus', help='Focus area for analysis')
@click.option('--output', default='analysis_report.md', help='Output file')
def analyze(focus, output):
    """AI-powered code analysis"""
    async def run_analysis():
        with Progress() as progress:
            task = progress.add_task("Analyzing codebase...", total=100)
            
            result = await ai.analyze_codebase(focus)
            progress.update(task, completed=100)
            
            if result.success:
                console.print(f"✅ Analysis complete! Report saved to {result.files_created}", style="green")
                console.print(f"💰 Cost: ${ai.connector.total_cost:.4f}")
            else:
                console.print("❌ Analysis failed", style="red")
    
    asyncio.run(run_analysis())

@cli.command()
@click.argument('target')
@click.option('--requirements', prompt='Refactoring requirements', help='What to improve')
def refactor(target, requirements):
    """AI-powered code refactoring"""
    async def run_refactor():
        console.print(f"🔄 Refactoring {target}...")
        result = await ai.refactor_code(target, requirements)
        
        if result.success:
            console.print("✅ Refactoring complete!", style="green")
            for file in result.files_created:
                console.print(f"📝 Modified: {file}")
        else:
            console.print("❌ Refactoring failed", style="red")
    
    asyncio.run(run_refactor())

@cli.command()
@click.option('--type', default='comprehensive', help='Documentation type')
def docs(type):
    """Generate AI-powered documentation"""
    async def generate_docs():
        console.print("📚 Generating documentation...")
        result = await ai.create_documentation(type)
        
        if result.success:
            console.print("✅ Documentation generated!", style="green")
        else:
            console.print("❌ Documentation generation failed", style="red")
    
    asyncio.run(generate_docs())

if __name__ == '__main__':
    cli()
```

### 4. Game Development Integration

```python
# game_ai.py - Game Master and content generation
from nexus.connectors import GMConnector
from nexus import NexusConnector, AIProvider
import asyncio

class GameAI:
    """AI assistant for game development"""
    
    def __init__(self):
        # General purpose AI
        self.ai = NexusConnector(
            provider=AIProvider.ANTHROPIC,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            workspace="./game_content"
        )
        
        # Specialized Game Master AI
        self.gm = GMConnector(
            provider=AIProvider.ANTHROPIC,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            game_system="D20 Narrative Hybrid"
        )
    
    async def generate_content(self, content_type: str, theme: str, parameters: dict):
        """Generate game content dynamically"""
        task = f"""
        Generate {content_type} for a {theme} game with these parameters:
        {parameters}
        
        Requirements:
        1. **Balanced and Fair** - Ensure gameplay balance
        2. **Engaging Content** - Create interesting and varied content
        3. **Replayability** - Add variety for multiple playthroughs
        4. **Technical Integration** - Format for easy code integration
        5. **Thematic Consistency** - Match the {theme} setting
        
        Include JSON data structures for easy parsing.
        """
        return await self.ai.execute_task(task)
    
    async def run_game_session(self, session_data: dict):
        """Run an AI-powered game session"""
        response = await self.gm.process_action({
            "session_id": session_data["session_id"],
            "player_action": session_data["action"],
            "game_state": session_data["state"],
            "character": session_data["character"]
        })
        
        return {
            "narrative": response.narrative,
            "choices": response.suggested_actions,
            "dice_roll": response.requires_roll,
            "state_updates": response.state_changes
        }
    
    async def balance_mechanics(self, config_file: str):
        """Analyze and balance game mechanics"""
        task = f"""
        Analyze game balance in {config_file}:
        
        1. **Mathematical Analysis**
           - Calculate expected values and probabilities
           - Identify overpowered/underpowered elements
           - Check for dominant strategies
        
        2. **Balance Adjustments**
           - Suggest specific numerical changes
           - Maintain fun factor and player agency
           - Consider different player skill levels
        
        3. **Testing Scenarios**
           - Create test cases for balance verification
           - Simulate different gameplay scenarios
           - Provide metrics for ongoing balance monitoring
        """
        return await self.ai.execute_task(task)

# Example usage
async def enhance_rpg_game():
    game_ai = GameAI()
    
    # Generate dynamic content
    enemies = await game_ai.generate_content(
        content_type="enemy_encounters",
        theme="cyberpunk",
        parameters={"difficulty": "medium", "count": 10, "environment": "urban"}
    )
    
    # Run game session
    session_result = await game_ai.run_game_session({
        "session_id": "game_123",
        "action": {"text": "I hack into the corporate mainframe"},
        "state": {"location": "Neon Tower", "floor": 42},
        "character": {"name": "Nova", "class": "Netrunner", "level": 5}
    })
    
    print(f"Narrative: {session_result['narrative']}")
    print(f"Player choices: {session_result['choices']}")
```

## Advanced Integration Patterns

### 1. Provider Switching and Fallbacks

```python
class RobustAI:
    """AI with automatic provider fallbacks"""
    
    def __init__(self):
        self.providers = [
            (AIProvider.ANTHROPIC, os.getenv("ANTHROPIC_API_KEY")),
            (AIProvider.OPENAI, os.getenv("OPENAI_API_KEY")),
            (AIProvider.DEEPSEEK, os.getenv("DEEPSEEK_API_KEY"))
        ]
        self.current_connector = None
        self._initialize_connector()
    
    def _initialize_connector(self):
        """Initialize with first available provider"""
        for provider, api_key in self.providers:
            if api_key:
                self.current_connector = NexusConnector(
                    provider=provider,
                    api_key=api_key,
                    auto_execute=True
                )
                break
    
    async def execute_with_fallback(self, task: str) -> TaskResult:
        """Execute task with automatic provider fallback"""
        for provider, api_key in self.providers:
            if not api_key:
                continue
                
            try:
                connector = NexusConnector(
                    provider=provider,
                    api_key=api_key,
                    auto_execute=True,
                    max_iterations=5
                )
                
                result = await connector.execute_task(task)
                if result.success:
                    return result
                    
            except Exception as e:
                print(f"Provider {provider.value} failed: {e}")
                continue
        
        raise Exception("All providers failed")
```

### 2. Batch Processing and Queue Management

```python
import asyncio
from dataclasses import dataclass
from typing import List, Callable
from datetime import datetime

@dataclass
class AITask:
    id: str
    description: str
    priority: int
    callback: Callable = None
    created_at: datetime = datetime.now()

class AITaskQueue:
    """Managed queue for AI tasks with priorities"""
    
    def __init__(self, max_concurrent: int = 3):
        self.queue: List[AITask] = []
        self.running_tasks = {}
        self.max_concurrent = max_concurrent
        self.ai = ProjectAI()
    
    def add_task(self, task: AITask):
        """Add task to queue with priority ordering"""
        self.queue.append(task)
        self.queue.sort(key=lambda t: t.priority, reverse=True)
    
    async def process_queue(self):
        """Process queued tasks with concurrency limits"""
        while self.queue or self.running_tasks:
            # Start new tasks up to concurrency limit
            while (len(self.running_tasks) < self.max_concurrent and self.queue):
                task = self.queue.pop(0)
                asyncio.create_task(self._execute_task(task))
            
            # Wait a bit before checking again
            await asyncio.sleep(1)
    
    async def _execute_task(self, task: AITask):
        """Execute individual task"""
        self.running_tasks[task.id] = task
        
        try:
            result = await self.ai.connector.execute_task(task.description)
            
            if task.callback:
                await task.callback(task, result)
                
        except Exception as e:
            print(f"Task {task.id} failed: {e}")
        
        finally:
            del self.running_tasks[task.id]
```

### 3. Real-time Collaboration Features

```python
# real_time_ai.py - WebSocket-based real-time AI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from nexus.web import WebConnector
import asyncio
import json

app = FastAPI()

class AICollaborationManager:
    """Manage real-time AI collaboration sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.ai = ProjectAI()
    
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket connection for real-time AI"""
        await websocket.accept()
        self.active_sessions[session_id] = websocket
        
        try:
            while True:
                # Receive user input
                data = await websocket.receive_text()
                request = json.loads(data)
                
                # Process with AI
                if request["type"] == "code_analysis":
                    await self._stream_code_analysis(websocket, request["code"])
                elif request["type"] == "task":
                    await self._stream_task_execution(websocket, request["task"])
                
        except WebSocketDisconnect:
            del self.active_sessions[session_id]
    
    async def _stream_code_analysis(self, websocket: WebSocket, code: str):
        """Stream AI analysis in real-time"""
        # Send immediate acknowledgment
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "Analyzing code..."
        }))
        
        # Stream AI response
        async for chunk in self.ai.connector.stream_message(
            f"Analyze this code and provide real-time feedback: {code}"
        ):
            await websocket.send_text(json.dumps({
                "type": "analysis_chunk",
                "content": chunk
            }))
        
        # Send completion
        await websocket.send_text(json.dumps({
            "type": "analysis_complete",
            "message": "Analysis finished"
        }))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    manager = AICollaborationManager()
    await manager.handle_connection(websocket, session_id)
```

## Production Deployment

### 1. Environment Configuration

Create `.env` file:
```bash
# AI Provider Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
XAI_API_KEY=your_xai_key
DEEPSEEK_API_KEY=your_deepseek_key

# AI Configuration
AI_PROVIDER=anthropic
AI_MAX_ITERATIONS=10
AI_AUTO_EXECUTE=true
AI_SAFE_MODE=true
AI_WORKSPACE=./ai_output

# Web Server (if using web mode)
NEXUS_PORT=8000
NEXUS_HOST=0.0.0.0
SESSION_TIMEOUT=3600
```

### 2. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Nexus Connector from GitHub
RUN pip install git+https://github.com/Clark-Wallace/The-Nexus-Connector.git

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-c", "from nexus.web import WebConnector; import asyncio; import os; asyncio.run(WebConnector(provider='anthropic', api_key=os.getenv('ANTHROPIC_API_KEY'), port=8000).start_server())"]
```

### 3. Production Monitoring

```python
# monitoring.py
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class AIMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0

class AIMonitor:
    """Production monitoring for AI operations"""
    
    def __init__(self):
        self.metrics = AIMetrics()
        self.request_times = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('nexus_ai')
    
    async def monitored_execute(self, ai_connector, task: str) -> Dict[str, Any]:
        """Execute AI task with monitoring"""
        start_time = time.time()
        
        try:
            self.metrics.total_requests += 1
            self.logger.info(f"Starting AI task: {task[:100]}...")
            
            result = await ai_connector.execute_task(task)
            
            # Track metrics
            execution_time = time.time() - start_time
            self.request_times.append(execution_time)
            self.metrics.avg_response_time = sum(self.request_times) / len(self.request_times)
            
            if result.success:
                self.metrics.successful_requests += 1
                self.logger.info(f"Task completed successfully in {execution_time:.2f}s")
            else:
                self.metrics.failed_requests += 1
                self.logger.error(f"Task failed after {execution_time:.2f}s")
            
            # Track costs
            if hasattr(ai_connector, 'total_cost'):
                self.metrics.total_cost += ai_connector.total_cost
            
            return {
                "result": result,
                "execution_time": execution_time,
                "metrics": self.metrics
            }
            
        except Exception as e:
            self.metrics.failed_requests += 1
            self.logger.error(f"Task exception: {str(e)}")
            raise
    
    def get_health_check(self) -> Dict[str, Any]:
        """Health check endpoint data"""
        success_rate = (
            self.metrics.successful_requests / self.metrics.total_requests 
            if self.metrics.total_requests > 0 else 0
        )
        
        return {
            "status": "healthy" if success_rate > 0.95 else "degraded",
            "total_requests": self.metrics.total_requests,
            "success_rate": success_rate,
            "avg_response_time": self.metrics.avg_response_time,
            "total_cost": self.metrics.total_cost
        }
```

## Best Practices

### 1. Security and API Key Management
- Store API keys in environment variables or secure key management
- Use different keys for development/staging/production
- Implement rate limiting to prevent abuse
- Monitor API usage and costs

### 2. Error Handling and Resilience
- Implement fallback providers
- Use circuit breakers for failing services
- Cache results when appropriate
- Provide manual alternatives for critical paths

### 3. Cost Management
- Set usage budgets and alerts
- Choose appropriate models for different tasks
- Implement request caching
- Monitor token usage patterns

### 4. Performance Optimization
- Use async/await throughout
- Implement connection pooling
- Cache frequent requests
- Batch similar operations

### 5. Testing AI Integration
- Mock AI responses for unit tests
- Use test-specific API keys with limits
- Test fallback scenarios
- Validate AI output quality

## Migration Checklist

- [ ] Clone/install The Nexus Connector in your project
- [ ] Create AI assistant module with error handling
- [ ] Add environment variables for API keys
- [ ] Update requirements.txt with dependencies
- [ ] Implement basic AI integration in one feature
- [ ] Add monitoring and logging
- [ ] Test with different providers
- [ ] Document AI features for your team
- [ ] Set up production deployment
- [ ] Configure monitoring and alerts

---

*The Nexus Connector v0.2.0 provides production-ready AI integration with session management, web server capabilities, and autonomous task execution. Build once, deploy anywhere, and let AI enhance your applications.*