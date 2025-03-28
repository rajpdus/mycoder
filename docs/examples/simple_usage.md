# Simple Usage Examples

This document shows basic usage examples for MyCoder-Py.

## Basic Setup

```python
import asyncio
from mycoder.agent.llm import create_provider, Message, MessageRole
from mycoder.agent.tools import get_default_tools
from mycoder.agent.tool_manager import ToolManager

async def main():
    # Create an LLM provider (OpenAI in this case)
    provider = create_provider("openai", model="gpt-4")
    
    # Create a tool manager and register tools
    tool_manager = ToolManager()
    tool_manager.register_tools(get_default_tools())
    
    # Initialize conversation
    messages = [
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant with access to tools."
        ),
        Message(
            role=MessageRole.USER,
            content="What files are in the current directory?"
        )
    ]
    
    # Get tool schemas for the LLM
    tool_schemas = tool_manager.get_tool_schemas_for_llm("openai")
    
    # Generate a response
    response = await provider.generate(messages, tools=tool_schemas)
    
    # Handle tool calls if present
    if response.message.is_tool_call():
        for tool_call in response.message.tool_calls:
            print(f"Tool call: {tool_call.name}")
            
            # Execute the tool
            result = await tool_manager.execute_tool(
                tool_call.name, 
                tool_call.arguments
            )
            
            # Add the tool result to messages
            messages.append(
                Message(
                    role=MessageRole.TOOL,
                    content=str(result),
                    tool_call_id=tool_call.id
                )
            )
        
        # Get final response with tool results
        final_response = await provider.generate(messages)
        print(f"Final response: {final_response.message.content}")
    else:
        print(f"Response: {response.message.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Reading a File

```python
import asyncio
from mycoder.agent.tools.file_ops import ReadFileTool

async def read_file_example():
    # Create the tool
    read_tool = ReadFileTool()
    
    # Execute the tool
    result = await read_tool.execute(
        file_path="example.txt",
        offset=0,
        limit=10
    )
    
    print(f"File content: {result.content}")
    print(f"Total lines: {result.total_lines}")

if __name__ == "__main__":
    asyncio.run(read_file_example())
```

## Running a Shell Command

```python
import asyncio
from mycoder.agent.tools.shell import RunCommandTool

async def shell_example():
    # Create the tool
    shell_tool = RunCommandTool()
    
    # Execute the tool
    result = await shell_tool.execute(
        command="ls -la",
        working_dir=None,  # Current directory
        timeout=10
    )
    
    print(f"Command output: {result.stdout}")
    print(f"Exit code: {result.exit_code}")

if __name__ == "__main__":
    asyncio.run(shell_example())
```

## Interacting with the User

```python
import asyncio
from mycoder.agent.tools.user import UserPromptTool, UserMessageTool

async def user_interaction_example():
    # Create the tools
    prompt_tool = UserPromptTool()
    message_tool = UserMessageTool()
    
    # Display a message to the user
    await message_tool.execute(
        content="# Welcome to MyCoder\n\nThis is a demonstration of user interaction.",
        format="markdown",
        level="info"
    )
    
    # Get input from the user
    name = await prompt_tool.execute(
        message="What is your name?",
        default="User"
    )
    
    # Display a personalized message
    await message_tool.execute(
        content=f"Hello, {name}! It's nice to meet you.",
        format="plain",
        level="success"
    )

if __name__ == "__main__":
    asyncio.run(user_interaction_example())
```

## Creating a Custom Tool

```python
import asyncio
from pydantic import BaseModel, Field
from mycoder.agent.tools.base import Tool, ToolExecutionError

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
            # WARNING: eval is used for demonstration only
            # In a real application, use a safer method
            result = eval(expression)
            return {"result": result}
        except Exception as e:
            raise ToolExecutionError(
                message=f"Error evaluating expression: {str(e)}",
                tool_name=self.name,
                original_error=e
            )

async def custom_tool_example():
    # Create the tool
    calc_tool = CalculatorTool()
    
    # Execute the tool
    result = await calc_tool.execute(expression="2 + 2 * 3")
    print(f"Result: {result['result']}")

if __name__ == "__main__":
    asyncio.run(custom_tool_example())
``` 