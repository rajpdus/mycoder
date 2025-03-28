"""
Base classes for LLM providers in MyCoder.

This module defines the abstract base class that all LLM providers must implement,
along with common types and utility functions.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"  # For tool calls and results


class MessageContent(BaseModel):
    """Content of a message, which can be text or a structured object."""
    
    type: str = Field(
        default="text",
        description="Type of content (text or other format)"
    )
    text: Optional[str] = Field(
        default=None,
        description="Text content of the message"
    )
    # Could be extended with other content types like images, etc.


class ToolCallResult(BaseModel):
    """Result of a tool call."""
    
    tool_name: str
    result: Any
    error: Optional[str] = None


class ToolCall(BaseModel):
    """A call to a tool by the LLM."""
    
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[ToolCallResult] = None


class Message(BaseModel):
    """A message in a conversation with the LLM."""
    
    role: MessageRole
    content: Union[str, MessageContent]
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool result messages
    
    def is_tool_call(self) -> bool:
        """Check if this message is a tool call."""
        return self.role == MessageRole.ASSISTANT and self.tool_calls is not None


class LLMResponse(BaseModel):
    """Response from the LLM."""
    
    message: Message
    usage: Optional[Dict[str, int]] = None  # Token usage information if available


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure consistent
    behavior and API across different providers.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the name of the provider.
        
        Returns:
            str: The name of the provider (e.g., "anthropic", "openai")
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the name of the model being used.
        
        Returns:
            str: The name of the model (e.g., "claude-3", "gpt-4")
        """
        pass
    
    @property
    @abstractmethod
    def context_window(self) -> int:
        """
        Get the context window size of the model in tokens.
        
        Returns:
            int: The context window size
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
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
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            int: The number of tokens
        """
        pass
    
    def count_message_tokens(self, messages: List[Message]) -> int:
        """
        Count the total number of tokens in a list of messages.
        
        This is a simple implementation that counts each message separately.
        Providers may override this with more accurate implementations.
        
        Args:
            messages: The messages to count tokens for
            
        Returns:
            int: The total number of tokens
        """
        total = 0
        for message in messages:
            if isinstance(message.content, str):
                total += self.count_tokens(message.content)
            else:
                # For structured content, count text fields
                if message.content.text:
                    total += self.count_tokens(message.content.text)
            
            # Count tool calls if present
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    # Count tool name
                    total += self.count_tokens(tool_call.name)
                    
                    # Count arguments as JSON
                    args_json = str(tool_call.arguments)
                    total += self.count_tokens(args_json)
                    
                    # Count result if present
                    if tool_call.result:
                        result_json = str(tool_call.result.dict())
                        total += self.count_tokens(result_json)
        
        return total
    
    def format_tool_for_provider(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a tool schema for this specific provider.
        
        This is a default implementation that assumes the tool schema
        is already in the format expected by the provider. Specific provider
        implementations should override this method if needed.
        
        Args:
            tool_schema: The tool schema to format
            
        Returns:
            Dict[str, Any]: The formatted tool schema
        """
        return tool_schema
