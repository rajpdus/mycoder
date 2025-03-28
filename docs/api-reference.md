# API Reference

This document provides a detailed reference for the MyCoder-Py API, covering the key classes, methods, and types used across the codebase.

## Agent Module

### Tool System

#### `Tool` (Abstract Base Class)

The base class that all tools must inherit from.

```python
class Tool(ABC):
    name: str                 # The name of the tool
    description: str          # Human-readable description
    args_schema: Type[BaseModel]  # Pydantic model for arguments
    returns_schema: Optional[Type[BaseModel]] = None  # Optional result schema
    
    async def run(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass
    
    async def execute(self, **kwargs) -> Any:
        """Validate arguments and execute the tool."""
        pass
    
    def get_schema_for_llm(self, provider: str = "anthropic") -> Dict[str, Any]:
        """Generate a schema representation for the LLM provider."""
        pass
```

#### `create_tool_from_func`

Factory function to create a Tool class from a regular async function.

```python
def create_tool_from_func(
    func, 
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Type[Tool]:
    """Create a Tool class from a function."""
    pass
```

#### `ToolManager`

Class that manages tool registration and execution.

```python
class ToolManager:
    def register_tool(self, tool_class: Type[Tool]) -> None:
        """Register a tool class."""
        pass
    
    def register_tools(self, tool_classes: List[Type[Tool]]) -> None:
        """Register multiple tool classes at once."""
        pass
    
    def get_tool(self, name: str) -> Tool:
        """Get a registered tool by name."""
        pass
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool with the given name is registered."""
        pass
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        pass
    
    def get_tool_names(self) -> Set[str]:
        """Get the names of all registered tools."""
        pass
    
    def get_tool_schemas_for_llm(self, provider: str = "anthropic") -> List[Dict[str, Any]]:
        """Get schemas for all tools in the format expected by a specific LLM provider."""
        pass
    
    async def execute_tool(
        self, name: str, arguments: Dict[str, Any], handle_errors: bool = True
    ) -> Union[Any, Dict[str, str]]:
        """Execute a tool with the given arguments."""
        pass
```

### Built-in Tools

#### File Operations

```python
class ReadFileTool(Tool):
    """Read the contents of a file."""
    async def run(self, file_path: str, offset: int = 0, limit: Optional[int] = None) -> FileContentsResult:
        pass

class WriteFileTool(Tool):
    """Write content to a file."""
    async def run(self, file_path: str, content: str, mode: str = "w") -> bool:
        pass

class ListDirTool(Tool):
    """List the contents of a directory."""
    async def run(self, dir_path: str, pattern: Optional[str] = None, include_hidden: bool = False) -> DirContentsResult:
        pass
```

#### Shell Commands

```python
class RunCommandTool(Tool):
    """Execute a shell command."""
    async def run(self, command: str, working_dir: Optional[str] = None, timeout: Optional[int] = None, env: Optional[Dict[str, str]] = None) -> ShellCommandResult:
        pass
```

#### User Interaction

```python
class UserPromptTool(Tool):
    """Ask the user for input."""
    async def run(self, message: str, default: Optional[str] = None, password: bool = False, choices: Optional[list[str]] = None) -> str:
        pass

class UserMessageTool(Tool):
    """Display a message to the user."""
    async def run(self, content: str, format: str = "markdown", level: str = "info") -> bool:
        pass
```

### Tool Registration

```python
def get_default_tools() -> List[Type[Tool]]:
    """Get the default set of tools for the agent."""
    pass

def get_tools_by_categories(categories: List[str]) -> List[Type[Tool]]:
    """Get tools from specific categories."""
    pass
```

## LLM Module

### Base Classes

#### `LLMProvider` (Abstract Base Class)

```python
class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the provider."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model being used."""
        pass
    
    @property
    @abstractmethod
    def context_window(self) -> int:
        """Get the context window size of the model in tokens."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        pass
```

#### Message Types

```python
class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(BaseModel):
    """A message in a conversation with the LLM."""
    role: MessageRole
    content: Union[str, MessageContent]
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
```

### Provider Implementations

#### OpenAI

```python
class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""
    pass

def create_openai_provider(
    api_key: Optional[str] = None,
    model: str = "gpt-4-turbo",
    organization: Optional[str] = None
) -> OpenAIProvider:
    """Create an OpenAI provider instance."""
    pass
```

### Factory Functions

```python
def get_provider(provider_name: str) -> type:
    """Get a provider class by name."""
    pass

def create_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Create an LLM provider instance by name."""
    pass
```

## Configuration

### Settings

```python
class Settings(BaseSettings):
    """Main settings class for MyCoder."""
    # LLM provider settings
    provider: LLMProvider
    model: Optional[str]
    max_tokens: int
    temperature: float
    context_window: Optional[int]
    base_url: Optional[str]
    
    # API Keys
    anthropic_api_key: Optional[str]
    openai_api_key: Optional[str]
    
    # Logging and error reporting
    log_level: LogLevel
    token_usage: bool
    sentry_dsn: Optional[str]
    profile: bool
    
    # Feature flags
    github_mode: bool
    interactive: bool
    user_prompt: bool
    upgrade_check: bool
    sub_agent_mode: SubAgentMode
    
    # Browser automation settings
    headless: bool
    user_session: bool
    browser: BrowserSettings
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key for the selected provider."""
        pass
```

## Utilities

### Logging

```python
def configure_logging(
    log_level: Union[LogLevel, str] = LogLevel.INFO,
    show_path: bool = False,
    rich_tracebacks: bool = True,
) -> None:
    """Configure the root logger with rich output."""
    pass

def get_logger(name: str, log_level: Optional[Union[LogLevel, str]] = None) -> logging.Logger:
    """Get a logger with the specified name and log level."""
    pass
```

### Error Handling

```python
def setup_error_handling(enable_sentry: bool = False, sentry_dsn: Optional[str] = None) -> None:
    """Set up global error handling and reporting."""
    pass

def handle_exception(
    e: Exception, 
    exit_on_error: bool = False,
    exit_code: int = 1,
    report_to_sentry: bool = True
) -> None:
    """Handle an exception with nice formatting and optional reporting."""
    pass
```

## Command-Line Interface

### Main CLI

```python
@click.group(invoke_without_command=True)
@click.version_option(package_name="mycoder")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """MyCoder: AI-powered coding assistant."""
    pass

@cli.command("run", help="Execute a prompt or start interactive mode")
@click.argument("prompt", required=False)
@add_shared_options()
def default_command(prompt: Optional[str] = None, **options) -> None:
    """Default command to run the AI agent with a prompt or interactively."""
    pass
```

### Options

```python
def add_shared_options() -> Callable[[F], F]:
    """Decorator function to add shared options to a Click command."""
    pass

def convert_options_to_settings_dict(options: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Click options dict to a format suitable for updating Settings."""
    pass
``` 