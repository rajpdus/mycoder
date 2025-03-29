"""
Browser tool for web automation.

This tool provides browser automation capabilities using Playwright,
allowing the agent to interact with web pages.
"""

import asyncio
import os
import uuid
from typing import Dict, List, Optional, Union

from playwright.async_api import async_playwright
from pydantic import BaseModel, Field

from .base import Tool


# Global dict to store browser sessions
_browser_sessions: Dict[str, dict] = {}


class StartSessionArgs(BaseModel):
    """Arguments for starting a browser session."""
    
    headless: bool = Field(
        default=True,
        description="Whether to run the browser in headless mode"
    )
    browser_type: str = Field(
        default="chromium",
        description="Type of browser to use (chromium, firefox, webkit)"
    )


class NavigateArgs(BaseModel):
    """Arguments for navigating to a URL."""
    
    session_id: str = Field(
        description="ID of the browser session"
    )
    url: str = Field(
        description="URL to navigate to"
    )
    wait_until: str = Field(
        default="load",
        description="When to consider navigation as finished: 'domcontentloaded', 'load', 'networkidle'"
    )


class ClickArgs(BaseModel):
    """Arguments for clicking an element."""
    
    session_id: str = Field(
        description="ID of the browser session"
    )
    selector: str = Field(
        description="CSS selector for the element to click"
    )
    wait_for_navigation: bool = Field(
        default=True,
        description="Whether to wait for navigation to complete after clicking"
    )


class TypeArgs(BaseModel):
    """Arguments for typing into an element."""
    
    session_id: str = Field(
        description="ID of the browser session"
    )
    selector: str = Field(
        description="CSS selector for the element to type into"
    )
    text: str = Field(
        description="Text to type"
    )
    delay: int = Field(
        default=20,
        description="Delay between keypresses in milliseconds"
    )


class GetContentArgs(BaseModel):
    """Arguments for getting page content."""
    
    session_id: str = Field(
        description="ID of the browser session"
    )
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector for the element to get content from (if omitted, gets full page)"
    )
    content_type: str = Field(
        default="text",
        description="Type of content to get: 'text', 'html', or 'innerText'"
    )


class ScreenshotArgs(BaseModel):
    """Arguments for taking a screenshot."""
    
    session_id: str = Field(
        description="ID of the browser session"
    )
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector for the element to screenshot (if omitted, screenshots full page)"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path where to save the screenshot (if omitted, returns base64)"
    )


class CloseSessionArgs(BaseModel):
    """Arguments for closing a browser session."""
    
    session_id: str = Field(
        description="ID of the browser session to close"
    )


class BrowserResult(BaseModel):
    """Result of browser operations."""
    
    success: bool = Field(
        description="Whether the operation was successful"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID of the browser session"
    )
    message: str = Field(
        description="Message describing the result"
    )
    content: Optional[str] = Field(
        default=None,
        description="Content returned by the operation"
    )
    screenshot: Optional[str] = Field(
        default=None,
        description="Base64-encoded screenshot data"
    )


