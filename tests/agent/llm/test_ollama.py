"""
Tests for the Ollama LLM provider.
"""

import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycoder.agent.llm.base import Message, MessageRole
from mycoder.agent.llm.ollama import OllamaConfig, OllamaProvider, OllamaResponse


@pytest.fixture
def ollama_provider():
    """Create an OllamaProvider instance for testing."""
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3",
        context_window=4096
    )
    return OllamaProvider(config=config)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_post = AsyncMock()
        mock_instance.post = mock_post
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_response():
    """Create a mock Ollama API response."""
    return {
        "model": "llama3",
        "created_at": "2023-01-01T00:00:00Z",
        "response": "This is a test response from Ollama.",
        "done": True,
        "context": [1, 2, 3],
        "total_duration": 1000000000,
        "load_duration": 100000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 500000000,
        "eval_count": 20,
        "eval_duration": 500000000
    }


@pytest.fixture
def messages():
    """Create a list of test messages."""
    return [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        Message(role=MessageRole.USER, content="Hello, how are you?")
    ]


def test_provider_properties(ollama_provider):
    """Test the provider's basic properties."""
    assert ollama_provider.provider_name == "ollama"
    assert ollama_provider.model_name == "llama3"
    assert ollama_provider.context_window == 4096


def test_count_tokens(ollama_provider):
    """Test the token counting method."""
    text = "This is a test sentence for token counting."
    token_count = ollama_provider.count_tokens(text)
    
    # Approximate token count checking
    assert token_count > 0
    assert 7 <= token_count <= 15  # Reasonable range for this short sentence


@pytest.mark.asyncio
async def test_generate_text_response(ollama_provider, mock_http_client, mock_response, messages):
    """Test generating a text response."""
    # Set up mock response
    mock_post_response = MagicMock()
    mock_post_response.json.return_value = mock_response
    mock_post_response.raise_for_status = MagicMock()
    mock_http_client.post.return_value = mock_post_response
    
    # Call generate
    response = await ollama_provider.generate(messages)
    
    # Check the response
    assert response.message.role == MessageRole.ASSISTANT
    assert response.message.content == "This is a test response from Ollama."
    assert response.usage is not None
    assert response.usage["prompt_tokens"] == 10
    assert response.usage["completion_tokens"] == 20
    
    # Verify API call
    mock_http_client.post.assert_called_once()
    args, kwargs = mock_http_client.post.call_args
    assert args[0] == "/api/generate"
    assert "model" in kwargs["json"]
    assert kwargs["json"]["model"] == "llama3"
    assert "prompt" in kwargs["json"]
    assert "stream" in kwargs["json"]
    assert not kwargs["json"]["stream"]  # Should not be streaming


@pytest.mark.asyncio
async def test_generate_tool_call(ollama_provider, mock_http_client, messages):
    """Test generating a tool call response."""
    # Set up mock response with tool call JSON
    tool_call_response = {
        "model": "llama3",
        "created_at": "2023-01-01T00:00:00Z",
        "response": """I need to use a tool to help with this.
```json
{
  "name": "fetch",
  "arguments": {
    "url": "https://example.com",
    "method": "GET"
  }
}
```""",
        "done": True,
        "prompt_eval_count": 10,
        "eval_count": 20
    }
    
    # Set up mock
    mock_post_response = MagicMock()
    mock_post_response.json.return_value = tool_call_response
    mock_post_response.raise_for_status = MagicMock()
    mock_http_client.post.return_value = mock_post_response
    
    # Define tool for testing
    tools = [
        {
            "name": "fetch",
            "description": "Fetch data from a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    ]
    
    # Call generate with tools
    response = await ollama_provider.generate(messages, tools=tools)
    
    # Check for tool call
    assert response.message.role == MessageRole.ASSISTANT
    assert response.message.tool_calls is not None
    assert len(response.message.tool_calls) == 1
    assert response.message.tool_calls[0].name == "fetch"
    assert response.message.tool_calls[0].arguments["url"] == "https://example.com"
    assert response.message.tool_calls[0].arguments["method"] == "GET"


@pytest.mark.asyncio
async def test_format_prompt(ollama_provider, messages):
    """Test formatting messages into a prompt."""
    prompt = ollama_provider._format_prompt(messages)
    
    # Check basic formatting
    assert "System: You are a helpful assistant." in prompt
    assert "User: Hello, how are you?" in prompt
    assert prompt.endswith("Assistant: ")  # Should end with assistant prompt


@pytest.mark.asyncio
async def test_format_tool_prompt(ollama_provider, messages):
    """Test formatting prompt with tools."""
    tools = [
        {
            "name": "fetch",
            "description": "Fetch data from a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    ]
    
    prompt = ollama_provider._format_prompt(messages, tools)
    
    # Should include tool instructions
    assert "System: You are a helpful assistant." in prompt
    
    # Add a tool call to messages and format again
    tool_call_msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        tool_calls=[
            {
                "id": "123",
                "name": "fetch",
                "arguments": {
                    "url": "https://example.com"
                }
            }
        ]
    )
    
    messages.append(tool_call_msg)
    
    # Add a tool result
    tool_result_msg = Message(
        role=MessageRole.TOOL,
        content="Result from fetch tool",
        tool_call_id="123"
    )
    
    messages.append(tool_result_msg)
    
    prompt = ollama_provider._format_prompt(messages, tools)
    
    # Should include tool call and result
    assert "I need to use the fetch tool" in prompt
    assert "Result from fetch" in prompt 