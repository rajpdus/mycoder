"""
Tests for the SubAgent tool implementation.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mycoder.agent.tools.sub_agent import SubAgent, SubAgentArgs


@pytest.fixture
def temp_working_dir(tmp_path):
    """Create a temporary working directory for sub-agents."""
    return str(tmp_path)


def test_sub_agent_tool_init():
    """Test initializing the SubAgent tool."""
    tool = SubAgent()
    assert tool.name == "sub_agent"
    assert "subordinate agent" in tool.description.lower()
    assert tool.args_schema == SubAgentArgs


def test_sub_agent_args_validation(temp_working_dir):
    """Test validation of SubAgentArgs."""
    # Valid working directory
    args = SubAgentArgs(
        prompt="Test prompt",
        working_dir=temp_working_dir,
        tools=["file", "shell"],
        wait=True
    )
    assert args.prompt == "Test prompt"
    assert args.working_dir == temp_working_dir
    
    # Non-existent directory
    with pytest.raises(ValueError) as e:
        SubAgentArgs(prompt="Test", working_dir="/non/existent/dir")
    assert "does not exist" in str(e.value)
    
    # File as directory
    temp_file = Path(temp_working_dir) / "test_file"
    temp_file.touch()
    with pytest.raises(ValueError) as e:
        SubAgentArgs(prompt="Test", working_dir=str(temp_file))
    assert "not a directory" in str(e.value) 