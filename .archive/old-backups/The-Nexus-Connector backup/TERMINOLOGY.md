# The Nexus Connector - Terminology Guide

## Core Concepts

### The Nexus Connector
The universal AI connection interface that enables seamless interaction with any AI provider.

### Nexus Connection
The active connection established between your application and an AI provider through The Nexus Connector.

## Usage Examples

### Establishing a Connection
```python
# Create a Nexus Connector instance
connector = NexusConnector(provider=AIProvider.OPENAI, api_key="...")

# You now have a Nexus Connection established
```

### Correct Terminology

✅ **DO say:**
- "Establish a Nexus Connection"
- "Connect through The Nexus Connector"
- "The Nexus Connection is active"
- "Send messages via the Nexus Connection"
- "Switch providers while maintaining the Nexus Connection interface"

❌ **DON'T say:**
- "Create a wrapper"
- "Use the unified wrapper"
- "Initialize the wrapper"

## Key Phrases

- **"The Nexus Connector"** - The library/framework itself
- **"Nexus Connection"** - The active connection instance
- **"Establish a Nexus Connection"** - Creating a connection
- **"Through the Nexus Connection"** - Using the connection
- **"Universal connection interface"** - What The Nexus Connector provides

## Example Sentences

1. "The Nexus Connector provides a universal interface for establishing Nexus Connections with any AI provider."

2. "Once you've established a Nexus Connection, you can seamlessly switch between providers without changing your code."

3. "Send your prompts through the Nexus Connection and receive responses in a unified format."

4. "The Nexus Connector handles all provider-specific details, so you can focus on your application logic."

## Import Changes

```python
# Old
from nexus import UnifiedAIWrapper

# New
from nexus import NexusConnector
```

## Class Name Changes

- `UnifiedAIWrapper` → `NexusConnector`
- Instance variable names: `wrapper` → `connector`

This terminology emphasizes the connection-based nature of the interface and creates a more distinctive brand identity.