import os
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from pathlib import Path
from typing import Optional, List, Dict, Any
import boto3
import json
import re
from dotenv import load_dotenv
from .tools import ToolManager
from .session import Session

# Load environment variables from .env file
load_dotenv()

# Initialize typer app and rich console
app = typer.Typer(help="Kazuri - Your AI-powered development assistant")
console = Console()
tool_manager = ToolManager()
session = Session()

# Version number
VERSION = "0.1.2"

def get_aws_config() -> Dict[str, str]:
    """Get AWS configuration from environment variables."""
    config = {
        'service_name': 'bedrock-runtime',
        'region_name': os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION'),
        'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'aws_session_token': os.getenv('AWS_SESSION_TOKEN')  # Optional for temporary credentials
    }
    
    # Remove None values
    return {k: v for k, v in config.items() if v is not None}

def load_system_prompt() -> str:
    """Load the system prompt from file."""
    prompt_path = Path(__file__).parent / "system_prompt.txt"
    with open(prompt_path, 'r') as f:
        return f.read()

def format_task_for_claude(task: str, environment_details: Optional[str] = None) -> str:
    # Load system prompt from file
    system_prompt = load_system_prompt()
    
    # Get recent conversation history
    recent_context = session.get_recent_context(limit=5)
    
    prompt = f"{system_prompt}\n\n"
    
    # Add recent conversation history if available
    if recent_context:
        prompt += f"Recent Conversation History:\n{recent_context}\n\n"
    
    prompt += f"Human: {task}"
    
    if environment_details:
        prompt += f"\n\nEnvironment Details:\n{environment_details}"
    
    return prompt

def get_environment_details():
    """Gather relevant environment details."""
    details = []
    
    # Add current working directory files
    details.append("# Current Working Directory Files")
    try:
        files = tool_manager.list_files(".")
        if files["success"]:
            details.extend(files["files"])
    except Exception:
        pass
    
    # Add VSCode visible files and open tabs if available
    details.append("\n# VSCode Context")
    details.append("(Add any relevant VSCode context)")
    
    # Add any active tool uses from recent history
    recent_tool_uses = session.get_last_tool_uses()
    if recent_tool_uses:
        details.append("\n# Recent Tool Uses")
        for tool_use in recent_tool_uses:
            details.append(f"- {tool_use.get('tool', 'Unknown')}: {tool_use.get('result', 'No result')}")
    
    return "\n".join(details)

def extract_code_block(text: str, start_idx: int) -> tuple[str, int]:
    """Extract a code block from text starting at start_idx."""
    lines = text[start_idx:].split('\n')
    code_lines = []
    end_idx = start_idx
    
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('</'):
            code_lines.append(line)
            end_idx = start_idx + sum(len(l) + 1 for l in lines[:i+1])
        elif line.strip().startswith('</'):
            break
    
    return '\n'.join(code_lines), end_idx

def process_tool_use(response: str):
    """Process any tool use requests in the response."""
    try:
        # First check for proper XML format
        if "<tool_name>" in response:
            tool_start = response.find("<tool_name>")
            tool_end = response.find("</tool_name>")
            if tool_start != -1 and tool_end != -1:
                tool_name = response[tool_start + 11:tool_end].strip()
                
                # Extract parameters
                params = {}
                param_start = response.find("<", tool_end)
                while param_start != -1:
                    param_end = response.find(">", param_start)
                    if param_end == -1:
                        break
                    
                    param_name = response[param_start + 1:param_end]
                    if param_name.startswith('/'):  # Skip closing tags
                        param_start = response.find("<", param_end)
                        continue
                        
                    content_start = param_end + 1
                    content_end = response.find(f"</{param_name}>", content_start)
                    if content_end == -1:
                        break
                    
                    params[param_name] = response[content_start:content_end].strip()
                    param_start = response.find("<", content_end)
                
                return {
                    "tool": tool_name,
                    "parameters": params
                }
        
        # Check for alternative format: <write_file> filename: path
        write_file_match = re.search(r'<write_file>\s*filename:\s*([^\n]+)', response)
        if write_file_match:
            filename = write_file_match.group(1).strip()
            code_start = write_file_match.end()
            code, _ = extract_code_block(response, code_start)
            
            # Convert to proper format
            return {
                "tool": "write_to_file",
                "parameters": {
                    "path": filename,
                    "content": code.strip()
                }
            }
        
        return None
    except Exception as e:
        console.print(f"[red]Error processing tool use: {str(e)}[/red]")
        return None