class Browser(Tool):
    """
    Tool for browser automation using Playwright.
    
    This tool allows the agent to interact with websites, including
    navigation, clicking elements, typing text, extracting content,
    and taking screenshots.
    """
    
    name = "browser"
    description = (
        "Automate web browser interactions. This tool allows you to navigate to websites, "
        "click elements, type text, extract content, and take screenshots. "
        "Operations include: start_session, navigate, click, type, get_content, "
        "screenshot, and close_session. Each operation requires a session_id "
        "except for start_session which creates a new session."
    )
    args_schema = Union[
        StartSessionArgs, 
        NavigateArgs, 
        ClickArgs, 
        TypeArgs, 
        GetContentArgs, 
        ScreenshotArgs, 
        CloseSessionArgs
    ]
    returns_schema = BrowserResult
    
    async def run(self, **kwargs) -> dict:
        """
        Execute the appropriate browser operation based on the arguments.
        
        The operation is determined by inspecting the arguments provided.
        
        Args:
            **kwargs: Arguments specific to the browser operation
            
        Returns:
            dict: Result of the browser operation
        """
        # Determine which operation to perform based on the arguments
        if 'headless' in kwargs and 'browser_type' in kwargs:
            return await self._start_session(**kwargs)
        elif 'url' in kwargs and 'session_id' in kwargs:
            return await self._navigate(**kwargs)
        elif 'selector' in kwargs and 'session_id' in kwargs and 'text' in kwargs:
            return await self._type(**kwargs)
        elif 'selector' in kwargs and 'session_id' in kwargs and 'wait_for_navigation' in kwargs:
            return await self._click(**kwargs)
        elif 'session_id' in kwargs and 'content_type' in kwargs:
            return await self._get_content(**kwargs)
        elif 'session_id' in kwargs and 'path' in kwargs:
            return await self._screenshot(**kwargs)
        elif 'session_id' in kwargs:
            return await self._close_session(**kwargs)
        else:
            raise ValueError("Invalid arguments for browser tool")
    
    async def _start_session(self, headless: bool = True, browser_type: str = "chromium") -> dict:
        """
        Start a new browser session.
        
        Args:
            headless: Whether to run the browser in headless mode
            browser_type: Type of browser to use (chromium, firefox, webkit)
            
        Returns:
            dict: Result with session ID
        """
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize Playwright and browser
        playwright = await async_playwright().start()
        
        # Select browser type
        if browser_type.lower() == "firefox":
            browser = await playwright.firefox.launch(headless=headless)
        elif browser_type.lower() == "webkit":
            browser = await playwright.webkit.launch(headless=headless)
        else:
            browser = await playwright.chromium.launch(headless=headless)
        
        # Create a new page
        page = await browser.new_page()
        
        # Store session data
        _browser_sessions[session_id] = {
            "playwright": playwright,
            "browser": browser,
            "page": page,
            "browser_type": browser_type
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Started {browser_type} browser session"
        }
    
    async def _navigate(self, session_id: str, url: str, wait_until: str = "load") -> dict:
        """
        Navigate to a URL in the specified browser session.
        
        Args:
            session_id: ID of the browser session
            url: URL to navigate to
            wait_until: When to consider navigation as finished
            
        Returns:
            dict: Result of the navigation
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        page = _browser_sessions[session_id]["page"]
        
        # Validate wait_until parameter
        valid_wait_options = ["domcontentloaded", "load", "networkidle"]
        if wait_until not in valid_wait_options:
            wait_until = "load"  # Default to 'load' if invalid
        
        # Navigate to the URL
        try:
            await page.goto(url, wait_until=wait_until)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Navigated to {url}",
                "content": await page.title()
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to navigate to {url}: {str(e)}"
            }
    
    async def _click(self, session_id: str, selector: str, wait_for_navigation: bool = True) -> dict:
        """
        Click an element on the page.
        
        Args:
            session_id: ID of the browser session
            selector: CSS selector for the element to click
            wait_for_navigation: Whether to wait for navigation to complete after clicking
            
        Returns:
            dict: Result of the click operation
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        page = _browser_sessions[session_id]["page"]
        
        try:
            # Wait for the selector to be available
            await page.wait_for_selector(selector, state="visible", timeout=5000)
            
            if wait_for_navigation:
                # Click with navigation
                async with page.expect_navigation():
                    await page.click(selector)
            else:
                # Click without waiting for navigation
                await page.click(selector)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Clicked element '{selector}'",
                "content": await page.title()
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to click element '{selector}': {str(e)}"
            }
    
    async def _type(self, session_id: str, selector: str, text: str, delay: int = 20) -> dict:
        """
        Type text into an element.
        
        Args:
            session_id: ID of the browser session
            selector: CSS selector for the element to type into
            text: Text to type
            delay: Delay between keypresses in milliseconds
            
        Returns:
            dict: Result of the typing operation
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        page = _browser_sessions[session_id]["page"]
        
        try:
            # Wait for the selector to be available
            await page.wait_for_selector(selector, state="visible", timeout=5000)
            
            # Clear the input field first
            await page.fill(selector, "")
            
            # Type the text
            await page.type(selector, text, delay=delay)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Typed text into element '{selector}'"
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to type text into element '{selector}': {str(e)}"
            }
    
    async def _get_content(
        self, 
        session_id: str, 
        content_type: str = "text",
        selector: Optional[str] = None
    ) -> dict:
        """
        Get content from the page or a specific element.
        
        Args:
            session_id: ID of the browser session
            selector: CSS selector for the element to get content from
            content_type: Type of content to get: 'text', 'html', or 'innerText'
            
        Returns:
            dict: Result with the requested content
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        page = _browser_sessions[session_id]["page"]
        
        try:
            if selector:
                # Wait for the selector to be available
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                
                # Get content based on type
                if content_type == "html":
                    content = await page.inner_html(selector)
                elif content_type == "innerText":
                    content = await page.inner_text(selector)
                else:  # Default to text
                    content = await page.text_content(selector)
            else:
                # Get content from full page
                if content_type == "html":
                    content = await page.content()
                else:  # Default to text for full page
                    content = await page.evaluate("document.body.textContent")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Retrieved {content_type} content" + (f" from '{selector}'" if selector else ""),
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to get content: {str(e)}"
            }
    
    async def _screenshot(
        self, 
        session_id: str, 
        path: Optional[str] = None,
        selector: Optional[str] = None
    ) -> dict:
        """
        Take a screenshot of the page or a specific element.
        
        Args:
            session_id: ID of the browser session
            path: Path where to save the screenshot
            selector: CSS selector for the element to screenshot
            
        Returns:
            dict: Result with the screenshot data
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        page = _browser_sessions[session_id]["page"]
        
        try:
            screenshot_options = {}
            
            # Set path if provided
            if path:
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                screenshot_options["path"] = path
            
            # Always return as base64
            screenshot_options["type"] = "jpeg"
            screenshot_options["quality"] = 80
            
            # Take the screenshot
            if selector:
                # Wait for the selector to be available
                await page.wait_for_selector(selector, state="visible", timeout=5000)
                
                # Screenshot specific element
                element = await page.query_selector(selector)
                if element:
                    screenshot = await element.screenshot(**screenshot_options)
                else:
                    raise ValueError(f"Element '{selector}' not found")
            else:
                # Screenshot full page
                screenshot = await page.screenshot(**screenshot_options)
            
            # If path was not provided, return base64 data
            screenshot_data = None
            if not path:
                import base64
                screenshot_data = base64.b64encode(screenshot).decode("utf-8")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Took screenshot" + (f" of element '{selector}'" if selector else "") + (f" and saved to {path}" if path else ""),
                "screenshot": screenshot_data
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to take screenshot: {str(e)}"
            }
    
    async def _close_session(self, session_id: str) -> dict:
        """
        Close a browser session.
        
        Args:
            session_id: ID of the browser session to close
            
        Returns:
            dict: Result of the close operation
        """
        if session_id not in _browser_sessions:
            return {
                "success": False,
                "message": f"Browser session {session_id} not found"
            }
        
        try:
            # Get session components
            session = _browser_sessions[session_id]
            browser = session["browser"]
            playwright = session["playwright"]
            
            # Close browser and playwright
            await browser.close()
            await playwright.stop()
            
            # Remove session from dict
            del _browser_sessions[session_id]
            
            return {
                "success": True,
                "message": f"Closed browser session {session_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "message": f"Failed to close browser session: {str(e)}"
            } 