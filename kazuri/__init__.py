"""
Kazuri - Your AI-powered development assistant using AWS Bedrock
"""

from .cli import app, main
from .tools import ToolManager
from .session import Session

__version__ = "0.1.0"
__author__ = "Hillary Murefu"
__email__ = "hillarywang2005@gmail.com"

__all__ = ["app", "main", "ToolManager", "Session"]
