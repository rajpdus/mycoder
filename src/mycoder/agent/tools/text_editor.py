"""
Text Editor tool for advanced file modifications.

This tool provides more sophisticated file editing capabilities
beyond the basic read/write operations in file_ops.py.
"""

import os
import re
from difflib import unified_diff
from pathlib import Path
from typing import List, Optional, Union

import aiofiles
from pydantic import BaseModel, Field, validator

from .base import Tool


class ReplaceArgs(BaseModel):
    """Arguments for the replace operation."""
    
    file_path: str = Field(
        description="Path to the file to edit"
    )
    search: str = Field(
        description="Text or pattern to search for"
    )
    replacement: str = Field(
        description="Text to replace the matched pattern with"
    )
    regex: bool = Field(
        default=False,
        description="Whether to use regex for search"
    )
    case_sensitive: bool = Field(
        default=True,
        description="Whether the search should be case sensitive"
    )
    
    @validator('file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return str(path.resolve())


class InsertArgs(BaseModel):
    """Arguments for the insert operation."""
    
    file_path: str = Field(
        description="Path to the file to edit"
    )
    content: str = Field(
        description="Content to insert"
    )
    position: int = Field(
        description="Line number where to insert content (1-indexed)"
    )
    
    @validator('file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return str(path.resolve())
    
    @validator('position')
    def validate_position(cls, v):
        if v < 1:
            raise ValueError(f"Position must be at least 1 (1-indexed), got {v}")
        return v


class AppendArgs(BaseModel):
    """Arguments for the append operation."""
    
    file_path: str = Field(
        description="Path to the file to edit"
    )
    content: str = Field(
        description="Content to append to the file"
    )
    
    @validator('file_path')
    def validate_file_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File does not exist: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return str(path.resolve())


class EditResult(BaseModel):
    """Result of text editing operations."""
    
    success: bool = Field(
        description="Whether the edit was successful"
    )
    changes: int = Field(
        description="Number of changes made"
    )
    diff: str = Field(
        description="Unified diff showing the changes made"
    )


class TextEditor(Tool):
    """
    Tool for advanced text editing operations.
    
    This tool provides more sophisticated file editing capabilities
    including regex-based search and replace, insertion at specific
    positions, and appending content.
    """
    
    name = "text_editor"
    description = (
        "Edit text files with advanced operations. This tool allows for "
        "search and replace (with optional regex support), inserting content "
        "at specific line numbers, and appending to files. Returns a diff "
        "showing the changes made."
    )
    args_schema = Union[ReplaceArgs, InsertArgs, AppendArgs]
    returns_schema = EditResult
    
    async def run(self, **kwargs) -> dict:
        """
        Execute the appropriate editing operation based on the arguments.
        
        The operation is determined by inspecting the arguments provided.
        
        Args:
            **kwargs: Arguments specific to the operation
            
        Returns:
            dict: Result of the editing operation
        """
        # Determine which operation to perform based on the arguments
        if 'search' in kwargs and 'replacement' in kwargs:
            return await self._replace(**kwargs)
        elif 'position' in kwargs and 'content' in kwargs:
            return await self._insert(**kwargs)
        elif 'content' in kwargs:
            return await self._append(**kwargs)
        else:
            raise ValueError("Invalid arguments for text_editor")
    
    async def _replace(
        self, 
        file_path: str, 
        search: str, 
        replacement: str,
        regex: bool = False,
        case_sensitive: bool = True
    ) -> dict:
        """
        Perform search and replace in a file.
        
        Args:
            file_path: Path to the file to edit
            search: Text or pattern to search for
            replacement: Text to replace the matched pattern with
            regex: Whether to use regex for search
            case_sensitive: Whether the search should be case sensitive
            
        Returns:
            dict: Result of the editing operation
        """
        # Read the original file
        async with aiofiles.open(file_path, 'r') as file:
            content = await file.read()
        
        # Store original for diff
        original_lines = content.splitlines()
        
        # Perform the search and replace
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(search, flags)
            new_content, count = pattern.subn(replacement, content)
        else:
            if not case_sensitive:
                # Use case-insensitive replace for non-regex
                def replace_case_insensitive(text, old, new):
                    """Case insensitive search and replace."""
                    regex = re.compile(re.escape(old), re.IGNORECASE)
                    return regex.sub(new, text)
                
                new_content, count = replace_case_insensitive(content, search, replacement), content.lower().count(search.lower())
            else:
                new_content = content.replace(search, replacement)
                count = content.count(search)
        
        # Only write if changes were made
        if count > 0:
            async with aiofiles.open(file_path, 'w') as file:
                await file.write(new_content)
        
        # Generate diff
        new_lines = new_content.splitlines()
        diff_lines = list(unified_diff(
            original_lines, new_lines,
            fromfile=f'a/{os.path.basename(file_path)}',
            tofile=f'b/{os.path.basename(file_path)}',
            lineterm=''
        ))
        diff = '\n'.join(diff_lines)
        
        return {
            "success": count > 0,
            "changes": count,
            "diff": diff
        }
    
    async def _insert(self, file_path: str, content: str, position: int) -> dict:
        """
        Insert content at a specific position in a file.
        
        Args:
            file_path: Path to the file to edit
            content: Content to insert
            position: Line number where to insert content (1-indexed)
            
        Returns:
            dict: Result of the editing operation
        """
        # Read the original file
        async with aiofiles.open(file_path, 'r') as file:
            lines = await file.readlines()
        
        # Store original for diff
        original_lines = [line.rstrip('\n') for line in lines]
        
        # Position is 1-indexed, convert to 0-indexed
        position = min(position - 1, len(lines))
        
        # Insert the content
        content_lines = content.split('\n')
        new_lines = lines[:position] + [line + '\n' for line in content_lines] + lines[position:]
        
        # Write the file
        async with aiofiles.open(file_path, 'w') as file:
            await file.writelines(new_lines)
        
        # Generate diff
        new_lines_stripped = [line.rstrip('\n') for line in new_lines]
        diff_lines = list(unified_diff(
            original_lines, new_lines_stripped,
            fromfile=f'a/{os.path.basename(file_path)}',
            tofile=f'b/{os.path.basename(file_path)}',
            lineterm=''
        ))
        diff = '\n'.join(diff_lines)
        
        return {
            "success": True,
            "changes": len(content_lines),
            "diff": diff
        }
    
    async def _append(self, file_path: str, content: str) -> dict:
        """
        Append content to a file.
        
        Args:
            file_path: Path to the file to edit
            content: Content to append to the file
            
        Returns:
            dict: Result of the editing operation
        """
        # Read the original file
        async with aiofiles.open(file_path, 'r') as file:
            original_content = await file.read()
        
        # Store original for diff
        original_lines = original_content.splitlines()
        
        # Append content, ensuring proper newline separation
        if original_content and not original_content.endswith('\n'):
            content = '\n' + content
        
        # Write the file
        async with aiofiles.open(file_path, 'a') as file:
            await file.write(content)
        
        # Read the updated file for diff
        async with aiofiles.open(file_path, 'r') as file:
            new_content = await file.read()
        
        # Generate diff
        new_lines = new_content.splitlines()
        diff_lines = list(unified_diff(
            original_lines, new_lines,
            fromfile=f'a/{os.path.basename(file_path)}',
            tofile=f'b/{os.path.basename(file_path)}',
            lineterm=''
        ))
        diff = '\n'.join(diff_lines)
        
        # Count added lines
        content_lines = content.split('\n')
        changes = len(content_lines)
        if content.startswith('\n'):
            changes += 1
        
        return {
            "success": True,
            "changes": changes,
            "diff": diff
        } 