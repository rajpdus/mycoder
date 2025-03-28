"""
Tests for the Session tool implementation.
"""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from mycoder.agent.tools.session import Session, SessionArgs, SessionData


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create a temporary directory for session data."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    return session_dir


@pytest.fixture
def session_tool(temp_session_dir):
    """Create a Session tool instance for testing."""
    with patch("mycoder.agent.tools.session.SESSIONS_DIR", str(temp_session_dir)):
        session = Session()
        yield session


def test_session_tool_init():
    """Test initializing the Session tool."""
    session = Session()
    assert session.name == "session"
    assert "manage session data" in session.description.lower()
    assert session.args_schema == SessionArgs


@pytest.mark.asyncio
async def test_save_session_data(session_tool, temp_session_dir):
    """Test saving session data."""
    session_id = "test-session"
    data = {"key": "value", "number": 42}
    
    # Run the session tool to save data
    result = await session_tool.run(
        operation="save",
        session_id=session_id,
        data=data
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "saved" in result["message"].lower()
    
    # Verify the file was created
    session_file = temp_session_dir / f"{session_id}.json"
    assert session_file.exists()
    
    # Verify the file content
    with open(session_file, "r") as f:
        saved_data = json.load(f)
        assert saved_data == data


@pytest.mark.asyncio
async def test_load_session_data(session_tool, temp_session_dir):
    """Test loading session data."""
    session_id = "test-session"
    data = {"key": "value", "number": 42}
    
    # Create a session file
    session_file = temp_session_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(data, f)
    
    # Run the session tool to load data
    result = await session_tool.run(
        operation="load",
        session_id=session_id
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert result["data"] == data


@pytest.mark.asyncio
async def test_load_nonexistent_session(session_tool):
    """Test loading a session that doesn't exist."""
    # Run the session tool to load a nonexistent session
    result = await session_tool.run(
        operation="load",
        session_id="nonexistent-session"
    )
    
    # Verify the result
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_update_session_data(session_tool, temp_session_dir):
    """Test updating session data."""
    session_id = "test-session"
    initial_data = {"key": "value", "number": 42}
    update_data = {"key": "new value", "new_key": "added"}
    
    # Create a session file
    session_file = temp_session_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(initial_data, f)
    
    # Run the session tool to update data
    result = await session_tool.run(
        operation="update",
        session_id=session_id,
        data=update_data
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "updated" in result["message"].lower()
    
    # Verify the file content was updated correctly
    with open(session_file, "r") as f:
        updated_data = json.load(f)
        assert updated_data["key"] == "new value"  # Updated value
        assert updated_data["number"] == 42  # Unchanged value
        assert updated_data["new_key"] == "added"  # New value


@pytest.mark.asyncio
async def test_delete_session_data(session_tool, temp_session_dir):
    """Test deleting session data."""
    session_id = "test-session"
    data = {"key": "value"}
    
    # Create a session file
    session_file = temp_session_dir / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(data, f)
    
    # Run the session tool to delete the session
    result = await session_tool.run(
        operation="delete",
        session_id=session_id
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "deleted" in result["message"].lower()
    
    # Verify the file was deleted
    assert not session_file.exists()


@pytest.mark.asyncio
async def test_delete_nonexistent_session(session_tool):
    """Test deleting a session that doesn't exist."""
    # Run the session tool to delete a nonexistent session
    result = await session_tool.run(
        operation="delete",
        session_id="nonexistent-session"
    )
    
    # Verify the result
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_list_sessions(session_tool, temp_session_dir):
    """Test listing available sessions."""
    # Create some session files
    sessions = ["session1", "session2", "session3"]
    for session_id in sessions:
        session_file = temp_session_dir / f"{session_id}.json"
        with open(session_file, "w") as f:
            json.dump({"id": session_id}, f)
    
    # Run the session tool to list sessions
    result = await session_tool.run(
        operation="list"
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "sessions" in result
    assert len(result["sessions"]) == 3
    assert set(result["sessions"]) == set(sessions)


@pytest.mark.asyncio
async def test_invalid_operation(session_tool):
    """Test providing an invalid operation."""
    # Run the session tool with an invalid operation
    result = await session_tool.run(
        operation="invalid"
    )
    
    # Verify the result
    assert result["status"] == "error"
    assert "invalid operation" in result["error"].lower()


@pytest.mark.asyncio
async def test_save_with_invalid_data(session_tool):
    """Test saving with invalid data."""
    # Run the session tool with invalid data (not JSON serializable)
    class NonSerializable:
        pass
    
    result = await session_tool.run(
        operation="save",
        session_id="test-session",
        data={"invalid": NonSerializable()}
    )
    
    # Verify the result
    assert result["status"] == "error"
    assert "error saving" in result["error"].lower() 