"""
Shell command execution tools for MyCoder.

This module provides tools for executing shell commands and interacting
with subprocesses.
"""

import asyncio
import os
import shlex
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from mycoder.agent.tools.base import Tool
from mycoder.utils.errors import ToolExecutionError
from mycoder.utils.logging import get_logger

logger = get_logger("mycoder.agent.tools.shell")


class ShellCommandArgs(BaseModel):
    """Arguments for the run_command tool."""
    
    command: str = Field(
        description="The shell command to execute"
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="Working directory for the command (defaults to current directory)"
    )
    timeout: Optional[int] = Field(
        default=None,
        description="Command timeout in seconds (None means no timeout)"
    )
    env: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional environment variables for the command"
    )
    
    @validator("command")
    def command_must_not_be_empty(cls, v: str) -> str:
        """Validate that the command is not empty."""
        if not v.strip():
            raise ValueError("Command must not be empty")
        return v


class ShellCommandResult(BaseModel):
    """Result of a shell command execution."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float  # seconds
    command: str


class RunCommandTool(Tool):
    """
    Tool for executing shell commands.
    
    This tool runs a shell command and returns its output, exit code, and other details.
    """
    
    name = "run_command"
    description = "Execute a shell command and return its output"
    args_schema = ShellCommandArgs
    returns_schema = ShellCommandResult
    
    async def run(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ShellCommandResult:
        """
        Execute a shell command asynchronously.
        
        Args:
            command: The shell command to execute
            working_dir: Working directory for the command (defaults to current directory)
            timeout: Command timeout in seconds (None means no timeout)
            env: Additional environment variables for the command
            
        Returns:
            ShellCommandResult: Object containing the result of the command execution
            
        Raises:
            ToolExecutionError: If there's an error executing the command
        """
        start_time = time.time()
        logger.debug(f"Executing command: {command}")
        
        try:
            # Prepare environment
            env_vars = os.environ.copy()
            if env:
                env_vars.update(env)
            
            # Prepare working directory
            cwd = None
            if working_dir:
                cwd = Path(working_dir)
                if not cwd.exists():
                    raise ToolExecutionError(
                        message=f"Working directory does not exist: {working_dir}",
                        tool_name=self.name,
                        original_error=None
                    )
            
            # Create and start the process
            process = None
            if os.name == 'nt':  # Windows
                # On Windows, we need to use shell=True to handle commands like 'dir'
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env_vars,
                    cwd=cwd,
                )
            else:  # Unix-like
                # On Unix, parse the command and use create_subprocess_exec for security
                cmd_args = shlex.split(command)
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env_vars,
                    cwd=cwd,
                )
            
            # Wait for process to complete with optional timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                
                # Decode output
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Build result
                result = ShellCommandResult(
                    success=(process.returncode == 0),
                    exit_code=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    duration=duration,
                    command=command
                )
                
                logger.debug(
                    f"Command completed with exit code {result.exit_code} in {result.duration:.2f}s"
                )
                return result
                
            except asyncio.TimeoutError:
                # Try to terminate the process
                try:
                    process.terminate()
                    await asyncio.sleep(0.5)
                    if process.returncode is None:
                        process.kill()
                except Exception:
                    pass
                
                duration = time.time() - start_time
                raise ToolExecutionError(
                    message=f"Command timed out after {timeout} seconds",
                    tool_name=self.name,
                    original_error=None
                )
            
        except ToolExecutionError:
            # Re-raise ToolExecutionError
            raise
        except Exception as e:
            raise ToolExecutionError(
                message="Error executing shell command",
                tool_name=self.name,
                original_error=e
            ) from e
