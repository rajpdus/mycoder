# Tool System

The Tool System in MyCoder-Py provides a structured way for the AI agent to interact with the external world. This document covers the design, usage, and extension of this system.

## Overview

The Tool System consists of:

- **Abstract base class** (`Tool`) that defines the interface for all tools
- **Tool implementations** for various capabilities
- **Schema generation** for LLM function calling
- **ToolManager** for registering and executing tools
- **Factory functions** for creating tools from regular functions

## Core Components

### Base Classes and Models

- `Tool` - Abstract base class that all tools must implement
- Tool-specific argument and result models using Pydantic

### Tool Categories

- **File Operations**
  - `ReadFileTool` - Read content from files
  - `WriteFileTool` - Write content to files
  - `ListDirTool` - List directory contents

- **Shell**
  - `RunCommandTool` - Execute shell commands

- **User Interaction**
  - `UserPromptTool` - Ask the user for input
  - `UserMessageTool` - Display messages to the user

### Tool Manager

The `ToolManager` class handles:
- Tool registration
- Tool retrieval by name
- Schema generation for LLM providers
- Tool execution with error handling

## Usage Examples

### Using the Tool Manager

```python
from mycoder.agent.tool_manager import ToolManager
from mycoder.agent.tools import get_default_tools

# Create a tool manager
tool_manager = ToolManager()

# Register default tools
tool_manager.register_tools(get_default_tools())

# Execute a tool
result = await tool_manager.execute_tool(
    "read_file", 
    {"file_path": "example.txt", "offset": 0, "limit": 10}
)

# Get schemas for an LLM provider
tool_schemas = tool_manager.get_tool_schemas_for_llm("openai")
```

### Direct Tool Usage

```python
from mycoder.agent.tools.file_ops import ReadFileTool

# Create a tool instance
read_tool = ReadFileTool()

# Execute the tool
result = await read_tool.execute(
    file_path="example.txt",
    offset=0,
    limit=10
)

# Get the tool's schema
schema = read_tool.get_schema_for_llm()
```

### Creating a Custom Tool

By subclassing the `Tool` base class:

```python
from pydantic import BaseModel, Field
from mycoder.agent.tools.base import Tool

# Define arguments model
class CalculatorArgs(BaseModel):
    expression: str = Field(
        description="Mathematical expression to evaluate"
    )

# Implement the tool
class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a mathematical expression"
    args_schema = CalculatorArgs
    
    async def run(self, expression: str):
        """Evaluate a mathematical expression."""
        try:
            return {"result": eval(expression)}
        except Exception as e:
            raise ToolExecutionError(
                message=f"Error evaluating expression: {str(e)}",
                tool_name=self.name,
                original_error=e
            )
```

### Creating a Tool from a Function

```python
import asyncio
from mycoder.agent.tools.base import create_tool_from_func

async def fetch_weather(location: str, units: str = "metric"):
    """Get the current weather for a location."""
    # Implementation here
    await asyncio.sleep(1)  # Simulate API call
    return {"temperature": 22, "condition": "Sunny", "location": location}

# Create a tool from the function
WeatherTool = create_tool_from_func(
    fetch_weather,
    name="get_weather",
    description="Get weather information for a location"
)
```

## Schema Generation

Tools automatically generate schemas for different LLM providers:

```python
# Get schema for Anthropic
anthropic_schema = tool.get_schema_for_llm("anthropic")

# Get schema for OpenAI
openai_schema = tool.get_schema_for_llm("openai")
```

## Error Handling

Tools use a standard error handling approach:

1. `ToolExecutionError` wraps original exceptions
2. Error details include the tool name and original error
3. Tools can handle specific errors related to their domain

Example of proper error handling in a tool:

```python
async def run(self, file_path: str):
    try:
        # Implementation here
        return result
    except FileNotFoundError as e:
        raise ToolExecutionError(
            message=f"File not found: {file_path}",
            tool_name=self.name,
            original_error=e
        )
    except Exception as e:
        raise ToolExecutionError(
            message=f"Error executing tool",
            tool_name=self.name,
            original_error=e
        )
```

## Implementing a New Tool

To add a new tool:

1. Define a Pydantic model for the tool's arguments
2. Subclass the `Tool` base class
3. Implement the `run` method
4. Register the tool with the `ToolManager`

See the "Creating a Custom Tool" example above for details. 