def execute_tool(tool_use: Optional[Dict[str, Any]], yes: bool = False) -> Dict[str, Any]:
    """Execute the specified tool with given parameters."""
    try:
        if not tool_use:
            return {"success": False, "error": "No tool use specified"}
        
        if not isinstance(tool_use, dict):
            return {"success": False, "error": f"Invalid tool use type: {type(tool_use)}"}
        
        tool_name = tool_use.get("tool")
        if not tool_name:
            return {"success": False, "error": "Tool name not specified"}
        
        params = tool_use.get("parameters", {})
        if not isinstance(params, dict):
            return {"success": False, "error": f"Invalid parameters type: {type(params)}"}
        
        # Show tool details and get confirmation
        console.print("\n[yellow]Tool Request:[/yellow]")
        console.print(f"Tool: {tool_name}")
        console.print("Parameters:")
        for key, value in params.items():
            if key == "content":
                console.print(f"  {key}: <code content follows>")
                console.print(Panel(value, title="Code Content"))
            else:
                console.print(f"  {key}: {value}")
        
        # Special handling for code-related tools
        if tool_name == "write_to_file":
            console.print("\n[yellow]Would you like to save this code to disk?[/yellow]")
            if yes or Confirm.ask("Save code?"):
                result = tool_manager.execute_tool(tool_name, params)
                if result.get("success"):
                    console.print(f"[green]Code saved to: {result.get('path')}[/green]")
                    
                    # If there's a next step suggested (like running the code)
                    if result.get("next_step"):
                        next_step = result["next_step"]
                        next_tool = next_step.get("tool")
                        if next_tool == "execute_command":
                            console.print("\n[yellow]Would you like to run this code in a visible terminal?[/yellow]")
                            if yes or Confirm.ask("Run code?"):
                                run_result = tool_manager.execute_command(next_step["command"])
                                result["run_result"] = run_result
                        elif next_tool == "browser_action":
                            console.print("\n[yellow]Would you like to open this in your browser?[/yellow]")
                            if yes or Confirm.ask("Open in browser?"):
                                browser_result = tool_manager.browser_action({
                                    "action": "launch",
                                    "url": next_step["url"]
                                })
                                result["browser_result"] = browser_result
                
                return result
            return {"success": False, "error": "Code save cancelled by user"}
        
        # Special handling for browser and terminal actions
        elif tool_name == "browser_action":
            console.print("\n[yellow]Would you like to open this in your browser?[/yellow]")
            if yes or Confirm.ask("Open browser?"):
                result = tool_manager.browser_action(params)
                if result.get("success"):
                    console.print("[green]Browser opened successfully![/green]")
                return result
            return {"success": False, "error": "Browser action cancelled by user"}
        
        elif tool_name == "execute_command":
            console.print("\n[yellow]Would you like to run this command in a visible terminal?[/yellow]")
            if yes or Confirm.ask("Run in terminal?"):
                result = tool_manager.execute_command(params["command"])
                if result.get("success"):
                    console.print("[green]Command executed successfully![/green]")
                return result
            return {"success": False, "error": "Command execution cancelled by user"}
        
        # For other tools, use default confirmation
        if not yes:
            console.print("\n[yellow]Do you want to proceed with this action?[/yellow]")
            if not Confirm.ask("Confirm?"):
                return {"success": False, "error": "Tool execution cancelled by user"}
        
        result = tool_manager.execute_tool(tool_name, params)
        
        # Store tool use in session if successful
        if result and result.get("success"):
            result["tool"] = tool_name
            result["parameters"] = params
        
        return result
    except Exception as e:
        console.print(f"[red]Error executing tool: {str(e)}[/red]")
        return {
            "success": False,
            "error": str(e)
        }

@app.command()
def ask(
    task: str = typer.Argument(..., help="The task or question you want help with"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm all prompts")
):
    """Ask Kazuri for help with a development task."""
    try:
        # Get AWS configuration
        aws_config = get_aws_config()
        if not aws_config.get('region_name'):
            console.print("[red]Error: AWS region not set. Please set AWS_REGION or AWS_DEFAULT_REGION environment variable.[/red]")
            raise typer.Exit(1)
        
        # Initialize AWS Bedrock client
        bedrock = boto3.client(**aws_config)
        
        # Get environment details
        env_details = get_environment_details()
        
        # Format prompt with conversation history
        formatted_prompt = format_task_for_claude(task, env_details)
        
        # Call Claude through AWS Bedrock
        console.print("[green]Thinking...[/green]")
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.7
        }
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        completion = response_body['content'][0]['text']
        
        # Process any tool use before displaying response
        tool_use = process_tool_use(completion)
        tool_results = []
        if tool_use:
            result = execute_tool(tool_use, yes)
            if result:
                tool_results.append(result)
                if result.get("success"):
                    console.print("[green]Tool execution successful[/green]")
                    if "content" in result:
                        console.print(result["content"])
                    elif "files" in result:
                        console.print("\n".join(result["files"]))
                else:
                    console.print(f"[red]Tool execution failed: {result.get('error', 'Unknown error')}[/red]")
        
        # Store interaction in session
        session.add_interaction(task, completion, tool_results)
        
        # Display the response
        console.print(Panel(
            Markdown(completion),
            title="Kazuri's Response",
            border_style="green"
        ))
        
        # If verbose, show additional debug info
        if verbose:
            console.print("\n[dim]Debug Information:[/dim]")
            console.print(f"[dim]Current Directory: {os.getcwd()}[/dim]")
            console.print(f"[dim]Available Tools: {tool_manager.list_tools()}[/dim]")
            console.print(f"[dim]AWS Region: {aws_config['region_name']}[/dim]")
            console.print(f"[dim]Session File: {session.current_session}[/dim]")
            console.print("\n[dim]Recent Context:[/dim]")
            console.print(session.get_recent_context())
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def version():
    """Show the version of Kazuri."""
    console.print(f"Kazuri version: {VERSION}")

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()
