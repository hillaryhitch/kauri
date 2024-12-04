# Installing and Testing Kazuri

## Local Development Installation

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
.\venv\Scripts\activate
```

3. Install development dependencies:
```bash
make install
```

## AWS Configuration

1. Create a `.env` file from the template:
```bash
cp .env.example .env
```

2. Edit `.env` with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=eu-west-1  # or your preferred region
```

## Testing the Installation

1. Run the test suite:
```bash
make test
```

2. Try a simple command:
```bash
kazuri version
```

3. Test with AWS Bedrock:
```bash
kazuri ask "What is the current working directory?"
```

## Common Issues and Solutions

1. AWS Credentials Error:
```
Error: AWS region not set
```
Solution: Make sure your AWS credentials are properly set in the `.env` file or environment variables.

2. Module Not Found:
```
ModuleNotFoundError: No module named 'kazuri'
```
Solution: Make sure you're in the virtual environment and have run `make install`.

3. Permission Issues:
```
Error: Permission denied
```
Solution: Check your AWS IAM user has the correct permissions (AmazonBedrockFullAccess).

## Development Workflow

1. Make your changes:
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test
```

2. Build documentation:
```bash
# Build docs
make docs

# Serve docs locally
make docs-serve
```

3. Build package:
```bash
make build
```

## Publishing to PyPI

1. Update version in `setup.py`

2. Create and push a tag:
```bash
git tag v0.1.0
git push origin v0.1.0
```

3. GitHub Actions will automatically:
- Run tests
- Build package
- Publish to PyPI (on tag push)
- Deploy documentation

## Using with Git

1. Initialize Git repository:
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Add remote repository:
```bash
git remote add origin https://github.com/yourusername/kazuri.git
git push -u origin main
```

3. Create feature branch:
```bash
git checkout -b feature/new-feature
```

4. Make changes and commit:
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

5. Create pull request on GitHub

## Directory Structure

```
kazuri_dev/
├── kazuri/              # Main package directory
│   ├── __init__.py
│   ├── cli.py          # CLI implementation
│   ├── tools.py        # Tool implementations
│   └── session.py      # Session management
├── tests/              # Test directory
│   └── test_kazuri.py
├── docs/               # Documentation
│   └── index.md
├── .github/            # GitHub Actions
│   └── workflows/
│       └── ci.yml
├── .env.example        # Environment variables template
├── .gitignore         # Git ignore file
├── LICENSE            # MIT License
├── Makefile          # Development commands
├── README.md         # Project readme
├── requirements.txt  # Project dependencies
├── setup.py         # Package setup
└── mkdocs.yml       # Documentation config
