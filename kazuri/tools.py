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
        # Create a directory for saving generated code
        self.code_dir = Path(self.working_dir) / "generated_code"
        self.code_dir.mkdir(exist_ok=True)
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return [
            "execute_command",
            "read_file",
            "write_to_file",
            "search_files",
            "list_files",
            "list_code_definitions",
            "browser_action"
        ]
    
    def execute_tool(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        try:
            if not isinstance(tool, str):
                return {"success": False, "error": f"Invalid tool type: {type(tool)}"}
            
            if not isinstance(params, dict):
                return {"success": False, "error": f"Invalid parameters type: {type(params)}"}
            
            # Debug logging
            print(f"Executing tool: {tool}")
            print(f"Parameters: {params}")
            
            if tool == "list_files":
                return self.list_files(
                    params.get("path", "."),
                    params.get("recursive", "false").lower() == "true"
                )
            elif tool == "read_file":
                if "path" not in params:
                    return {"success": False, "error": "Path parameter is required"}
                return self.read_file(params["path"])
            elif tool == "write_to_file":
                if "path" not in params or "content" not in params:
                    return {"success": False, "error": "Path and content parameters are required"}
                return self.write_to_file(params["path"], params["content"])
            elif tool == "search_files":
                if "path" not in params or "regex" not in params:
                    return {"success": False, "error": "Path and regex parameters are required"}
                return self.search_files(
                    params["path"],
                    params["regex"],
                    params.get("file_pattern", "*")
                )
            elif tool == "execute_command":
                if "command" not in params:
                    return {"success": False, "error": "Command parameter is required"}
                return self.execute_command(params["command"])
            elif tool == "list_code_definitions":
                if "path" not in params:
                    return {"success": False, "error": "Path parameter is required"}
                return self.list_code_definitions(params["path"])
            elif tool == "browser_action":
                if "action" not in params:
                    return {"success": False, "error": "Action parameter is required"}
                return self.browser_action(params)
            else:
                return {"success": False, "error": f"Unknown tool: {tool}"}
        except Exception as e:
            return {"success": False, "error": f"Tool execution error: {str(e)}"}
    
    def write_to_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file and handle appropriately based on file type."""
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / path
            
            # Create directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the file
            with open(file_path, 'w') as f:
                f.write(content)
            
            result = {
                "success": True,
                "path": str(file_path),
                "error": None
            }
            
            # For Python files, prepare for terminal execution
            if file_path.suffix == '.py':
                if 'import streamlit' in content:
                    result["next_step"] = {
                        "tool": "execute_command",
                        "command": f"streamlit run {file_path}"
                    }
                else:
                    result["next_step"] = {
                        "tool": "execute_command",
                        "command": f"python {file_path}"
                    }
            
            # For web files, prepare for browser testing
            elif file_path.suffix in ['.html', '.htm']:
                result["next_step"] = {
                    "tool": "browser_action",
                    "url": f"file://{file_path.absolute()}"
                }
            
            # For JavaScript files
            elif file_path.suffix == '.js':
                if '<html' in content or 'document.' in content:
                    # Browser JavaScript - create HTML wrapper
                    html_path = file_path.with_suffix('.html')
                    with open(html_path, 'w') as f:
                        f.write(f'''
                        <!DOCTYPE html>
                        <html>
                        <head><title>JavaScript Test</title></head>
                        <body>
                            <h1>JavaScript Test</h1>
                            <script src="{file_path.name}"></script>
                        </body>
                        </html>
                        ''')
                    result["next_step"] = {
                        "tool": "browser_action",
                        "url": f"file://{html_path.absolute()}"
                    }
                else:
                    # Node.js file
                    result["next_step"] = {
                        "tool": "execute_command",
                        "command": f"node {file_path}"
                    }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": None
            }
    
    def execute_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a system command in a visible terminal."""
        try:
            if not isinstance(command, str):
                return {
                    "success": False,
                    "error": f"Invalid command type: {type(command)}",
                    "code": -1
                }
            
            # Set working directory
            work_dir = cwd if cwd else self.working_dir
            
            if os.name == 'nt':  # Windows
                # Always use start command to open new visible terminal
                terminal_command = f'''
                start cmd.exe /K "cd /d {work_dir} && conda activate kazuri && {command} && echo. && echo Press any key to close... && pause > nul"
                '''
            elif os.uname().sysname == "Darwin":  # macOS
                # Always use Terminal.app with conda activation
                escaped_command = command.replace("'", "'\\''")
                terminal_command = f'''
                osascript -e '
                    tell application "Terminal"
                        activate
                        do script "cd {work_dir} && conda activate kazuri && {escaped_command} && echo && echo Press enter to close... && read"
                        set custom title of front window to "Kazuri Terminal"
                    end tell
                '
                '''
            else:  # Linux
                # Try common terminal emulators with conda activation
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                terminal_found = False
                
                for term in terminals:
                    try:
                        subprocess.run(['which', term], check=True, capture_output=True)
                        if term == 'gnome-terminal':
                            terminal_command = f'{term} -- bash -c "cd {work_dir} && conda activate kazuri && {command}; echo; echo Press enter to close...; read"'
                        else:
                            terminal_command = f'{term} -e "cd {work_dir} && conda activate kazuri && {command}; echo; echo Press enter to close...; read"'
                        terminal_found = True
                        break
                    except subprocess.CalledProcessError:
                        continue
                
                if not terminal_found:
                    return {
                        "success": False,
                        "error": "No supported terminal emulator found",
                        "code": -1
                    }
            
            # Run the terminal command
            result = subprocess.run(
                terminal_command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            # Always return success for terminal commands since they run in a new window
            return {
                "success": True,
                "output": "Command running in new terminal window",
                "error": None,
                "code": 0
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "code": -1
            }
    
    def browser_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle browser actions using system browser."""
        try:
            action = params.get("action")
            if not action:
                return {"success": False, "error": "Action parameter is required"}
            
            if action == "launch":
                url = params.get("url")
                if not url:
                    return {"success": False, "error": "URL is required for launch action"}
                
                try:
                    # Handle local files
                    if url.startswith(('file://', '/')):
                        if url.startswith('file://'):
                            file_path = url[7:]
                        else:
                            file_path = url
                        
                        abs_path = os.path.abspath(file_path)
                        if not os.path.exists(abs_path):
                            return {"success": False, "error": f"File not found: {abs_path}"}
                        
                        # Open local file in system browser
                        if os.name == 'nt':  # Windows
                            os.startfile(abs_path)
                        elif os.uname().sysname == "Darwin":  # macOS
                            subprocess.run(["open", abs_path])
                        else:  # Linux
                            subprocess.run(["xdg-open", abs_path])
                    else:
                        # Open URL in system browser
                        if os.name == 'nt':  # Windows
                            os.startfile(url)
                        elif os.uname().sysname == "Darwin":  # macOS
                            subprocess.run(["open", url])
                        else:  # Linux
                            subprocess.run(["xdg-open", url])
                    
                    return {"success": True, "action": "launch", "url": url}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif action == "close":
                return {"success": True, "action": "close"}
            
            else:
                return {"success": False, "error": f"Unknown browser action: {action}"}
        except Exception as e:
            return {"success": False, "error": f"Browser action error: {str(e)}"}
    
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
