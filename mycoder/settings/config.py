"""
Configuration management for MyCoder.

This module handles loading and validation of configuration from environment 
variables and potentially configuration files.
"""

import enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):
    """Log level options for configuring the logging verbosity."""

    DEBUG = "debug"
    VERBOSE = "verbose"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SubAgentMode(str, enum.Enum):
    """Modes for sub-agent execution workflow."""

    DISABLED = "disabled"
    SYNC = "sync"
    ASYNC = "async"


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class BrowserSettings(BaseModel):
    """Settings for browser automation with Playwright."""

    use_system_browsers: bool = Field(
        default=True,
        description="Whether to use system browsers or Playwright's bundled browsers",
    )
    preferred_type: Literal["chromium", "firefox", "webkit"] = Field(
        default="chromium",
        description="Preferred browser type",
    )
    executable_path: Optional[Path] = Field(
        default=None,
        description="Custom browser executable path (overrides automatic detection)",
    )


class MCPServerAuth(BaseModel):
    """Authentication configuration for MCP servers."""

    type: Literal["bearer", "basic"] = "bearer"
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class MCPServer(BaseModel):
    """Model Context Protocol server configuration."""

    name: str
    url: str
    auth: MCPServerAuth


class MCPSettings(BaseModel):
    """Settings for the Model Context Protocol integration."""

    servers: List[MCPServer] = Field(default_factory=list)
    default_resources: List[str] = Field(default_factory=list)
    default_tools: List[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """
    Main settings class for MyCoder.

    Loads configuration from environment variables and potentially 
    configuration files.
    """

    # LLM provider settings
    provider: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        description="AI model provider to use",
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model name within the provider. If not specified, uses provider default.",
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum number of tokens to generate in a single response",
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for text generation (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    context_window: Optional[int] = Field(
        default=None,
        description="Manual override for context window size in tokens",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for API endpoint (mostly used for Ollama)",
    )

    # API Keys for providers - not defined here with default values for security,
    # instead they're loaded from environment variables
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key",
        alias="ANTHROPIC_API_KEY",
    )

    # Logging and error reporting
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Minimum logging level",
    )
    token_usage: bool = Field(
        default=False,
        description="Whether to output token usage information at info log level",
    )
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error reporting",
        alias="SENTRY_DSN",
    )
    profile: bool = Field(
        default=False,
        description="Enable performance profiling",
    )

    # Feature flags
    github_mode: bool = Field(
        default=True,
        description="Enable GitHub mode for working with issues and PRs",
    )
    interactive: bool = Field(
        default=False,
        description="Enable interactive corrections during agent execution",
    )
    user_prompt: bool = Field(
        default=True,
        description="Enable the userPrompt tool for agent",
    )
    upgrade_check: bool = Field(
        default=True,
        description="Enable check for newer versions of MyCoder",
    )
    sub_agent_mode: SubAgentMode = Field(
        default=SubAgentMode.ASYNC,
        description="Sub-agent workflow mode",
    )

    # Browser automation settings
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode with no UI showing",
    )
    user_session: bool = Field(
        default=False,
        description="Use user's existing browser session instead of sandboxed session",
    )
    browser: BrowserSettings = Field(
        default_factory=BrowserSettings,
        description="Browser detection and configuration settings",
    )

    # MCP settings
    mcp: MCPSettings = Field(
        default_factory=MCPSettings,
        description="Model Context Protocol configuration",
    )

    # System prompt customization
    custom_prompt: Union[str, List[str]] = Field(
        default="",
        description="Custom instructions to append to the system prompt",
    )

    # Extra settings
    extras: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional settings that don't fit into the predefined categories",
    )

    # Define configuration for settings loading
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    def get_api_key(self) -> Optional[str]:
        """
        Get the API key for the selected provider.

        Returns:
            Optional[str]: The API key if available, or None.
        """
        if self.provider == LLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        return None

    @field_validator("custom_prompt")
    @classmethod
    def validate_custom_prompt(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Ensure custom_prompt is properly formatted.

        Args:
            v: The custom prompt value to validate.

        Returns:
            The validated custom prompt.
        """
        if isinstance(v, list):
            return "\n".join(v)
        return v


def load_settings() -> Settings:
    """
    Load and validate settings from environment variables.

    Returns:
        Settings: The loaded and validated settings.
    """
    return Settings() 