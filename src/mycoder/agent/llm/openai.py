"""
OpenAI LLM provider implementation for MyCoder.

This module implements the LLM provider interface for OpenAI models.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import tiktoken
from openai import AsyncOpenAI, BadRequestError, AuthenticationError, RateLimitError

from .base import LLMProvider, LLMResponse, Message, MessageRole, ToolCall
from .exceptions import (
    LLMError,
    ProviderAPIError,
    ProviderRateLimitError,
    ProviderAuthenticationError,
    ModelNotFoundError,
    ContentFilterError,
    ContextLengthExceededError
)


class OpenAIConfig:
    """Configuration for the OpenAI provider."""
    
    # Default model settings
    DEFAULT_MODEL = "gpt-4-turbo"
    MODEL_CONTEXT_WINDOWS = {
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-1106": 16385,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4-turbo-preview": 128000
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        organization: Optional[str] = None
    ):
        """
        Initialize the OpenAI configuration.
        
        Args:
            api_key: The OpenAI API key (falls back to OPENAI_API_KEY env var)
            model: The model to use (defaults to gpt-4-turbo)
            organization: The organization ID to use (falls back to OPENAI_ORG env var)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
        
        self.model = model
        self.organization = organization or os.environ.get("OPENAI_ORG")
        
        # Set up logging
        self.logger = logging.getLogger("mycoder.llm.openai")


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider implementation.
    
    This provider supports OpenAI's API for text generation.
    """
    
    def __init__(self, config: OpenAIConfig):
        """
        Initialize the OpenAI provider.
        
        Args:
            config: The OpenAI configuration
        """
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            organization=config.organization
        )
        
        # Set up tokenizer
        self._tokenizer = tiktoken.encoding_for_model(config.model)
        self.logger = config.logger
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "openai"
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.config.model
    
    @property
    def context_window(self) -> int:
        """Get the context window size."""
        return OpenAIConfig.MODEL_CONTEXT_WINDOWS.get(
            self.config.model, 8192  # Default fallback if model not in the dict
        )
    
    def format_message(self, message: Message) -> Dict[str, Any]:
        """
        Format a Message object into OpenAI's API format.
        
        Args:
            message: The message to format
            
        Returns:
            Dict[str, Any]: The formatted message for OpenAI's API
        """
        openai_message = {"role": message.role.value}
        
        # Handle content
        if isinstance(message.content, str):
            openai_message["content"] = message.content
        else:
            # Handle structured content
            openai_message["content"] = message.content.text or ""
        
        # Handle tool calls and results
        if message.tool_call_id:
            openai_message["tool_call_id"] = message.tool_call_id
        
        if message.tool_calls:
            openai_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(tool_call.arguments)
                    }
                }
                for tool_call in message.tool_calls
            ]
        
        return openai_message
    
    def format_tool_for_provider(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a tool schema for OpenAI's API.
        
        Args:
            tool_schema: The tool schema to format
            
        Returns:
            Dict[str, Any]: The formatted tool schema for OpenAI's API
        """
        return {
            "type": "function",
            "function": tool_schema
        }
    
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response using OpenAI's API.
        
        Args:
            messages: The conversation messages
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse: The LLM's response
            
        Raises:
            LLMError: If there's an error generating a response
        """
        # Format messages for OpenAI
        openai_messages = [self.format_message(message) for message in messages]
        
        # Format tools for OpenAI if provided
        openai_tools = None
        if tools:
            openai_tools = [self.format_tool_for_provider(tool) for tool in tools]
        
        try:
            # Get response from OpenAI
            self.logger.debug(f"Sending request to OpenAI with {len(openai_messages)} messages")
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                tools=openai_tools,
                temperature=temperature,
                max_tokens=max_tokens,
                tool_choice="auto"
            )
            
            # Extract response
            assistant_message = response.choices[0].message
            
            # Format response
            message = Message(
                role=MessageRole.ASSISTANT,
                content=assistant_message.content or ""
            )
            
            # Extract tool calls if present
            if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
                message.tool_calls = [
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                    )
                    for tool_call in assistant_message.tool_calls
                ]
            
            # Extract usage information
            usage = None
            if hasattr(response, "usage"):
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                message=message,
                usage=usage
            )
        
        except AuthenticationError as e:
            self.logger.error(f"OpenAI authentication error: {str(e)}")
            raise ProviderAuthenticationError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name
            )
        
        except RateLimitError as e:
            self.logger.error(f"OpenAI rate limit error: {str(e)}")
            raise ProviderRateLimitError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name
            )
        
        except BadRequestError as e:
            error_msg = str(e)
            self.logger.error(f"OpenAI API error: {error_msg}")
            
            # Check if it's a context length error
            if "maximum context length" in error_msg.lower() or "tokens" in error_msg.lower():
                raise ContextLengthExceededError(
                    message=error_msg,
                    provider=self.provider_name,
                    model=self.model_name
                )
            
            # Check if it's a content filter error
            elif "content filter" in error_msg.lower() or "policy violation" in error_msg.lower():
                raise ContentFilterError(
                    message=error_msg,
                    provider=self.provider_name,
                    model=self.model_name
                )
            
            # Generic API error
            else:
                raise ProviderAPIError(
                    message=error_msg,
                    provider=self.provider_name,
                    model=self.model_name
                )
        
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise LLMError(
                message=f"Unexpected error: {str(e)}",
                provider=self.provider_name,
                model=self.model_name
            )
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            int: The number of tokens
        """
        if not text:
            return 0
        
        tokens = self._tokenizer.encode(text)
        return len(tokens)


def create_openai_provider(
    api_key: Optional[str] = None,
    model: str = OpenAIConfig.DEFAULT_MODEL,
    organization: Optional[str] = None
) -> OpenAIProvider:
    """
    Create an OpenAI provider with the given configuration.
    
    This is a convenience function to create an OpenAI provider without
    having to create a configuration object first.
    
    Args:
        api_key: The OpenAI API key (falls back to OPENAI_API_KEY env var)
        model: The model to use (defaults to gpt-4-turbo)
        organization: The organization ID to use (falls back to OPENAI_ORG env var)
        
    Returns:
        OpenAIProvider: The OpenAI provider
        
    Raises:
        ValueError: If the API key is not provided
    """
    config = OpenAIConfig(
        api_key=api_key,
        model=model,
        organization=organization
    )
    return OpenAIProvider(config) 