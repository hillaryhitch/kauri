import pytest
import os
import json
from pathlib import Path
from typer.testing import CliRunner
from kazuri.cli import app
from kazuri.session import Session
from unittest.mock import patch, MagicMock

runner = CliRunner()

@pytest.fixture
def temp_session_dir(tmp_path):
    """Fixture to provide temporary session directory."""
    return str(tmp_path / "test_sessions")

@pytest.fixture
def session(temp_session_dir):
    """Fixture to provide a test session instance."""
    return Session(session_dir=temp_session_dir)

def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Kazuri version: 0.1.1" in result.stdout

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

def test_session_initialization(temp_session_dir):
    """Test session initialization and directory creation."""
    session = Session(session_dir=temp_session_dir)
    assert Path(temp_session_dir).exists()
    assert (Path(temp_session_dir) / "artifacts").exists()
    assert session.current_session is not None

def test_save_generated_content(session):
    """Test saving generated content."""
    content = "def test_function():\n    return 'Hello, World!'"
    filepath = session.save_generated_content(
        content=content,
        filename="test_function.py",
        description="Test function implementation",
        content_type="code"
    )
    
    # Verify file was saved
    assert Path(filepath).exists()
    with open(filepath) as f:
        assert f.read() == content
    
    # Verify metadata was saved
    saved_files = session.list_saved_files()
    assert len(saved_files) == 1
    assert saved_files[0]['original_name'] == "test_function.py"
    assert saved_files[0]['type'] == "code"

def test_save_file_copy(session, tmp_path):
    """Test saving a copy of an existing file."""
    # Create a test file
    source_file = tmp_path / "source.txt"
    source_content = "Test content"
    source_file.write_text(source_content)
    
    # Save a copy
    filepath = session.save_file_copy(
        source_path=str(source_file),
        description="Test file copy"
    )
    
    # Verify copy was saved
    assert Path(filepath).exists()
    with open(filepath) as f:
        assert f.read() == source_content
    
    # Verify metadata was saved
    saved_files = session.list_saved_files(content_type="file_copy")
    assert len(saved_files) == 1
    assert saved_files[0]['original_name'] == "source.txt"

def test_session_history_persistence(temp_session_dir):
    """Test that session history persists between instances."""
    # Create first session and add interaction
    session1 = Session(session_dir=temp_session_dir)
    session1.add_interaction(
        task="Test task",
        response="Test response",
        tool_uses=[{"tool": "test_tool", "result": "success"}]
    )
    
    # Create new session instance and verify history loaded
    session2 = Session(session_dir=temp_session_dir)
    assert len(session2.history) == 1
    assert session2.history[0]["task"] == "Test task"
    assert session2.history[0]["response"] == "Test response"

def test_session_export_import(session, tmp_path):
    """Test session export and import functionality."""
    # Add some data to the session
    session.add_interaction("Test task", "Test response")
    session.save_generated_content("test content", "test.txt")
    
    # Export session
    export_file = tmp_path / "export.json"
    session.export_session(str(export_file))
    
    # Create new session and import
    new_session = Session(session_dir=str(tmp_path / "new_session"))
    new_session.import_session(str(export_file))
    
    # Verify data was imported
    assert len(new_session.history) == 1
    assert len(new_session.saved_files) == 1
    assert new_session.history[0]["task"] == "Test task"

def test_get_recent_context(session):
    """Test getting recent conversation context."""
    # Add multiple interactions
    for i in range(10):
        session.add_interaction(f"Task {i}", f"Response {i}")
    
    # Get recent context with default limit
    context = session.get_recent_context()
    assert len(context.split("Human: ")) == 6  # 5 recent interactions + empty string from split
    
    # Get recent context with custom limit
    context = session.get_recent_context(limit=3)
    assert len(context.split("Human: ")) == 4  # 3 recent interactions + empty string from split

def test_list_saved_files_filtering(session):
    """Test filtering saved files by type."""
    # Save different types of content
    session.save_generated_content("code content", "test.py", content_type="code")
    session.save_generated_content("config content", "test.json", content_type="config")
    
    # Test filtering
    code_files = session.list_saved_files(content_type="code")
    assert len(code_files) == 1
    assert code_files[0]['type'] == "code"
    
    config_files = session.list_saved_files(content_type="config")
    assert len(config_files) == 1
    assert config_files[0]['type'] == "config"
    
    all_files = session.list_saved_files()
    assert len(all_files) == 2
