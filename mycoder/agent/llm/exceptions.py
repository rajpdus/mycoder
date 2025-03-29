"""
Exceptions for LLM providers in MyCoder.

This module defines the exceptions that can be raised by LLM providers.
"""

from typing import Any, Dict, Optional


class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LLM error.
        
        Args:
            message: The error message
            provider: The provider name (e.g., "anthropic")
            model: The model name (e.g., "claude-3-sonnet")
            details: Additional error details
        """
        self.provider = provider
        self.model = model
        self.details = details or {}
        
        # Format the message with provider and model information if available
        if provider and model:
            full_message = f"[{provider}/{model}] {message}"
        elif provider:
            full_message = f"[{provider}] {message}"
        else:
            full_message = message
        
        super().__init__(full_message)


class ProviderAPIError(LLMError):
    """Exception raised when there's an API error from the provider."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        model: Optional[str] = None,
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize the provider API error.
        
        Args:
            message: The error message
            provider: The provider name (e.g., "anthropic")
            model: The model name if applicable
            status_code: The HTTP status code if applicable
            original_error: The original exception
        """
        self.status_code = status_code
        
        # Add status code to details
        details = {}
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, provider, model, details)


class ProviderRateLimitError(ProviderAPIError):
    """Exception raised when the provider's rate limit is exceeded."""
    pass


class ProviderAuthenticationError(ProviderAPIError):
    """Exception raised when there's an authentication error with the provider."""
    pass


class ModelNotFoundError(LLMError):
    """Exception raised when the requested model is not found."""
    pass


class ContentFilterError(LLMError):
    """Exception raised when the content is filtered by the provider's content filter."""
    pass


class ContextLengthExceededError(LLMError):
    """Exception raised when the context length is exceeded."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        token_count: Optional[int] = None,
        max_tokens: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the context length exceeded error.
        
        Args:
            message: The error message
            provider: The provider name
            model: The model name
            token_count: The actual token count
            max_tokens: The maximum allowed tokens
            details: Additional error details
        """
        self.token_count = token_count
        self.max_tokens = max_tokens
        
        # Add token information to details
        details = details or {}
        if token_count:
            details["token_count"] = token_count
        if max_tokens:
            details["max_tokens"] = max_tokens
        
        super().__init__(message, provider, model, details) 