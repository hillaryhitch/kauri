import pytest
from typer.testing import CliRunner
from kazuri.cli import app
from unittest.mock import patch, MagicMock

runner = CliRunner()

def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Kazuri version: 0.1.0" in result.stdout

@patch('boto3.client')
def test_ask_command(mock_boto3):
    """Test ask command with mocked AWS response."""
    # Mock AWS Bedrock response
    mock_response = {
        'body': MagicMock(
            read=MagicMock(
                return_value='{"content": [{"text": "Here is a simple example..."}]}'
            )
        )
    }
    mock_boto3.return_value.invoke_model.return_value = mock_response

    # Test ask command
    result = runner.invoke(app, ["ask", "Create a simple function"])
    assert result.exit_code == 0
    assert "Kazuri's Response" in result.stdout

@patch('kazuri.tools.ToolManager')
def test_tool_execution(mock_tool_manager):
    """Test tool execution with mocked tool manager."""
    # Mock tool manager response
    mock_tool_manager.return_value.list_files.return_value = {
        "success": True,
        "files": ["file1.py", "file2.py"]
    }

    # Test ask command with tool use
    result = runner.invoke(app, ["ask", "List Python files", "-y"])
    assert result.exit_code == 0

def test_error_handling():
    """Test error handling without AWS credentials."""
    result = runner.invoke(app, ["ask", "Test task"])
    assert result.exit_code == 1
    assert "AWS region not set" in result.stdout

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to set up test environment variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")

def test_aws_config(mock_env):
    """Test AWS configuration with environment variables."""
    from kazuri.cli import get_aws_config
    config = get_aws_config()
    assert config["aws_access_key_id"] == "test_key"
    assert config["aws_secret_access_key"] == "test_secret"
    assert config["region_name"] == "eu-west-1"
