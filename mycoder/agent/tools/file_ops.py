"""
File operations tools for MyCoder.

This module provides tools for reading, writing, and manipulating files in
the file system.
"""

import os
from pathlib import Path
from typing import List, Optional, Union

import aiofiles
from pydantic import BaseModel, Field, validator

from src.mycoder.agent.tools.base import Tool
from src.mycoder.utils.errors import ToolExecutionError
from src.mycoder.utils.logging import get_logger

logger = get_logger("mycoder.agent.tools.file_ops")


class ReadFileArgs(BaseModel):
    """Arguments for the read_file tool."""
    
    file_path: str = Field(
        description="Path to the file to read"
    )
    offset: Optional[int] = Field(
        default=0,
        description="Line number to start reading from (0-indexed)"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of lines to read"
    )
    
    @validator("offset")
    def offset_must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        """Validate that offset is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Offset must be non-negative")
        return v
    
    @validator("limit")
    def limit_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that limit is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Limit must be positive")
        return v


class WriteFileArgs(BaseModel):
    """Arguments for the write_file tool."""
    
    file_path: str = Field(
        description="Path to the file to write"
    )
    content: str = Field(
        description="Content to write to the file"
    )
    mode: str = Field(
        default="w",
        description="Write mode: 'w' to overwrite, 'a' to append"
    )
    
    @validator("mode")
    def mode_must_be_valid(cls, v: str) -> str:
        """Validate that mode is either 'w' or 'a'."""
        if v not in ['w', 'a']:
            raise ValueError("Mode must be either 'w' (overwrite) or 'a' (append)")
        return v


class ListDirArgs(BaseModel):
    """Arguments for the list_dir tool."""
    
    dir_path: str = Field(
        description="Path to the directory to list"
    )
    pattern: Optional[str] = Field(
        default=None,
        description="Optional glob pattern to filter files"
    )
    include_hidden: bool = Field(
        default=False,
        description="Whether to include hidden files (starting with .)"
    )


class FileInfo(BaseModel):
    """Information about a file or directory."""
    
    name: str
    path: str
    is_dir: bool
    size: int  # in bytes
    last_modified: float  # timestamp


class FileContentsResult(BaseModel):
    """Result of a file read operation."""
    
    content: str
    file_path: str
    total_lines: int
    start_line: int
    end_line: int


class DirContentsResult(BaseModel):
    """Result of a directory listing operation."""
    
    items: List[FileInfo]
    dir_path: str
    count: int


class ReadFileTool(Tool):
    """
    Tool for reading file contents.
    
    This tool reads a file from the file system and returns its contents.
    """
    
    name = "read_file"
    description = "Read the contents of a file"
    args_schema = ReadFileArgs
    returns_schema = FileContentsResult
    
    async def run(
        self,
        file_path: str,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> FileContentsResult:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file to read
            offset: Line number to start reading from (0-indexed)
            limit: Maximum number of lines to read
            
        Returns:
            FileContentsResult: Object containing the file contents and metadata
            
        Raises:
            ToolExecutionError: If there's an error reading the file
        """
        path = Path(file_path)
        logger.debug(f"Reading file: {path}")
        
        try:
            # Check if file exists
            if not path.exists():
                raise ToolExecutionError(
                    message=f"File does not exist: {file_path}",
                    tool_name=self.name,
                    original_error=None
                )
            
            # Check if path is a file
            if not path.is_file():
                raise ToolExecutionError(
                    message=f"Path is not a file: {file_path}",
                    tool_name=self.name,
                    original_error=None
                )
            
            # Read file contents
            async with aiofiles.open(path, mode='r', encoding='utf-8', errors='replace') as f:
                lines = await f.readlines()
            
            # Apply offset and limit
            total_lines = len(lines)
            start_line = min(offset, total_lines)
            
            if limit is not None:
                end_line = min(start_line + limit, total_lines)
            else:
                end_line = total_lines
            
            # Get the relevant lines
            selected_lines = lines[start_line:end_line]
            content = ''.join(selected_lines)
            
            # Create result
            result = FileContentsResult(
                content=content,
                file_path=str(path),
                total_lines=total_lines,
                start_line=start_line,
                end_line=end_line - 1 if end_line > start_line else start_line
            )
            
            logger.debug(f"Read {end_line - start_line} lines from {path}")
            return result
            
        except ToolExecutionError:
            # Re-raise ToolExecutionError
            raise
        except Exception as e:
            raise ToolExecutionError(
                message=f"Error reading file: {str(e)}",
                tool_name=self.name,
                original_error=e
            ) from e


