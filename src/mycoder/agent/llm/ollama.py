"""
Ollama LLM provider implementation.

This module provides an implementation of the LLMProvider interface
for the Ollama API, allowing local models to be used with MyCoder.
"""

import asyncio
import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Union, cast

import httpx
from pydantic import BaseModel, Field

from .base import LLMProvider, LLMResponse, Message, MessageRole, ToolCall
from .exceptions import LLMError, ProviderAPIError


class OllamaTokenCount(BaseModel):
    """Response from Ollama token counting."""
    
    tokens: int


class OllamaModelInfo(BaseModel):
    """Information about an Ollama model."""
    
    name: str
    model_count_url: str
    context_length: int = Field(default=4096)  # Default context window for most Ollama models


class OllamaResponse(BaseModel):
    """Response from Ollama API."""
    
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaConfig(BaseModel):
    """Configuration for Ollama provider."""
    
    base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API"
    )
    model: str = Field(
        default="llama3",
        description="Model name to use"
    )
    context_window: int = Field(
        default=4096,
        description="Context window size in tokens"
    )


# Pattern to extract function calls from markdown or JSON in Ollama output
FUNCTION_CALL_PATTERN = re.compile(
    r"```(json|.*)\s*({[\s\S]*?})\s*```|({[\s\S]*})",
    re.MULTILINE
)


