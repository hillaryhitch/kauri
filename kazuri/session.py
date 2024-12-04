import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class Session:
    """Manages session state and conversation history."""
    
    def __init__(self, session_dir: str = ".kazuri_sessions"):
        """Initialize session manager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.current_session = None
        self.history = []
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
                    self.history = json.load(f)
        else:
            self.create_new_session()
    
    def create_new_session(self):
        """Create a new session file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = self.session_dir / f"session_{timestamp}.json"
        self.history = []
        self.save_session()
    
    def add_interaction(self, task: str, response: str, tool_uses: Optional[List[Dict[str, Any]]] = None):
        """Add a new interaction to the session history.
        
        Args:
            task: The user's task or question
            response: Kazuri's response
            tool_uses: List of tools used and their results
        """
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "response": response,
            "tool_uses": tool_uses or []
        })
        self.save_session()
    
    def save_session(self):
        """Save current session to file."""
        with open(self.current_session, 'w') as f:
            json.dump(self.history, f, indent=2)
    
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
            context.append(f"Human: {interaction['task']}")
            context.append(f"Assistant: {interaction['response']}")
            if interaction['tool_uses']:
                context.append("Tool Uses:")
                for tool_use in interaction['tool_uses']:
                    context.append(f"- {tool_use['tool']}: {tool_use.get('result', 'No result')}")
        
        return "\n\n".join(context)
    
    def get_last_response(self) -> Optional[str]:
        """Get the last response from history."""
        if self.history:
            return self.history[-1]["response"]
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
            "start_time": self.history[0]["timestamp"] if self.history else None,
            "last_interaction": self.history[-1]["timestamp"] if self.history else None
        }
    
    def export_session(self, output_file: str):
        """Export the current session to a file.
        
        Args:
            output_file: Path to save the exported session
        """
        with open(output_file, 'w') as f:
            json.dump({
                "session_info": self.get_session_info(),
                "history": self.history
            }, f, indent=2)
    
    def import_session(self, input_file: str):
        """Import a session from a file.
        
        Args:
            input_file: Path to the session file to import
        """
        with open(input_file, 'r') as f:
            data = json.load(f)
            if "history" in data:
                self.history = data["history"]
                self.save_session()
            else:
                raise ValueError("Invalid session file format")
