"""
Tests for the Think tool.
"""

import pytest

from mycoder.agent.tools.think import Think, ThinkArgs, ThinkResult


@pytest.fixture
def think_tool():
    """Create a Think tool instance for testing."""
    return Think()


def test_think_tool_init(think_tool):
    """Test that the Think tool initializes correctly."""
    assert think_tool.name == "think"
    assert "reason step-by-step" in think_tool.description
    assert think_tool.args_schema == ThinkArgs
    assert think_tool.returns_schema == ThinkResult


def test_think_args_validation():
    """Test validation of ThinkArgs."""
    # Valid args
    args = ThinkArgs(thought="This is a test thought")
    assert args.thought == "This is a test thought"

    # Empty thought is still valid
    args = ThinkArgs(thought="")
    assert args.thought == ""


@pytest.mark.asyncio
async def test_think_run(think_tool):
    """Test running the Think tool."""
    thought = "I need to analyze this problem step by step. First, I'll check if..."
    result = await think_tool.run(thought=thought)
    
    assert isinstance(result, dict)
    assert "result" in result
    assert f"I have processed your thinking: {thought}" == result["result"]


@pytest.mark.asyncio
async def test_think_execute(think_tool):
    """Test executing the Think tool with validation."""
    thought = "Let me think about this problem carefully."
    result = await think_tool.execute(thought=thought)
    
    assert isinstance(result, dict)
    assert "result" in result
    assert f"I have processed your thinking: {thought}" == result["result"] 