class OllamaProvider(LLMProvider):
    """
    LLM provider implementation for Ollama API.
    
    This provider allows using local models via Ollama for MyCoder.
    Note that tool usage with Ollama is experimental and may not work
    consistently with all models.
    """
    
    def __init__(
        self,
        config: Optional[OllamaConfig] = None,
        **kwargs
    ):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Configuration for the provider
            **kwargs: Additional arguments to override config values
        """
        # Initialize config, overriding with kwargs if provided
        self._config = config or OllamaConfig()
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        self._http_client = httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=120.0
        )
    
    @property
    def provider_name(self) -> str:
        """
        Get the name of the provider.
        
        Returns:
            str: The name of the provider
        """
        return "ollama"
    
    @property
    def model_name(self) -> str:
        """
        Get the name of the model being used.
        
        Returns:
            str: The name of the model
        """
        return self._config.model
    
    @property
    def context_window(self) -> int:
        """
        Get the context window size of the model in tokens.
        
        Returns:
            int: The context window size
        """
        return self._config.context_window
    
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response from Ollama.
        
        Args:
            messages: List of messages in the conversation
            tools: Optional list of tool definitions
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            LLMResponse: The LLM's response
            
        Raises:
            LLMError: If there's an error generating a response
        """
        try:
            # Format prompt in a way Ollama understands
            prompt = self._format_prompt(messages, tools)
            
            # Prepare request payload
            data = {
                "model": self._config.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
            }
            
            if max_tokens:
                data["num_predict"] = max_tokens
            
            # If tools are provided, add a system instruction about using them
            if tools and len(tools) > 0:
                tool_instruction = self._generate_tool_instruction(tools)
                data["system"] = tool_instruction
            
            # Make request to Ollama API
            response = await self._http_client.post("/api/generate", json=data)
            response.raise_for_status()
            
            # Parse the response
            ollama_response = OllamaResponse.parse_obj(response.json())
            
            # Check for tool calls in the response
            message = self._parse_response(ollama_response, tools)
            
            # Create LLMResponse
            return LLMResponse(
                message=message,
                usage={
                    "prompt_tokens": ollama_response.prompt_eval_count or 0,
                    "completion_tokens": ollama_response.eval_count or 0,
                    "total_tokens": (ollama_response.prompt_eval_count or 0) + (ollama_response.eval_count or 0)
                }
            )
        
        except httpx.HTTPStatusError as e:
            raise LLMError(f"HTTP error from Ollama: {e.response.text}")
        except httpx.RequestError as e:
            raise LLMError(f"Request error with Ollama: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error with Ollama: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            int: The number of tokens
        """
        # Simple approximation since Ollama doesn't provide a standard way
        # to count tokens without making API calls. Each model might use
        # a different tokenizer.
        # This is a very rough approximation.
        words = text.split()
        return len(words) + len(text) // 4
    
    def _format_prompt(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Format messages into a prompt string for Ollama.
        
        Args:
            messages: The messages to format
            tools: Optional list of tool definitions
            
        Returns:
            str: The formatted prompt
        """
        formatted_messages = []
        
        # If tools are provided, add a system instruction if not already present
        if tools and len(tools) > 0:
            has_system = any(m.role == MessageRole.SYSTEM for m in messages)
            if not has_system:
                tool_instruction = self._generate_tool_instruction(tools)
                formatted_messages.append(f"System: {tool_instruction}\n")
        
        # Format each message
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                formatted_messages.append(f"System: {message.content}\n")
            elif message.role == MessageRole.USER:
                formatted_messages.append(f"User: {message.content}\n")
            elif message.role == MessageRole.ASSISTANT:
                if isinstance(message.content, str) and message.content.strip():
                    formatted_messages.append(f"Assistant: {message.content}\n")
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        args_str = json.dumps(tool_call.arguments, indent=2)
                        tool_call_str = (
                            f"I need to use the {tool_call.name} tool.\n"
                            f"Arguments: ```json\n{args_str}\n```"
                        )
                        formatted_messages.append(f"Assistant: {tool_call_str}\n")
            elif message.role == MessageRole.TOOL:
                if message.tool_call_id:
                    # Format tool results
                    for prev_msg in reversed(messages):
                        if (prev_msg.role == MessageRole.ASSISTANT and 
                            prev_msg.tool_calls and 
                            any(t.id == message.tool_call_id for t in prev_msg.tool_calls)):
                            for tool_call in prev_msg.tool_calls:
                                if tool_call.id == message.tool_call_id:
                                    result_str = f"Result from {tool_call.name}: {message.content}"
                                    formatted_messages.append(f"{result_str}\n")
                                    break
                            break
        
        # Add final prompt for assistant
        formatted_messages.append("Assistant: ")
        
        return "".join(formatted_messages)
    
    def _generate_tool_instruction(self, tools: List[Dict[str, Any]]) -> str:
        """
        Generate system instruction for using tools.
        
        Args:
            tools: The tools available to the model
            
        Returns:
            str: System instruction for using tools
        """
        tool_descriptions = []
        for tool in tools:
            params_str = json.dumps(tool.get("parameters", {}), indent=2)
            tool_descriptions.append(
                f"Tool: {tool.get('name')}\n"
                f"Description: {tool.get('description')}\n"
                f"Parameters: {params_str}\n"
            )
        
        tools_str = "\n".join(tool_descriptions)
        
        return (
            "You have access to the following tools. When you need to use a tool, "
            "respond with a JSON object in the following format:\n\n"
            "```json\n{\n  \"name\": \"tool_name\",\n  \"arguments\": {\n    \"arg1\": \"value1\",\n    \"arg2\": \"value2\"\n  }\n}\n```\n\n"
            f"Available tools:\n\n{tools_str}"
        )
    
    def _parse_response(
        self,
        ollama_response: OllamaResponse,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """
        Parse Ollama response to extract message or tool calls.
        
        Args:
            ollama_response: Response from Ollama
            tools: Available tools
            
        Returns:
            Message: Parsed message with potential tool calls
        """
        text = ollama_response.response
        
        # If no tools or empty response, return simple text message
        if not tools or not text.strip():
            return Message(
                role=MessageRole.ASSISTANT,
                content=text
            )
        
        # Try to find function call in the response
        match = FUNCTION_CALL_PATTERN.search(text)
        if not match:
            # No function call found, return text message
            return Message(
                role=MessageRole.ASSISTANT,
                content=text
            )
        
        # Extract the JSON part
        json_str = match.group(2) or match.group(3)
        
        try:
            # Try to parse as JSON
            tool_data = json.loads(json_str)
            
            # Check if it has the expected structure for a tool call
            if "name" in tool_data and "arguments" in tool_data:
                tool_name = tool_data["name"]
                tool_args = tool_data["arguments"]
                
                # Create a tool call
                tool_call = ToolCall(
                    id=str(uuid.uuid4()),
                    name=tool_name,
                    arguments=tool_args
                )
                
                # Create message with tool call
                return Message(
                    role=MessageRole.ASSISTANT,
                    content="",  # Empty content for tool call messages
                    tool_calls=[tool_call]
                )
            
        except (json.JSONDecodeError, KeyError):
            # If JSON parsing fails or structure is wrong, return text message
            pass
        
        # Default: return as text message
        return Message(
            role=MessageRole.ASSISTANT,
            content=text
        ) 