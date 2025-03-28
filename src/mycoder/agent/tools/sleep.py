"""
Sleep tool for pausing execution.

This tool allows the agent to pause execution for a specified period.
"""

import asyncio
from typing import Optional

from pydantic import BaseModel, Field, validator

from .base import Tool


class SleepArgs(BaseModel):
    """Arguments for the Sleep tool."""
    
    seconds: float = Field(
        description="Number of seconds to sleep"
    )
    
    @validator('seconds')
    def validate_seconds(cls, v):
        """Validate that seconds is a reasonable value."""
        if v < 0:
            raise ValueError("Sleep time cannot be negative")
        if v > 60:
            raise ValueError("Sleep time cannot be more than 60 seconds")
        return v


class SleepResult(BaseModel):
    """Result of the Sleep tool."""
    
    message: str = Field(
        description="Confirmation message after sleeping"
    )


class Sleep(Tool):
    """
    Tool for pausing execution for a specified period.
    
    This tool allows the agent to wait for a certain amount of time
    before continuing with its operation.
    """
    
    name = "sleep"
    description = (
        "Pause execution for a specified number of seconds. "
        "This can be useful when you need to wait before performing "
        "the next action. Maximum sleep time is 60 seconds."
    )
    args_schema = SleepArgs
    returns_schema = SleepResult
    
    async def run(self, seconds: float) -> dict:
        """
        Sleep for the specified number of seconds.
        
        Args:
            seconds: Number of seconds to sleep
            
        Returns:
            dict: Confirmation message after sleeping
        """
        await asyncio.sleep(seconds)
        return {"message": f"Slept for {seconds} seconds"} 