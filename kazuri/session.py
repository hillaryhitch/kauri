import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

class Session:
    """Manages session state and conversation history."""
    
    def __init__(self, session_dir: str = ".kazuri_sessions"):
        """Initialize session manager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        # Create artifacts directory for storing generated files
        self.artifacts_dir = self.session_dir / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.history = []
        self.saved_files = {}  # Track saved files and their metadata
        self.load_or_create_session()
    
    def load_or_create_session(self):
        """Load existing session or create new one."""
        # Find most recent session file
        session_files = list(self.session_dir.glob("session_*.json"))
        if session_files:
            latest_session = max(session_files, key=lambda x: x.stat().st_mtime)
            # If session is older than 1 hour, create new one
            if (datetime.now().timestamp() - latest_session.stat().st_mtime) > 3600:
                self.create_new_session()
            else:
                self.current_session = latest_session
                with open(latest_session, 'r') as f:
                    try:
                        data = json.load(f)
                        # Handle both old format (list) and new format (dict)
                        if isinstance(data, list):
                            self.history = data
                            self.saved_files = {}
                        else:
                            self.history = data.get('history', [])
                            self.saved_files = data.get('saved_files', {})
                    except json.JSONDecodeError:
                        # If file is corrupted, create new session
                        self.create_new_session()
        else:
            self.create_new_session()
    
    def create_new_session(self):
        """Create a new session file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = self.session_dir / f"session_{timestamp}.json"
        self.history = []
        self.saved_files = {}
        self.save_session()
    
    def add_interaction(self, task: str, response: str, tool_uses: Optional[List[Dict[str, Any]]] = None):
        """Add a new interaction to the session history.
        
        Args:
            task: The user's task or question
            response: Kazuri's response
            tool_uses: List of tools used and their results
        """
        # Ensure tool_uses is a list of dictionaries
        if tool_uses is None:
            tool_uses = []
        elif not isinstance(tool_uses, list):
            tool_uses = []
        
        # Validate each tool use
        validated_tool_uses = []
        for tool_use in tool_uses:
            if isinstance(tool_use, dict):
                # Ensure required fields exist
                validated_tool_use = {
                    "tool": tool_use.get("tool", "unknown_tool"),
                    "parameters": tool_use.get("parameters", {}),
                    "result": tool_use.get("result", "No result")
                }
                validated_tool_uses.append(validated_tool_use)
        
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "response": response,
            "tool_uses": validated_tool_uses
        })
        self.save_session()
    
    def save_session(self):
        """Save current session to file."""
        with open(self.current_session, 'w') as f:
            json.dump({
                'history': self.history,
                'saved_files': self.saved_files
            }, f, indent=2)
    
    def save_generated_content(self, content: str, filename: str, description: str = "", content_type: str = "code") -> str:
        """Save generated content to a file in the artifacts directory.
        
        Args:
            content: The content to save
            filename: Desired filename
            description: Optional description of the content
            content_type: Type of content (e.g., 'code', 'text', 'config')
            
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = self.artifacts_dir / safe_filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.saved_files[safe_filename] = {
            'original_name': filename,
            'description': description,
            'type': content_type,
            'timestamp': timestamp,
            'path': str(file_path)
        }
        self.save_session()
        
        return str(file_path)
    
    def save_file_copy(self, source_path: str, description: str = "") -> str:
        """Save a copy of an existing file to the artifacts directory.
        
        Args:
            source_path: Path to the source file
            description: Optional description of the file
            
        Returns:
            Path to the saved copy
        """
        source = Path(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{source.name}"
        dest_path = self.artifacts_dir / safe_filename
        
        shutil.copy2(source, dest_path)
        
        self.saved_files[safe_filename] = {
            'original_name': source.name,
            'description': description,
            'type': 'file_copy',
            'timestamp': timestamp,
            'path': str(dest_path)
        }
        self.save_session()
        
        return str(dest_path)
    
    def get_saved_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about a saved file.
        
        Args:
            filename: Name of the saved file
            
        Returns:
            Dictionary containing file metadata or None if not found
        """
        return self.saved_files.get(filename)
    
    def list_saved_files(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved files, optionally filtered by type.
        
        Args:
            content_type: Optional filter by content type
            
        Returns:
            List of file metadata dictionaries
        """
        if content_type:
            return [
                {**metadata, 'filename': filename}
                for filename, metadata in self.saved_files.items()
                if metadata['type'] == content_type
            ]
        return [
            {**metadata, 'filename': filename}
            for filename, metadata in self.saved_files.items()
        ]
    
    def get_recent_context(self, limit: int = 5) -> str:
        """Get recent conversation context.
        
        Args:
            limit: Maximum number of recent interactions to include
        
        Returns:
            String containing recent conversation history
        """
        if not self.history:
            return ""
        
        recent = self.history[-limit:]
        context = []
        for interaction in recent:
            context.append(f"Human: {interaction.get('task', '')}")
            context.append(f"Assistant: {interaction.get('response', '')}")
            tool_uses = interaction.get('tool_uses', [])
            if tool_uses:
                context.append("Tool Uses:")
                for tool_use in tool_uses:
                    if isinstance(tool_use, dict):
                        tool_name = tool_use.get('tool', 'unknown_tool')
                        result = tool_use.get('result', 'No result')
                        context.append(f"- {tool_name}: {result}")
        
        return "\n\n".join(context)
    
    def get_last_response(self) -> Optional[str]:
        """Get the last response from history."""
        if self.history:
            return self.history[-1].get("response")
        return None
    
    def get_last_tool_uses(self) -> List[Dict[str, Any]]:
        """Get the last tool uses from history."""
        if self.history:
            return self.history[-1].get("tool_uses", [])
        return []
    
    def clear_history(self):
        """Clear the current session history."""
        self.history = []
        self.save_session()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        return {
            "session_file": str(self.current_session),
            "interaction_count": len(self.history),
            "saved_files_count": len(self.saved_files),
            "start_time": self.history[0].get("timestamp") if self.history else None,
            "last_interaction": self.history[-1].get("timestamp") if self.history else None
        }
    
    def export_session(self, output_file: str):
        """Export the current session to a file.
        
        Args:
            output_file: Path to save the exported session
        """
        with open(output_file, 'w') as f:
            json.dump({
                "session_info": self.get_session_info(),
                "history": self.history,
                "saved_files": self.saved_files
            }, f, indent=2)
    
    def import_session(self, input_file: str):
        """Import a session from a file.
        
        Args:
            input_file: Path to the session file to import
        """
        with open(input_file, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict) and "history" in data:
                    self.history = data["history"]
                    self.saved_files = data.get("saved_files", {})
                    self.save_session()
                else:
                    raise ValueError("Invalid session file format")
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in session file")
