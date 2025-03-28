# LLM Provider System

The LLM Provider system in MyCoder-Py is designed to create a consistent interface for interacting with different large language model APIs. This document covers the design, usage, and extension of this system.

## Overview

The LLM Provider system consists of:

- **Abstract base class** (`LLMProvider`) that defines the interface
- **Model classes** for messages, tool calls, and responses
- **Provider implementations** for specific LLM APIs (OpenAI, etc.)
- **Exception handling** for various error conditions
- **Factory functions** for creating provider instances

## Core Components

### Base Classes and Models

- `LLMProvider` - Abstract base class that all providers must implement
- `Message` - Represents a message in a conversation
- `MessageRole` - Enum of possible message roles (system, user, assistant, tool)
- `ToolCall` - Represents a tool call from the LLM
- `LLMResponse` - Wraps responses from the LLM

### Provider Implementations

- `OpenAIProvider` - Implementation for OpenAI's API (GPT models)
- `AnthropicProvider` - Implementation for Anthropic's API (Claude models)
- Ollama support planned for future versions

### Exception Handling

Specialized exceptions for different error scenarios:

- `LLMError` - Base exception for all LLM-related errors
- `ProviderAPIError` - API errors from providers
- `ProviderRateLimitError` - Rate limit exceeded errors
- `ProviderAuthenticationError` - Authentication failures
- `ContextLengthExceededError` - Token limit exceeded
- `ContentFilterError` - Content policy violations

## Usage Examples

### Basic Usage

```python
from mycoder.agent.llm import create_provider, Message, MessageRole

# Create a provider instance
provider = create_provider("openai", model="gpt-4")

# Create messages
messages = [
    Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    Message(role=MessageRole.USER, content="Hello, who are you?")
]

# Generate a response
response = await provider.generate(messages)

# Access the response content
print(response.message.content)
```

### Using Tools

```python
from mycoder.agent.llm import create_provider, Message, MessageRole
from mycoder.agent.tools import get_default_tools

# Create a provider
provider = create_provider("openai")

# Get tool schemas
tools = []
for tool_class in get_default_tools():
    tool = tool_class()
    tools.append(tool.get_schema_for_llm("openai"))

# Generate response with tools
response = await provider.generate(messages, tools=tools)

# Check if response contains tool calls
if response.message.is_tool_call():
    for tool_call in response.message.tool_calls:
        print(f"Tool call: {tool_call.name}")
        print(f"Arguments: {tool_call.arguments}")
```

## Token Counting

The LLM Provider system includes utilities for token counting:

```python
# Count tokens in a string
token_count = provider.count_tokens("This is a test message.")

# Count tokens in a list of messages
total_tokens = provider.count_message_tokens(messages)
```

## Implementing a New Provider

To add a new LLM provider:

1. Create a new module in `mycoder/agent/llm/`
2. Implement the `LLMProvider` abstract class
3. Add imports and registry in `__init__.py`

Example skeleton for a new provider:

```python
from .base import LLMProvider, LLMResponse, Message

class NewProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "new_provider"
    
    @property
    def model_name(self) -> str:
        return self.config.model
    
    @property
    def context_window(self) -> int:
        return 8192  # Default value
    
    async def generate(self, messages, tools=None, temperature=0.7, max_tokens=None):
        # Implementation here
        pass
    
    def count_tokens(self, text):
        # Implementation here
        pass
```

## Configuration

Providers can be configured through:

1. Direct initialization of provider classes
2. Factory functions like `create_openai_provider()`
3. Generic factory function `create_provider()`
4. Environment variables (e.g., OPENAI_API_KEY)

See the `.env.example` file for configuration options.

## Using Different Providers

MyCoder-Py makes it easy to switch between different LLM providers:

```python
from mycoder.agent.llm import create_provider, Message, MessageRole

# Create an OpenAI provider
openai_provider = create_provider("openai", model="gpt-4")

# Create an Anthropic provider
anthropic_provider = create_provider("anthropic", model="claude-3-sonnet-20240229")

# Use the providers
openai_response = await openai_provider.generate(messages)
anthropic_response = await anthropic_provider.generate(messages)
```

You can also choose the provider dynamically at runtime:

```python
def get_provider_for_task(task_type):
    if task_type == "coding":
        return create_provider("openai", model="gpt-4")
    elif task_type == "creative":
        return create_provider("anthropic", model="claude-3-opus-20240229")
    else:
        return create_provider("openai", model="gpt-3.5-turbo")
```

See `docs/examples/provider_switching.md` for more detailed examples.

## Model Context Protocol (MCP)

MyCoder-Py includes support for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), which allows AI assistants to access external context sources and tools during conversations. The MCP implementation provides:

1. Client for connecting to MCP servers
2. Tools for listing and retrieving resources from MCP servers
3. Integration with both OpenAI and Anthropic providers

### Configuring MCP Servers

MCP servers can be configured in your settings:

```python
from mycoder.settings.config import MCPServer, MCPServerAuth, MCPSettings, Settings

# Create MCP server configurations
mcp_settings = MCPSettings(
    servers=[
        MCPServer(
            name="docs",
            url="http://localhost:3000",
            auth=MCPServerAuth(
                type="bearer",
                token="your-token-here"
            )
        )
    ],
    default_resources=["docs://api/reference"],
    default_tools=["docs://search"]
)

# Use in settings
settings = Settings(mcp=mcp_settings)
```

### Using MCP in Your Code

```python
from mycoder.agent.mcp import MCPClient, MCPResource

async def get_documentation():
    # Create an MCP client
    server_config = settings.mcp.servers[0]
    async with MCPClient(server_config) as client:
        # List available resources
        resources = await client.list_resources()
        
        # Get a specific resource
        doc = await client.get_resource("docs://api/methods/create")
        
        # Use the resource content
        print(doc.content)
``` 