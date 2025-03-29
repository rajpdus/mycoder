"""
Session tool for managing persistent state.

This tool allows the agent to store and retrieve data
across interactions and execution cycles.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .base import Tool


# Global session storage
_session_data: Dict[str, Dict[str, Any]] = {}
_session_dir = None


def set_session_directory(directory: str) -> None:
    """
    Set the directory where session data will be persisted.
    
    Args:
        directory: Path to directory for storing session files
    """
    global _session_dir
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    _session_dir = path


def _get_session_file(session_id: str) -> Path:
    """
    Get the path to the session file.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Path: Path to the session file
    """
    global _session_dir
    if _session_dir is None:
        # Default to .mycoder/sessions in user's home directory
        home = Path.home()
        _session_dir = home / ".mycoder" / "sessions"
        _session_dir.mkdir(parents=True, exist_ok=True)
    
    return _session_dir / f"{session_id}.json"


def _load_session(session_id: str) -> Dict[str, Any]:
    """
    Load a session from disk if it exists.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Dict[str, Any]: Session data or empty dict if not found
    """
    global _session_data
    
    # If already in memory, return it
    if session_id in _session_data:
        return _session_data[session_id]
    
    # Otherwise, try to load from disk
    session_file = _get_session_file(session_id)
    if session_file.exists():
        try:
            with open(session_file, 'r') as f:
                _session_data[session_id] = json.load(f)
            return _session_data[session_id]
        except (json.JSONDecodeError, IOError):
            pass
    
    # If not found or error, create a new empty session
    _session_data[session_id] = {}
    return _session_data[session_id]


def _save_session(session_id: str) -> None:
    """
    Save a session to disk.
    
    Args:
        session_id: Unique session identifier
    """
    global _session_data
    
    if session_id in _session_data:
        session_file = _get_session_file(session_id)
        try:
            with open(session_file, 'w') as f:
                json.dump(_session_data[session_id], f, indent=2)
        except IOError:
            pass


class StoreArgs(BaseModel):
    """Arguments for storing data in a session."""
    
    session_id: str = Field(
        description="Unique session identifier"
    )
    key: str = Field(
        description="Key under which to store the data"
    )
    value: Any = Field(
        description="Data to store (must be JSON serializable)"
    )
    persist: bool = Field(
        default=True,
        description="Whether to persist the session to disk"
    )


class RetrieveArgs(BaseModel):
    """Arguments for retrieving data from a session."""
    
    session_id: str = Field(
        description="Unique session identifier"
    )
    key: str = Field(
        description="Key of the data to retrieve"
    )
    default: Optional[Any] = Field(
        default=None,
        description="Default value to return if key not found"
    )


class ListKeysArgs(BaseModel):
    """Arguments for listing keys in a session."""
    
    session_id: str = Field(
        description="Unique session identifier"
    )


class DeleteArgs(BaseModel):
    """Arguments for deleting data from a session."""
    
    session_id: str = Field(
        description="Unique session identifier"
    )
    key: str = Field(
        description="Key of the data to delete"
    )
    persist: bool = Field(
        default=True,
        description="Whether to persist the session to disk after deletion"
    )


class ClearArgs(BaseModel):
    """Arguments for clearing a session."""
    
    session_id: str = Field(
        description="Unique session identifier"
    )
    persist: bool = Field(
        default=True,
        description="Whether to persist the cleared session to disk"
    )


class SessionResult(BaseModel):
    """Result of session operations."""
    
    success: bool = Field(
        description="Whether the operation was successful"
    )
    message: str = Field(
        description="Message describing the result"
    )
    data: Optional[Any] = Field(
        default=None,
        description="Data returned by the operation"
    )


class Session(Tool):
    """
    Tool for managing persistent state across interactions.
    
    This tool allows storing and retrieving data that persists
    across multiple agent interactions and execution cycles.
    """
    
    name = "session"
    description = (
        "Manage persistent state across interactions. This tool allows you to "
        "store and retrieve data that persists across multiple interactions "
        "and execution cycles. Operations include: store, retrieve, list_keys, "
        "delete, and clear. Each operation requires a session_id parameter."
    )
    args_schema = Union[StoreArgs, RetrieveArgs, ListKeysArgs, DeleteArgs, ClearArgs]
    returns_schema = SessionResult
    
    async def run(self, **kwargs) -> dict:
        """
        Execute the appropriate session operation based on the arguments.
        
        The operation is determined by inspecting the arguments provided.
        
        Args:
            **kwargs: Arguments specific to the session operation
            
        Returns:
            dict: Result of the session operation
        """
        # Determine which operation to perform based on the arguments
        if 'key' in kwargs and 'value' in kwargs:
            return await self._store(**kwargs)
        elif 'key' in kwargs and 'default' in kwargs:
            return await self._retrieve(**kwargs)
        elif 'key' in kwargs:
            return await self._delete(**kwargs)
        elif 'persist' in kwargs:
            return await self._clear(**kwargs)
        else:
            return await self._list_keys(**kwargs)
    
    async def _store(
        self, 
        session_id: str, 
        key: str, 
        value: Any,
        persist: bool = True
    ) -> dict:
        """
        Store data in a session.
        
        Args:
            session_id: Unique session identifier
            key: Key under which to store the data
            value: Data to store (must be JSON serializable)
            persist: Whether to persist the session to disk
            
        Returns:
            dict: Result of the store operation
        """
        try:
            # Ensure the value is JSON serializable
            json.dumps(value)
            
            # Load the session
            session = _load_session(session_id)
            
            # Store the value
            session[key] = value
            
            # Persist to disk if requested
            if persist:
                _save_session(session_id)
            
            return {
                "success": True,
                "message": f"Stored data under key '{key}' in session '{session_id}'"
            }
        except TypeError as e:
            return {
                "success": False,
                "message": f"Failed to store data: Value is not JSON serializable: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to store data: {str(e)}"
            }
    
    async def _retrieve(
        self, 
        session_id: str, 
        key: str, 
        default: Optional[Any] = None
    ) -> dict:
        """
        Retrieve data from a session.
        
        Args:
            session_id: Unique session identifier
            key: Key of the data to retrieve
            default: Default value to return if key not found
            
        Returns:
            dict: Result with the retrieved data
        """
        try:
            # Load the session
            session = _load_session(session_id)
            
            # Check if key exists
            if key in session:
                return {
                    "success": True,
                    "message": f"Retrieved data for key '{key}' from session '{session_id}'",
                    "data": session[key]
                }
            else:
                return {
                    "success": True,
                    "message": f"Key '{key}' not found in session '{session_id}', returning default value",
                    "data": default
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to retrieve data: {str(e)}"
            }
    
    async def _list_keys(self, session_id: str) -> dict:
        """
        List all keys in a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            dict: Result with the list of keys
        """
        try:
            # Load the session
            session = _load_session(session_id)
            
            # Get the keys
            keys = list(session.keys())
            
            return {
                "success": True,
                "message": f"Listed keys from session '{session_id}'",
                "data": keys
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list keys: {str(e)}"
            }
    
    async def _delete(self, session_id: str, key: str, persist: bool = True) -> dict:
        """
        Delete data from a session.
        
        Args:
            session_id: Unique session identifier
            key: Key of the data to delete
            persist: Whether to persist the session to disk after deletion
            
        Returns:
            dict: Result of the delete operation
        """
        try:
            # Load the session
            session = _load_session(session_id)
            
            # Check if key exists
            if key in session:
                # Delete the key
                del session[key]
                
                # Persist to disk if requested
                if persist:
                    _save_session(session_id)
                
                return {
                    "success": True,
                    "message": f"Deleted key '{key}' from session '{session_id}'"
                }
            else:
                return {
                    "success": True,
                    "message": f"Key '{key}' not found in session '{session_id}', nothing to delete"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete data: {str(e)}"
            }
    
    async def _clear(self, session_id: str, persist: bool = True) -> dict:
        """
        Clear all data from a session.
        
        Args:
            session_id: Unique session identifier
            persist: Whether to persist the cleared session to disk
            
        Returns:
            dict: Result of the clear operation
        """
        try:
            # Create a new empty session
            _session_data[session_id] = {}
            
            # Persist to disk if requested
            if persist:
                _save_session(session_id)
            
            return {
                "success": True,
                "message": f"Cleared all data from session '{session_id}'"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clear session: {str(e)}"
            } 