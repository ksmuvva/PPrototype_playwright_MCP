# Playwright MCP Automation

This project implements an AI-powered browser automation agent using the Playwright Model Context Protocol (MCP). It allows using natural language commands to control browser interactions.

## Features

- Natural language to Playwright automation conversion
- Automatic parameter adaptation and error recovery
- Smart element selection strategies
- Extensive debugging and error handling
- Screenshot capture capabilities

## Structure

- `expiremental-new.py`: Main server/client implementation
- `exp_tools.py`: Core Playwright automation tools
- `playwright_function_patches.py`: Fixes for parameter mismatches and JavaScript evaluation
- `param_adapter.py`: Parameter adaptation utilities
- `playwright_adapter.py`: Adapters for Playwright methods
- `updated_screenshot.py` and `updated_smart_click.py`: Enhanced implementations

## Setup

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your `.env` file with:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   MCP_SERVER_COMMAND=python
   MCP_SERVER_ARGS=playwright_server.py
   LLM_MODEL=claude-3-7-sonnet-20250219
   MAX_TOKENS=4096
   ```

3. Run the application:
   ```
   python expiremental-new.py
   ```

## Testing

Test files are located in the `TEST/` directory.

## License

[Specify your license here]
