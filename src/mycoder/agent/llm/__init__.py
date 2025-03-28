"""
LLM provider module for MyCoder.

This module provides interfaces and implementations for various LLM providers.
"""

from .base import (
    LLMProvider,
    Message,
    MessageRole,
    Message as AssistantMessage,  # For backward compatibility
    Message as UserMessage,  # For backward compatibility
    LLMResponse as ResponseFormat,  # For backward compatibility
    ToolCall as Function,  # For backward compatibility
    ToolCallResult as ToolResult,  # For backward compatibility
    ToolCall,
)
from .exceptions import (
    LLMError,
    ProviderAPIError as APIError,
    ProviderRateLimitError as RateLimitError,
    ProviderAuthenticationError as AuthenticationError,
    ModelNotFoundError,
    ContentFilterError,
    ContextLengthExceededError as TokenCountError
)
from .anthropic import AnthropicConfig, AnthropicProvider, create_anthropic_provider
from .ollama import OllamaConfig, OllamaProvider
from .openai import OpenAIConfig, OpenAIProvider, create_openai_provider

__all__ = [
    # Base classes and types
    "LLMProvider",
    "Message",
    "MessageRole",
    "AssistantMessage",
    "UserMessage",
    "ResponseFormat",
    "Function",
    "ToolResult",
    "ToolCall",
    
    # Exceptions
    "LLMError",
    "TokenCountError",
    "RateLimitError",
    "AuthenticationError",
    "APIError",
    
    # Provider implementations
    "OpenAIConfig",
    "OpenAIProvider",
    "create_openai_provider",
    "AnthropicConfig",
    "AnthropicProvider",
    "create_anthropic_provider",
    "OllamaConfig",
    "OllamaProvider",
    "get_provider",
    "create_provider",
]

# Mapping of provider names to their implementation classes
PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(provider_type: str) -> type:
    """
    Get a provider class by name.
    
    Args:
        provider_type: The name of the provider
        
    Returns:
        The provider class
        
    Raises:
        ValueError: If the provider is not found
    """
    if provider_type not in PROVIDERS:
        raise ValueError(f"Unsupported provider type: {provider_type}. Supported types: {list(PROVIDERS.keys())}")
    
    return PROVIDERS[provider_type]


def create_provider(
    provider_type: str,
    **kwargs
) -> LLMProvider:
    """
    Create an LLM provider instance by name.
    
    This factory function simplifies the creation of LLM providers
    by handling configuration automatically.
    
    Args:
        provider_type: The name of the provider to create
        **kwargs: Provider-specific configuration options
        
    Returns:
        LLMProvider: The created provider instance
        
    Raises:
        ValueError: If the provider is not found
    """
    if provider_type == "openai":
        return create_openai_provider(**kwargs)
    elif provider_type == "anthropic":
        return create_anthropic_provider(**kwargs)
    elif provider_type == "ollama":
        return OllamaProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}. Supported types: {list(PROVIDERS.keys())}")
