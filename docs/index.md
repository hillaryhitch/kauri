# Welcome to Kazuri

Kazuri is your AI-powered development assistant that leverages AWS Bedrock's Claude 3 Sonnet model to help you with coding tasks, file operations, and development workflows right from your terminal.

## What is Kazuri?

Kazuri is a command-line tool that combines the power of AWS Bedrock's Claude 3 Sonnet model with a suite of development tools to help you:

- Write and modify code
- Search through codebases
- Execute system commands
- Manage files and directories
- Test web applications
- And much more!

## Key Features

- 🤖 **AI-Powered**: Uses Claude 3 Sonnet through AWS Bedrock for intelligent assistance
- 🧠 **Context-Aware**: Maintains session memory for more relevant responses
- 🛠️ **Built-in Tools**: Includes tools for file operations, code analysis, and system commands
- 🌐 **Browser Integration**: Test web applications directly from the CLI
- 🔄 **Session Management**: Remembers context from previous interactions
- 🚀 **Easy to Use**: Simple CLI interface with rich formatting

## Quick Start

1. Install Kazuri:
```bash
pip install kazuri
```

2. Set up AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=eu-west-1  # or your preferred region
```

3. Start using Kazuri:
```bash
kazuri ask "Create a Python function to read JSON from a file"
```

## Example Usage

Here's a simple example of using Kazuri to create and test a web component:

```bash
# Create a new React component
kazuri ask "Create a React button component with hover effects"

# Test the component in browser
kazuri ask "Test the button component we just created"

# Make modifications based on feedback
kazuri ask "Add a ripple effect to the button when clicked"
```

## Project Status

Kazuri is currently in active development. We welcome contributions from the community!

## Getting Started

Check out our [Installation Guide](getting-started/installation.md) to get started with Kazuri.

## Support

If you encounter any issues or have questions:

1. Check the [Documentation](https://hillaryhitch.github.io/kazuri)
2. Open an [Issue](https://github.com/hillaryhitch/kazuri/issues)
3. Join our [Community Discussions](https://github.com/hillaryhitch/kazuri/discussions)

## Contributing

We welcome contributions! See our [Contributing Guide](development/contributing.md) for details.

## License

Kazuri is released under the MIT License. See the [LICENSE](https://github.com/hillaryhitch/kazuri/blob/main/LICENSE) file for details.
