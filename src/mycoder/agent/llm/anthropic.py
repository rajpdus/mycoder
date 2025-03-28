"""
Anthropic LLM provider implementation for MyCoder.

This module implements the LLM provider interface for Anthropic's Claude models.
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import anthropic
from anthropic.types import ContentBlock, Message as AnthropicMessage
from anthropic import Anthropic, AsyncAnthropic, APIError, RateLimitError

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


class AnthropicConfig:
    """Configuration for the Anthropic provider."""
    
    # Default model settings
    DEFAULT_MODEL = "claude-3-opus-20240229"
    MODEL_CONTEXT_WINDOWS = {
        "claude-3-opus-20240229": 200000,  # 200k tokens
        "claude-3-sonnet-20240229": 200000,  # 200k tokens
        "claude-3-haiku-20240307": 200000,  # 200k tokens
        "claude-2.1": 200000,
        "claude-2.0": 100000,
        "claude-instant-1.2": 100000
    }
    
    # Claude message roles mapping
    ROLE_MAPPING = {
        MessageRole.SYSTEM: "system",  # Direct mapping for system
        MessageRole.USER: "user",      # Direct mapping for user
        MessageRole.ASSISTANT: "assistant",  # Direct mapping for assistant
        MessageRole.TOOL: "tool"      # Tool role - will be handled specially
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        organization: Optional[str] = None
    ):
        """
        Initialize the Anthropic configuration.
        
        Args:
            api_key: The Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model: The model to use (defaults to claude-3-opus)
            organization: The organization ID (not used for Anthropic but kept for interface consistency)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided or set in ANTHROPIC_API_KEY env var")
        
        self.model = model
        self.organization = organization  # Not used by Anthropic but kept for consistency
        
        # Set up logging
        self.logger = logging.getLogger("mycoder.llm.anthropic")


