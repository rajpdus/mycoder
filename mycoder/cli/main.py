"""
Main entry point for the MyCoder CLI.

This module defines the main CLI command group and handles the default command
for running the AI agent with a prompt.
"""

import sys
from pathlib import Path
from typing import Optional

import click
import rich_click
from rich.console import Console
from rich.prompt import Prompt

from src.mycoder.cli.options import add_shared_options, convert_options_to_settings_dict
from src.mycoder.settings.config import Settings, load_settings
from src.mycoder.utils.logging import configure_logging, get_logger

# Initialize console for rich output
console = Console()


@click.group(invoke_without_command=True)
@click.version_option(package_name="mycoder")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    MyCoder: AI-powered coding assistant.

    If no command is specified, the default behavior is to run the AI agent
    with the given prompt or interactively.
    """
    # If we're not in a subcommand, invoke the default command
    if ctx.invoked_subcommand is None:
        # Create a new context for the default command
        ctx.invoke(default_command)


@cli.command("run", help="Execute a prompt or start interactive mode")
@click.argument("prompt", required=False)
@add_shared_options()
def default_command(
    prompt: Optional[str] = None, 
    **options
) -> None:
    """
    Default command to run the AI agent with a prompt or interactively.

    Args:
        prompt: Optional prompt text to run. If not provided and interactive mode
               is not enabled, a prompt will be requested.
        **options: Additional options from shared options decorator.
    """
    # Load settings from environment and CLI options
    settings = load_settings()
    
    # Update settings with CLI options
    cli_settings = convert_options_to_settings_dict(options)
    for key, value in cli_settings.items():
        setattr(settings, key, value)
    
    # Configure logging based on settings
    configure_logging(settings.log_level)
    logger = get_logger("mycoder.cli.default")
    
    # Log the version and startup information
    import pkg_resources
    version = pkg_resources.get_distribution("mycoder").version
    logger.info(f"MyCoder v{version} - AI-powered coding assistant")
    
    # Determine the prompt source
    prompt_source = get_prompt_source(prompt, settings, options)
    
    if not prompt_source:
        logger.error("No prompt provided and interactive mode not enabled.")
        sys.exit(1)
    
    logger.info(f"Using prompt from {prompt_source[0]}: {prompt_source[1]}")
    
    # TODO: Initialize and run the agent with the prompt
    # This is a placeholder until we implement the agent
    logger.info("Agent execution would start here (not yet implemented)")
    console.print("[yellow]Agent functionality is not yet implemented.[/yellow]")
    console.print(f"[green]Would run with prompt:[/green] {prompt_source[1]}")


def get_prompt_source(
    prompt: Optional[str], settings: Settings, options: dict
) -> Optional[tuple[str, str]]:
    """
    Determine the prompt source and content.
    
    Args:
        prompt: The prompt provided as a command-line argument.
        settings: The application settings.
        options: CLI options from Click.
    
    Returns:
        A tuple of (source_type, prompt_content) or None if no prompt is available.
    """
    # Check if there's a prompt file specified
    if options.get("file"):
        file_path = Path(options["file"])
        file_content = file_path.read_text(encoding="utf-8").strip()
        
        # If interactive mode is enabled, this is just the initial content
        if settings.interactive:
            return "file + interactive", file_content
        else:
            return "file", file_content
    
    # Check if there's a direct prompt argument
    if prompt:
        return "argument", prompt
    
    # If interactive mode is enabled, prompt the user
    if settings.interactive:
        try:
            interactive_prompt = Prompt.ask(
                "[bold cyan]Enter your prompt[/bold cyan]", 
                console=console
            )
            return "interactive", interactive_prompt
        except (KeyboardInterrupt, EOFError):
            console.print("[yellow]Prompt input cancelled[/yellow]")
            return None
    
    # No prompt source found
    return None


if __name__ == "__main__":
    cli() 