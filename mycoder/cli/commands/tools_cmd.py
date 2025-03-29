"""
Tools subcommand for MyCoder CLI.

This module provides a command to list all available tools and their capabilities.
"""

import click
from rich.console import Console
from rich.table import Table

from src.mycoder.cli.main import cli

# Initialize console for rich output
console = Console()


@cli.command(name="tools", help="List all available tools and their capabilities")
def tools_command() -> None:
    """
    List all available tools and their capabilities.

    This command retrieves all the registered tools from the ToolManager
    and displays them in a formatted table, showing their names,
    descriptions, parameters, and return schemas.
    """
    console.print("[bold cyan]Available Tools[/bold cyan]")
    console.print()
    
    # Create a table to display tool info
    table = Table(
        title="Available Tools",
        show_header=True,
        header_style="bold magenta",
        box=None,
        title_style="bold cyan",
        expand=True,
    )
    
    # Add columns to the table
    table.add_column("Tool Name", style="bold green", no_wrap=True)
    table.add_column("Description", style="")
    table.add_column("Parameters", style="")
    
    # This is a placeholder until we implement the tool manager
    # We'll list a few sample tools to demonstrate the structure
    sample_tools = [
        {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": "file_path (required): Path to the file to read\noffset (optional): Starting line number\nlimit (optional): Maximum number of lines to read",
        },
        {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": "file_path (required): Path to the file to write\ncontent (required): Text content to write to file\nmode (optional): Write mode (overwrite or append)",
        },
        {
            "name": "run_command",
            "description": "Execute a shell command",
            "parameters": "command (required): The shell command to execute\nworking_dir (optional): Directory to run the command in\ntimeout (optional): Maximum time to wait for command to complete",
        },
        {
            "name": "browse_page",
            "description": "Navigate to and interact with a webpage",
            "parameters": "url (required): The URL to navigate to\nactions (optional): List of actions to perform on the page",
        },
    ]
    
    # Add sample tools to the table
    for tool in sample_tools:
        table.add_row(
            tool["name"],
            tool["description"],
            tool["parameters"],
        )
    
    console.print(table)
    
    console.print()
    console.print(
        "[yellow]Note:[/yellow] This is a placeholder showing sample tools. "
        "The actual tool list will be loaded from the Tool Manager once implemented."
    ) 