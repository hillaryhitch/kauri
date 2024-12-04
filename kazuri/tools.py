import os
import re
import glob
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

class ToolManager:
    """Manages the execution of various tools available to Kazuri."""
    
    def __init__(self):
        self.working_dir = os.getcwd()
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return [
            "execute_command",
            "read_file",
            "write_file",
            "search_files",
            "list_files",
            "list_code_definitions",
            "browser_action"
        ]
    
    def execute_tool(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        if tool == "list_files":
            return self.list_files(
                params.get("path", "."),
                params.get("recursive", "false").lower() == "true"
            )
        elif tool == "read_file":
            return self.read_file(params["path"])
        elif tool == "write_file":
            return self.write_file(params["path"], params["content"])
        elif tool == "search_files":
            return self.search_files(
                params["path"],
                params["regex"],
                params.get("file_pattern", "*")
            )
        elif tool == "execute_command":
            return self.execute_command(params["command"])
        elif tool == "list_code_definitions":
            return self.list_code_definitions(params["path"])
        else:
            return {"success": False, "error": f"Unknown tool: {tool}"}
    
    def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a system command safely."""
        try:
            # Set working directory
            work_dir = cwd if cwd else self.working_dir
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "code": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "code": -1
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file contents safely."""
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / path
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                    "content": None
                }
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file safely."""
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / path
            
            # Create directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "error": None,
                "path": str(file_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
    
    def search_files(self, path: str, pattern: str, file_pattern: str = "*") -> Dict[str, Any]:
        """Search files with pattern matching."""
        try:
            results = []
            search_path = Path(path)
            if not search_path.is_absolute():
                search_path = Path(self.working_dir) / path
            
            for file_path in search_path.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content.count('\n', 0, match.start()) + 1
                                results.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'match': match.group(),
                                    'context': self._get_context(content, match.start())
                                })
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            return {
                "success": True,
                "results": results,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": str(e)
            }
    
    def list_files(self, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
        """List files in directory."""
        try:
            list_path = Path(path)
            if not list_path.is_absolute():
                list_path = Path(self.working_dir) / path
            
            if recursive:
                files = [str(p.relative_to(list_path)) for p in list_path.rglob("*") if p.is_file()]
            else:
                files = [str(p.relative_to(list_path)) for p in list_path.glob("*") if p.is_file()]
            
            return {
                "success": True,
                "files": sorted(files),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "error": str(e)
            }
    
    def list_code_definitions(self, path: str) -> Dict[str, Any]:
        """List code definitions in files."""
        try:
            definitions = []
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / path
            
            if not file_path.exists():
                return {
                    "success": False,
                    "definitions": [],
                    "error": f"File not found: {path}"
                }
            
            # Simple regex patterns for common definitions
            patterns = {
                'function': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'class': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]',
                'variable': r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'
            }
            
            with open(file_path, 'r') as f:
                content = f.read()
                
                for def_type, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        definitions.append({
                            'type': def_type,
                            'name': match.group(1),
                            'line': content.count('\n', 0, match.start()) + 1
                        })
            
            return {
                "success": True,
                "definitions": sorted(definitions, key=lambda x: x['line']),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "definitions": [],
                "error": str(e)
            }
    
    def _get_context(self, content: str, position: int, context_lines: int = 2) -> str:
        """Get context around a match position."""
        lines = content.split('\n')
        line_num = content.count('\n', 0, position)
        
        start = max(0, line_num - context_lines)
        end = min(len(lines), line_num + context_lines + 1)
        
        return '\n'.join(lines[start:end])
