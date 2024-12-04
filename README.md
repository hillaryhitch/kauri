# Kazuri

Kazuri is your AI-powered development assistant using AWS Bedrock's Claude 3 Sonnet model. It helps you with coding tasks, file operations, and development workflows right from your terminal.

## Features

- CLI tool for easy interaction
- AWS Bedrock integration with Claude 3 Sonnet
- Session memory for contextual assistance
- Built-in development tools:
  - File operations (read/write)
  - Code search and analysis
  - System command execution
  - File listing and searching
  - Code definition analysis
  - Browser integration for web development

## Prerequisites

1. Python 3.10 or higher
2. AWS Account with Bedrock access
3. AWS credentials configured with appropriate permissions

## Installation from Git

1. Clone the repository:
```bash
git clone https://github.com/hillaryhitch/kazuri.git
cd kazuri
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## AWS Setup

1. Sign up for AWS and enable Bedrock:
   - Go to AWS Console
   - Search for "Amazon Bedrock"
   - Click "Get started with Amazon Bedrock"
   - Request access to Claude 3 Sonnet model (anthropic.claude-3-sonnet-20240229-v1:0)

2. Create an IAM User with Bedrock access:
   - Go to IAM in AWS Console
   - Create a new user
   - Attach the "AmazonBedrockFullAccess" policy

3. Get your AWS credentials:
   - After creating the IAM user, save the Access Key ID and Secret Access Key
   - These will be used in your .env file or environment variables

4. Configure AWS credentials:

Option 1: Using environment variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_REGION=eu-west-1  # or your preferred region where Claude is available
```

Option 2: Using .env file
```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

## Usage

Once installed and configured, you can use the `kazuri` command from anywhere:

```bash
# Ask for help with a task
kazuri ask "Create a Python function to sort a list of dictionaries by a specific key"

# Show verbose output
kazuri ask -v "How do I implement a binary search tree in Python?"

# Auto-confirm prompts
kazuri ask -y "Create a new React component"

# Check version
kazuri version
```

## Example Usage

1. Creating a new function:
```bash
$ kazuri ask "Create a function to read JSON from a file with error handling"

Tool Request: write_file
Parameters:
  path: json_utils.py
  content: [Function implementation]
Do you want to proceed? [y/n]: y

✨ Function created successfully! Here's how to use it:
import json_utils
data = json_utils.read_json('config.json')
```

2. Code search and analysis:
```bash
$ kazuri ask "Find all TODO comments in the project"

Tool Request: search_files
Parameters:
  path: .
  pattern: TODO|FIXME
Do you want to proceed? [y/n]: y

Found TODOs:
- src/main.py:45: TODO: Add error handling
- tests/test_api.py:12: TODO: Add more test cases
```

3. Web development:
```bash
$ kazuri ask "Create a simple HTML page with a button"

Tool Request: write_file
Parameters:
  path: index.html
  content: [HTML content]
Do you want to proceed? [y/n]: y

Tool Request: browser_action
Parameters:
  action: launch
  url: file:///path/to/index.html
Do you want to proceed? [y/n]: y

✨ Created and tested HTML page successfully!
```

## Development

To contribute to Kazuri:

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/new-feature
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Make your changes and commit:
```bash
git add .
git commit -m "feat: add new feature"
```

5. Push and create a pull request:
```bash
git push origin feature/new-feature
```

## Publishing to PyPI

1. Build the package:
```bash
python setup.py sdist bdist_wheel
```

2. Upload to PyPI:
```bash
twine upload dist/*
```

## License

MIT License - See LICENSE file for details.

## Author

Hillary Murefu (hillarywang2005@gmail.com)
