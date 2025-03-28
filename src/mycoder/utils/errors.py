"""
Error handling utilities and custom exceptions for MyCoder.

This module defines custom exception classes for different error scenarios
and helper functions for error handling and reporting.
"""

import sys
import traceback
from typing import Optional, Type

import sentry_sdk
from rich.console import Console

# Initialize console for rich error output
console = Console(stderr=True)


class MyCoderError(Exception):
    """Base exception class for all MyCoder errors."""
    pass


class ConfigError(MyCoderError):
    """Error raised when there's an issue with the configuration."""
    pass


class LLMError(MyCoderError):
    """Error raised when there's an issue with the LLM provider."""
    pass


class APIKeyError(LLMError):
    """Error raised when an API key is missing or invalid."""
    pass


class ToolError(MyCoderError):
    """Error raised when there's an issue with a tool."""
    pass


class ToolNotFoundError(ToolError):
    """Error raised when a requested tool doesn't exist."""
    pass


class ToolExecutionError(ToolError):
    """Error raised when a tool fails during execution."""
    
    def __init__(self, message: str, tool_name: str, original_error: Optional[Exception] = None):
        """
        Initialize a ToolExecutionError.
        
        Args:
            message: Error message
            tool_name: Name of the tool that failed
            original_error: The original exception that caused this error
        """
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"{message} (Tool: {tool_name})")


class AgentError(MyCoderError):
    """Error raised when there's an issue with the agent itself."""
    pass


def setup_error_handling(enable_sentry: bool = False, sentry_dsn: Optional[str] = None) -> None:
    """
    Set up global error handling and reporting.
    
    Args:
        enable_sentry: Whether to enable Sentry error reporting
        sentry_dsn: Sentry DSN (required if enable_sentry is True)
    """
    if enable_sentry:
        if not sentry_dsn:
            console.print("[yellow]Warning:[/yellow] Sentry enabled but no DSN provided.")
            return
            
        sentry_sdk.init(
            dsn=sentry_dsn,
            # Set traces_sample_rate to 1.0 to capture 100% of transactions
            traces_sample_rate=1.0,
        )
        console.print("[green]Sentry error reporting enabled.[/green]")


def handle_exception(
    e: Exception, 
    exit_on_error: bool = False,
    exit_code: int = 1,
    report_to_sentry: bool = True
) -> None:
    """
    Handle an exception with nice formatting and optional reporting.
    
    Args:
        e: The exception to handle
        exit_on_error: Whether to exit the program after handling
        exit_code: Exit code to use if exiting
        report_to_sentry: Whether to report to Sentry (if configured)
    """
    # Format the error message
    error_type = type(e).__name__
    error_msg = str(e)
    
    # Print a nice error message
    console.print(f"[bold red]Error ({error_type}):[/bold red] {error_msg}")
    
    # Show traceback for development/debugging
    if isinstance(e, MyCoderError):
        # For our custom errors, keep it cleaner
        if hasattr(e, 'original_error') and getattr(e, 'original_error'):
            orig = getattr(e, 'original_error')
            console.print(f"[dim]Caused by: {type(orig).__name__}: {str(orig)}[/dim]")
    else:
        # For unexpected errors, show the traceback
        console.print("[dim]Traceback:[/dim]")
        tb = traceback.format_exception(type(e), e, e.__traceback__)
        console.print("".join(tb), style="dim")
    
    # Report to Sentry if enabled
    if report_to_sentry:
        try:
            sentry_sdk.capture_exception(e)
        except Exception:
            # Ignore errors from Sentry reporting
            pass
    
    # Exit if requested
    if exit_on_error:
        sys.exit(exit_code)


def get_api_key_error(provider: str) -> str:
    """
    Get a user-friendly error message for missing API keys.
    
    Args:
        provider: The name of the provider with a missing key
        
    Returns:
        A formatted error message with instructions
    """
    provider = provider.lower()
    
    if provider == "anthropic":
        return (
            "Anthropic API key not found. Please set the ANTHROPIC_API_KEY "
            "environment variable or add it to your .env file."
        )
    elif provider == "openai":
        return (
            "OpenAI API key not found. Please set the OPENAI_API_KEY "
            "environment variable or add it to your .env file."
        )
    else:
        return f"API key not found for provider '{provider}'. Please check your configuration." 