class WriteFileTool(Tool):
    """
    Tool for writing content to files.
    
    This tool writes content to a file in the file system.
    """
    
    name = "write_file"
    description = "Write content to a file"
    args_schema = WriteFileArgs
    
    async def run(
        self,
        file_path: str,
        content: str,
        mode: str = "w"
    ) -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            mode: Write mode ('w' to overwrite, 'a' to append)
            
        Returns:
            bool: True if the write operation was successful
            
        Raises:
            ToolExecutionError: If there's an error writing to the file
        """
        path = Path(file_path)
        logger.debug(f"Writing to file: {path} (mode: {mode})")
        
        try:
            # Create directory if it doesn't exist
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            async with aiofiles.open(path, mode=mode, encoding='utf-8') as f:
                await f.write(content)
            
            logger.debug(f"Successfully wrote to {path}")
            return True
            
        except Exception as e:
            raise ToolExecutionError(
                message=f"Error writing to file: {str(e)}",
                tool_name=self.name,
                original_error=e
            ) from e


class ListDirTool(Tool):
    """
    Tool for listing directory contents.
    
    This tool lists the contents of a directory in the file system.
    """
    
    name = "list_dir"
    description = "List the contents of a directory"
    args_schema = ListDirArgs
    returns_schema = DirContentsResult
    
    async def run(
        self,
        dir_path: str,
        pattern: Optional[str] = None,
        include_hidden: bool = False
    ) -> DirContentsResult:
        """
        List the contents of a directory.
        
        Args:
            dir_path: Path to the directory to list
            pattern: Optional glob pattern to filter files
            include_hidden: Whether to include hidden files
            
        Returns:
            DirContentsResult: Object containing the directory contents and metadata
            
        Raises:
            ToolExecutionError: If there's an error listing the directory
        """
        path = Path(dir_path)
        logger.debug(f"Listing directory: {path}")
        
        try:
            # Check if directory exists
            if not path.exists():
                raise ToolExecutionError(
                    message=f"Directory does not exist: {dir_path}",
                    tool_name=self.name,
                    original_error=None
                )
            
            # Check if path is a directory
            if not path.is_dir():
                raise ToolExecutionError(
                    message=f"Path is not a directory: {dir_path}",
                    tool_name=self.name,
                    original_error=None
                )
            
            # Get directory contents
            items = []
            
            if pattern:
                entries = list(path.glob(pattern))
            else:
                entries = list(path.iterdir())
            
            # Filter out hidden files if needed
            if not include_hidden:
                entries = [entry for entry in entries if not entry.name.startswith('.')]
            
            # Create FileInfo objects
            for entry in entries:
                try:
                    stat = entry.stat()
                    items.append(
                        FileInfo(
                            name=entry.name,
                            path=str(entry),
                            is_dir=entry.is_dir(),
                            size=stat.st_size,
                            last_modified=stat.st_mtime
                        )
                    )
                except Exception:
                    # Skip entries that can't be accessed
                    continue
            
            # Create result
            result = DirContentsResult(
                items=items,
                dir_path=str(path),
                count=len(items)
            )
            
            logger.debug(f"Listed {len(items)} items in {path}")
            return result
            
        except ToolExecutionError:
            # Re-raise ToolExecutionError
            raise
        except Exception as e:
            raise ToolExecutionError(
                message=f"Error listing directory: {str(e)}",
                tool_name=self.name,
                original_error=e
            ) from e 