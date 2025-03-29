# MyCoder

An AI-powered coding assistant leveraging large language models.

## Features

- 🤖 **AI-Powered**: Uses Anthropic's Claude for intelligent coding assistance
- 🛠️ **Extensible Tool System**: Modular architecture with various tools for file operations, shell commands, and more
- 🌐 **Web Automation**: Browser automation with Playwright for interacting with web applications
- 🔄 **Parallel Execution**: Can spawn sub-agents for concurrent task processing
- 📝 **Smart Logging**: Hierarchical, color-coded logging system for clear output
- 👤 **Human Compatible**: Uses README files, project files, and shell commands to build context
- 💾 **Session Management**: Persistent state management across interactions
- 🌐 **GitHub Integration**: (Optional) GitHub mode for working with issues and PRs

## Installation

```bash
# Clone the repository

# Install with Poetry (recommended)
poetry install

# Install Playwright browsers
poetry run playwright install

# Or install with pip in a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install
```

## Configuration

MyCoder-Py requires API keys to function with LLM providers. Create a `.env` file in the root directory:

```
# Configure Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# For Ollama, you can set the base URL (defaults to http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434
```

## Usage

```bash
# Run with a prompt
mycoder "Implement a Python function to calculate Fibonacci numbers"

# Run in interactive mode
mycoder -i

# Read prompt from a file
mycoder -f prompt.txt

# Select a specific model
mycoder --model claude-3-opus-20240229 "Create a REST API with FastAPI"

# Use Ollama with a specific model
mycoder --provider ollama --model llama3 "Explain how to use virtual environments in Python"
```

## Available Tools

MyCoder-Py includes a comprehensive set of tools for interacting with your system and the web:

### File Operations
- **Read/Write Files**: Read from and write to files on your system
- **List Directories**: Get directory contents
- **Text Editor**: Advanced text editing operations with regex search/replace

### Shell Operations
- **Run Commands**: Execute shell commands and capture output

### User Interaction
- **Messages**: Display messages to the user
- **Prompts**: Ask the user for input

### Web Tools
- **Browser Automation**: Start browser sessions, navigate to websites, click elements, type text, extract content
- **HTTP Requests**: Make HTTP requests to APIs and websites

### Utility Tools
- **Think**: Internal reasoning without causing side effects
- **Session**: Store and retrieve data across multiple interactions
- **Sleep**: Pause execution for specified periods

## Development

```bash
# Run tests
poetry run pytest

# Type checking
poetry run mypy src

# Linting
poetry run ruff check src
```

## License

MIT 