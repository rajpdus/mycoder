"""
Test script for the OpenAI provider.

This script tests the basic functionality of the OpenAI provider.
"""

import asyncio
import os
import sys
from typing import List

from .base import Message, MessageRole
from .openai import create_openai_provider


async def test_openai_provider():
    """Test the OpenAI provider with a simple conversation."""
    # Create provider
    provider = create_openai_provider()
    
    # Create messages
    messages: List[Message] = [
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        ),
        Message(
            role=MessageRole.USER,
            content="Hello, who are you?"
        )
    ]
    
    # Generate response
    print("Generating response...")
    response = await provider.generate(messages, temperature=0.7)
    
    # Print response
    print(f"\nAssistant: {response.message.content}")
    
    # Print usage if available
    if response.usage:
        print(f"\nUsage: {response.usage}")
    
    # Count tokens
    prompt_tokens = provider.count_message_tokens(messages)
    print(f"Prompt tokens: {prompt_tokens}")


async def test_openai_with_tools():
    """Test the OpenAI provider with tool use."""
    # Create provider
    provider = create_openai_provider()
    
    # Define a tool
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for"
                    }
                },
                "required": ["location"]
            }
        }
    ]
    
    # Create messages
    messages: List[Message] = [
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        ),
        Message(
            role=MessageRole.USER,
            content="What's the weather like in San Francisco?"
        )
    ]
    
    # Generate response
    print("Generating response with tools...")
    response = await provider.generate(messages, tools=tools, temperature=0.7)
    
    # Check if it's a tool call
    if response.message.is_tool_call():
        print("\nTool calls:")
        for tool_call in response.message.tool_calls:
            print(f"- Tool: {tool_call.name}")
            print(f"  Arguments: {tool_call.arguments}")
    else:
        print(f"\nAssistant: {response.message.content}")
    
    # Print usage if available
    if response.usage:
        print(f"\nUsage: {response.usage}")


async def main():
    """Main entry point for the test script."""
    # Run tests
    if len(sys.argv) > 1 and sys.argv[1] == "tools":
        await test_openai_with_tools()
    else:
        await test_openai_provider()


if __name__ == "__main__":
    # Only run when script is executed directly
    asyncio.run(main()) 