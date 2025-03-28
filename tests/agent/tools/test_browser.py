"""
Tests for the Browser tool implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mycoder.agent.tools.browser import (
    Browser,
    BrowserGoToArgs,
    BrowserScreenshotArgs,
    BrowserSelectorArgs,
    BrowserTextArgs
)


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"screenshot_bytes")
    page.content = AsyncMock(return_value="<html><body>Test Content</body></html>")
    page.inner_text = AsyncMock(return_value="Test Text")
    return page


@pytest.fixture
def mock_browser():
    """Create a mock Playwright browser."""
    browser = MagicMock()
    browser.new_page = AsyncMock()
    return browser


@pytest.fixture
def mock_playwright():
    """Create a mock Playwright instance."""
    playwright = MagicMock()
    playwright.chromium = MagicMock()
    playwright.chromium.launch = AsyncMock()
    return playwright


@pytest.fixture
def browser_tool(mock_playwright, mock_browser, mock_page):
    """Create a Browser tool instance for testing."""
    with patch("mycoder.agent.tools.browser.async_playwright", return_value=mock_playwright):
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser
        browser = Browser()
        yield browser


def test_browser_tool_init():
    """Test initializing the Browser tool."""
    browser = Browser()
    assert browser.name == "browser"
    assert "automate browser" in browser.description.lower()
    assert browser.args_schema == BrowserGoToArgs | BrowserScreenshotArgs | BrowserSelectorArgs | BrowserTextArgs


@pytest.mark.asyncio
async def test_goto(browser_tool, mock_page):
    """Test the goto method of the Browser tool."""
    # Run the goto method
    result = await browser_tool.run(
        operation="goto",
        url="https://example.com"
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "Navigated to https://example.com" in result["message"]
    
    # Verify the page call
    mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")


@pytest.mark.asyncio
async def test_screenshot(browser_tool, mock_page):
    """Test the screenshot method of the Browser tool."""
    # Run the screenshot method
    result = await browser_tool.run(
        operation="screenshot",
        selector="body"
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert "screenshot" in result
    assert result["screenshot"].startswith("data:image/png;base64,")
    
    # Verify the page call
    mock_page.screenshot.assert_called_once()


@pytest.mark.asyncio
async def test_content(browser_tool, mock_page):
    """Test the content method of the Browser tool."""
    # Run the content method
    result = await browser_tool.run(
        operation="content"
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert result["content"] == "<html><body>Test Content</body></html>"
    
    # Verify the page call
    mock_page.content.assert_called_once()


@pytest.mark.asyncio
async def test_text(browser_tool, mock_page):
    """Test the text method of the Browser tool."""
    # Run the text method
    result = await browser_tool.run(
        operation="text",
        selector="body"
    )
    
    # Verify the result
    assert result["status"] == "success"
    assert result["text"] == "Test Text"
    
    # Verify the page call
    mock_page.inner_text.assert_called_once_with("body")


@pytest.mark.asyncio
async def test_error_handling(browser_tool, mock_page):
    """Test error handling in the Browser tool."""
    # Make the page.goto method raise an exception
    mock_page.goto.side_effect = Exception("Navigation error")
    
    # Run the goto method
    result = await browser_tool.run(
        operation="goto",
        url="https://example.com"
    )
    
    # Verify the result
    assert result["status"] == "error"
    assert "error" in result
    assert "Navigation error" in result["error"]


@pytest.mark.asyncio
async def test_lazy_initialization(mock_playwright, mock_browser, mock_page):
    """Test that the browser is initialized only when needed."""
    with patch("mycoder.agent.tools.browser.async_playwright", return_value=mock_playwright):
        mock_browser.new_page.return_value = mock_page
        mock_playwright.chromium.launch.return_value = mock_browser
        
        # Create a browser tool without initializing
        browser_tool = Browser()
        
        # Verify that playwright was not initialized
        assert browser_tool._context is None
        assert browser_tool._page is None
        
        # Run a method that requires initialization
        await browser_tool.run(operation="goto", url="https://example.com")
        
        # Verify that playwright was initialized
        assert mock_playwright.chromium.launch.called
        assert mock_browser.new_page.called


@pytest.mark.asyncio
async def test_cleanup(browser_tool, mock_page, mock_browser):
    """Test that the browser resources are cleaned up."""
    # Initialize the browser by using it
    await browser_tool.run(operation="goto", url="https://example.com")
    
    # Call cleanup
    await browser_tool.cleanup()
    
    # Verify that resources were closed
    mock_page.close.assert_called_once()
    mock_browser.close.assert_called_once() 