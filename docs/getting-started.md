# Getting Started with MyCoder-Py

This guide will help you set up and start using MyCoder-Py, an AI-powered coding assistant leveraging large language models.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry for package management
- For browser automation (optional): Chrome, Firefox, or Safari
- Git (for version control operations)

### Standard Installation

```bash

# Option 1: Install with pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Option 2: Install with Poetry (recommended)
poetry install
```

### Installing Optional Dependencies

For browser automation:

```bash
# With pip
pip install 'mycoder[browser]'
# Or with poetry
poetry install --extras browser

# Install browser binaries
playwright install
```

## Configuration

MyCoder-Py requires configuration for API keys and other settings. Create a `.env` file in the project root:

```env
# At least one of these is required
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Sentry for error reporting
# SENTRY_DSN=your_sentry_dsn_here
```

You can also use command-line options to override settings.

## Basic Usage

### Running with a Prompt

```bash
# Activate your virtual environment if using one
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run with a direct prompt
mycoder "Create a Python function to calculate the Fibonacci sequence"

# Run with a prompt from a file
mycoder -f prompt.txt

# Specify an LLM provider
mycoder --provider openai --model gpt-4 "Create a REST API with FastAPI"
```

### Interactive Mode

Interactive mode allows continuous interaction with the AI assistant:

```bash
mycoder -i
```

## Command-Line Options

MyCoder-Py offers various command-line options:

```
Options:
  --version                       Show the version and exit.
  --log-level, -l [debug|verbose|info|warning|error]
                                  Set minimum logging level  [default: info]
  --profile                       Enable performance profiling of CLI startup
  --provider [anthropic|openai|ollama]
                                  AI model provider to use
  --model TEXT                    AI model name to use (defaults to provider's
                                  default model)
  --max-tokens INTEGER            Maximum number of tokens to generate
  --temperature FLOAT             Temperature for text generation (0.0-1.0)
  --context-window INTEGER        Manual override for context window size in
                                  tokens
  --interactive, -i               Run in interactive mode, asking for prompts
                                  and enabling corrections during execution
                                  (use Ctrl+M to send corrections). Can be
                                  combined with -f/--file to append
                                  interactive input to file content.
  --file, -f FILE                 Read prompt from a file (can be combined
                                  with -i/--interactive)
  --token-usage                   Output token usage at info log level
  --headless BOOLEAN              Use browser in headless mode with no UI
                                  showing
  --user-session BOOLEAN          Use user's existing browser session instead
                                  of sandboxed session
  --user-prompt BOOLEAN           Enable or disable the userPrompt tool for
                                  getting user input during execution
  --upgrade-check BOOLEAN         Enable or disable version upgrade check (for
                                  automated/remote usage)
  --sub-agent-mode [disabled|sync|async]
                                  Sub-agent workflow mode (disabled, sync, or
                                  async)
  --github-mode BOOLEAN           Enable or disable GitHub integration
                                  features (requires git and gh CLI)
  --base-url TEXT                 Base URL for the LLM provider API (mainly
                                  for Ollama)
```

## Viewing Available Tools

To see all available tools:

```bash
mycoder tools
```

## Examples

### Basic Coding Tasks

```bash
# Generate a function
mycoder "Write a Python function to flatten a nested list"

# Create a small project
mycoder "Create a simple Flask web app with SQLite database"
```

### Working with Files

```bash
# Analyze a file
mycoder "Explain what this code does:" -f path/to/file.py

# Improve existing code
mycoder "Optimize this code for performance:" -f path/to/file.py
```

## Troubleshooting

### API Key Issues

If you get API key errors:

1. Check that you've created a `.env` file with the correct keys
2. Ensure the keys are for the correct provider
3. Check for spaces or typos in the keys

### Installation Problems

If you have installation issues:

1. Ensure you're using Python 3.10+
2. Try updating pip: `pip install --upgrade pip`
3. Install development dependencies: `pip install -e ".[dev]"` 