class AnthropicProvider(LLMProvider):
    """
    Anthropic LLM provider implementation.
    
    This provider supports Anthropic's API for Claude models.
    """
    
    def __init__(self, config: AnthropicConfig):
        """
        Initialize the Anthropic provider.
        
        Args:
            config: The Anthropic configuration
        """
        self.config = config
        self.client = AsyncAnthropic(api_key=config.api_key)
        self.logger = config.logger
    
    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.config.model
    
    @property
    def context_window(self) -> int:
        """Get the context window size."""
        return AnthropicConfig.MODEL_CONTEXT_WINDOWS.get(
            self.config.model, 100000  # Default fallback if model not in the dict
        )
    
    def _format_message_content(self, message: Message) -> List[ContentBlock]:
        """
        Format the message content for Anthropic's API.
        
        Args:
            message: The message to format
            
        Returns:
            List[ContentBlock]: Formatted content blocks
        """
        blocks = []
        
        # If it's a string, convert to a text content block
        if isinstance(message.content, str):
            blocks.append({"type": "text", "text": message.content})
        else:
            # Add the text content if available
            if message.content.text:
                blocks.append({"type": "text", "text": message.content.text})
        
        return blocks
    
    def format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Format a list of messages for Anthropic's API.
        
        Args:
            messages: The messages to format
            
        Returns:
            List[Dict[str, Any]]: The formatted messages for Anthropic's API
        """
        # Filter out any empty messages
        formatted_messages = []
        system_message = None
        
        for message in messages:
            # Extract system message - Anthropic handles it differently
            if message.role == MessageRole.SYSTEM:
                system_message = message.content if isinstance(message.content, str) else message.content.text
                continue
            
            # Skip empty messages
            if isinstance(message.content, str) and not message.content:
                continue
            
            # Map role
            role = AnthropicConfig.ROLE_MAPPING.get(message.role)
            if not role:
                self.logger.warning(f"Unknown message role: {message.role}, skipping")
                continue
            
            # Format standard messages
            if message.role in (MessageRole.USER, MessageRole.ASSISTANT):
                formatted_messages.append({
                    "role": role, 
                    "content": self._format_message_content(message)
                })
            # Format tool messages
            elif message.role == MessageRole.TOOL and message.tool_call_id:
                # Tool responses in Anthropic format
                formatted_messages.append({
                    "role": "assistant",  # In Anthropic, tool results are part of the assistant-tool exchange
                    "content": [{"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}]
                })
            
        return formatted_messages, system_message
    
    def format_tool_for_anthropic(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a tool schema for Anthropic's API.
        
        Args:
            tool_schema: The tool schema to format
            
        Returns:
            Dict[str, Any]: The formatted tool schema for Anthropic's API
        """
        # Anthropic uses "function" objects in their tools
        return {
            "name": tool_schema.get("name", ""),
            "description": tool_schema.get("description", ""),
            "input_schema": tool_schema.get("parameters", {})
        }
    
    def format_tool_for_provider(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a tool schema for the provider's API.
        
        Args:
            tool_schema: The tool schema to format
            
        Returns:
            Dict[str, Any]: The formatted tool schema for the provider's API
        """
        return self.format_tool_for_anthropic(tool_schema)
    
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response using Anthropic's API.
        
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
        # Format messages for Anthropic
        anthropic_messages, system_message = self.format_messages(messages)
        
        # Format tools for Anthropic if provided
        anthropic_tools = None
        if tools:
            anthropic_tools = [self.format_tool_for_anthropic(tool) for tool in tools]
        
        try:
            # Get response from Anthropic
            self.logger.debug(f"Sending request to Anthropic with {len(anthropic_messages)} messages")
            
            # Create message
            response = await self.client.messages.create(
                model=self.config.model,
                messages=anthropic_messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                tools=anthropic_tools
            )
            
            # Extract response content
            content_text = ""
            tool_calls = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    content_text += content_block.text
                elif content_block.type == "tool_use":
                    # Convert Anthropic tool_use to our ToolCall format
                    tool_calls.append(
                        ToolCall(
                            id=content_block.id,
                            name=content_block.name,
                            arguments=content_block.input
                        )
                    )
            
            # Format response
            message = Message(
                role=MessageRole.ASSISTANT,
                content=content_text
            )
            
            # Add tool calls if present
            if tool_calls:
                message.tool_calls = tool_calls
            
            # Extract usage information
            usage = None
            if hasattr(response, "usage"):
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            
            return LLMResponse(
                message=message,
                usage=usage
            )
        
        except anthropic.AuthenticationError as e:
            self.logger.error(f"Anthropic authentication error: {str(e)}")
            raise ProviderAuthenticationError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name
            )
        
        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic rate limit error: {str(e)}")
            raise ProviderRateLimitError(
                message=str(e),
                provider=self.provider_name,
                model=self.model_name
            )
        
        except anthropic.BadRequestError as e:
            error_msg = str(e)
            self.logger.error(f"Anthropic API error: {error_msg}")
            
            # Check if it's a context length error
            if "maximum context length" in error_msg.lower() or "tokens" in error_msg.lower():
                raise ContextLengthExceededError(
                    message=error_msg,
                    provider=self.provider_name,
                    model=self.model_name
                )
            
            # Check if it's a content filter error
            elif "content filtered" in error_msg.lower() or "content policy" in error_msg.lower():
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
        
        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            raise ProviderAPIError(
                message=str(e),
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
        
        # Use Anthropic's token counting utility
        return self.client.count_tokens(text)


def create_anthropic_provider(
    api_key: Optional[str] = None,
    model: str = AnthropicConfig.DEFAULT_MODEL,
    organization: Optional[str] = None
) -> AnthropicProvider:
    """
    Create an Anthropic provider with the given configuration.
    
    This is a convenience function to create an Anthropic provider without
    having to create a configuration object first.
    
    Args:
        api_key: The Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
        model: The model to use (defaults to claude-3-opus)
        organization: The organization ID (not used for Anthropic but kept for interface consistency)
        
    Returns:
        AnthropicProvider: The Anthropic provider
        
    Raises:
        ValueError: If the API key is not provided
    """
    config = AnthropicConfig(
        api_key=api_key,
        model=model,
        organization=organization
    )
    return AnthropicProvider(config) 