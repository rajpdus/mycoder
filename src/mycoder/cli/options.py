"""
Shared command line options for MyCoder.

This module defines the common CLI options that can be used across different commands.
"""

import click
import rich_click
from typing import Any, Callable, Dict, List, TypeVar

from mycoder.settings.config import LogLevel, LLMProvider, SubAgentMode

# Configure rich-click for nicer help pages
rich_click.STYLE_OPTION = "bold cyan"
rich_click.STYLE_SWITCH = "bold green"
rich_click.STYLE_METAVAR = "bold cyan"
rich_click.STYLE_HEADER = "bold yellow"
rich_click.STYLE_OPTION_HELP = ""
rich_click.STYLE_OPTION_DEFAULT = "dim"
rich_click.STYLE_OPTION_ENVVAR = "dim"
rich_click.USE_MARKDOWN = True
rich_click.SHOW_ARGUMENTS = True

# Type variable for the decorated function
F = TypeVar('F', bound=Callable[..., Any])


def add_shared_options() -> Callable[[F], F]:
    """
    Decorator function to add shared options to a Click command.

    This adds all the common options like log-level, provider, model, etc.,
    that are used across the MyCoder CLI commands.

    Returns:
        A decorator function that adds the shared options to a command.
    """
    shared_options: List[Callable] = [
        click.option(
            "--log-level",
            "-l",
            type=click.Choice([level.value for level in LogLevel], case_sensitive=False),
            default=LogLevel.INFO.value,
            help="Set minimum logging level",
            show_default=True,
        ),
        click.option(
            "--profile",
            is_flag=True,
            default=False,
            help="Enable performance profiling of CLI startup",
        ),
        click.option(
            "--provider",
            type=click.Choice([provider.value for provider in LLMProvider], case_sensitive=False),
            help="AI model provider to use",
            show_default=True,
        ),
        click.option(
            "--model",
            type=str,
            help="AI model name to use (defaults to provider's default model)",
        ),
        click.option(
            "--max-tokens",
            type=int,
            help="Maximum number of tokens to generate",
        ),
        click.option(
            "--temperature",
            type=float,
            help="Temperature for text generation (0.0-1.0)",
        ),
        click.option(
            "--context-window",
            type=int,
            help="Manual override for context window size in tokens",
        ),
        click.option(
            "--interactive",
            "-i",
            is_flag=True,
            default=False,
            help=(
                "Run in interactive mode, asking for prompts and enabling corrections "
                "during execution (use Ctrl+M to send corrections). Can be combined with "
                "-f/--file to append interactive input to file content."
            ),
        ),
        click.option(
            "--file",
            "-f",
            type=click.Path(exists=True, readable=True, file_okay=True, dir_okay=False),
            help="Read prompt from a file (can be combined with -i/--interactive)",
        ),
        click.option(
            "--token-usage",
            is_flag=True,
            default=False,
            help="Output token usage at info log level",
        ),
        click.option(
            "--headless",
            type=bool,
            help="Use browser in headless mode with no UI showing",
        ),
        click.option(
            "--user-session",
            type=bool,
            help="Use user's existing browser session instead of sandboxed session",
        ),
        click.option(
            "--user-prompt",
            type=bool,
            help="Enable or disable the userPrompt tool for getting user input during execution",
        ),
        click.option(
            "--upgrade-check",
            type=bool,
            help="Enable or disable version upgrade check (for automated/remote usage)",
        ),
        click.option(
            "--sub-agent-mode",
            type=click.Choice([mode.value for mode in SubAgentMode], case_sensitive=False),
            help="Sub-agent workflow mode (disabled, sync, or async)",
        ),
        click.option(
            "--github-mode",
            type=bool,
            help="Enable or disable GitHub integration features (requires git and gh CLI)",
        ),
        click.option(
            "--base-url",
            type=str,
            help="Base URL for the LLM provider API (mainly for Ollama)",
        ),
    ]

    def decorator(f: F) -> F:
        """Apply all shared options to the function in reverse order."""
        for option in reversed(shared_options):
            f = option(f)
        return f

    return decorator


def convert_options_to_settings_dict(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Click options dict to a format suitable for updating Settings.

    This handles converting string enums to their proper types and
    removing None values (to avoid overriding defaults).

    Args:
        options: Dictionary of CLI options from Click.

    Returns:
        Dict suitable for updating a Settings instance.
    """
    settings_dict = {}

    # Map of option names to their enum types if applicable
    enum_options = {
        "log_level": LogLevel,
        "provider": LLMProvider,
        "sub_agent_mode": SubAgentMode,
    }

    # Process each option, converting to enums where needed and skipping None values
    for key, value in options.items():
        if value is None:
            continue  # Skip None values to keep defaults

        # Convert string values to enums where needed
        if key in enum_options and isinstance(value, str):
            try:
                settings_dict[key] = enum_options[key](value)
            except ValueError:
                continue  # Skip invalid values
        else:
            settings_dict[key] = value

    return settings_dict 