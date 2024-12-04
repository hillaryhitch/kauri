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

def format_task_for_claude(task: str, environment_details: Optional[str] = None) -> str:
    system_prompt = """You are Kazuri, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices. 

When creating or modifying code:
1. First write the code and save it to a file
2. Then test the code thoroughly:
   - For web components, use browser_action to test in browser
   - For functions, write and run test cases
   - For CLI tools, test with sample commands
3. Always show the test results and ask for confirmation before proceeding

For web development tasks:
1. Save the code to appropriate files
2. Launch browser to test the implementation
3. Perform necessary interactions (clicks, typing, etc.)
4. Verify the functionality works as expected
5. Close browser when done

Available tools:
- execute_command: Execute system commands
- read_file: Read file contents
- write_file: Write content to a file
- search_files: Search for patterns in files
- list_files: List files in a directory
- list_code_definitions: List code definitions in files
- browser_action: Control a browser for testing web applications

When you need to use a tool, format your response like this:
<tool_name>tool_name</tool_name>
<parameter_name>parameter_value</parameter_name>

Always wait for user confirmation before executing any action."""
    
    prompt = f"{system_prompt}\n\nHuman: {task}"
    
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
    
    return "\n".join(details)

def process_tool_use(response: str):
    """Process any tool use requests in the response."""
    if "<tool_name>" not in response:
        return None
    
    # Extract tool name and parameters
    tool_start = response.find("<tool_name>")
    tool_end = response.find("</tool_name>")
    if tool_start == -1 or tool_end == -1:
        return None
    
    tool_name = response[tool_start + 11:tool_end].strip()
    
    # Extract parameters
    params = {}
    param_start = response.find("<", tool_end)
    while param_start != -1:
        param_end = response.find(">", param_start)
        if param_end == -1:
            break
        
        param_name = response[param_start + 1:param_end]
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

def execute_tool(tool_use, yes: bool = False) -> Dict[str, Any]:
    """Execute the specified tool with given parameters."""
    if not tool_use:
        return {"success": False, "error": "No tool use specified"}
    
    tool = tool_use["tool"]
    params = tool_use["parameters"]
    
    # Show tool details and get confirmation
    console.print("\n[yellow]Tool Request:[/yellow]")
    console.print(f"Tool: {tool}")
    console.print("Parameters:")
    for key, value in params.items():
        console.print(f"  {key}: {value}")
    
    # Always ask for confirmation unless in auto-confirm mode
    if not yes:
        console.print("\n[yellow]Do you want to proceed with this action?[/yellow]")
        if not Confirm.ask("Confirm?"):
            return {"success": False, "error": "Tool execution cancelled by user"}
    
    result = None
    
    if tool == "write_file":
        # Additional confirmation for file writes
        if not yes:
            console.print(f"\n[yellow]About to write to file:[/yellow] {params['path']}")
            console.print("\nContent preview:")
            console.print(params['content'][:200] + "..." if len(params['content']) > 200 else params['content'])
            if not Confirm.ask("\nProceed with file write?"):
                return {"success": False, "error": "File write cancelled by user"}
        result = tool_manager.write_file(params["path"], params["content"])
        
        # After writing code files, ask if user wants to test
        if result["success"] and any(params["path"].endswith(ext) for ext in ['.html', '.js', '.jsx', '.ts', '.tsx']):
            if yes or Confirm.ask("\nWould you like to test this in the browser?"):
                # Launch browser for testing
                file_path = os.path.abspath(params["path"])
                browser_result = execute_tool({
                    "tool": "browser_action",
                    "parameters": {
                        "action": "launch",
                        "url": f"file://{file_path}"
                    }
                }, yes)
                result["browser_test"] = browser_result
    
    elif tool == "execute_command":
        # Additional confirmation for command execution
        if not yes:
            console.print(f"\n[yellow]About to execute command:[/yellow] {params['command']}")
            if not Confirm.ask("\nProceed with command execution?"):
                return {"success": False, "error": "Command execution cancelled by user"}
        result = tool_manager.execute_command(params["command"])
    
    elif tool == "browser_action":
        action = params.get("action")
        if action == "launch":
            if not yes:
                console.print(f"\n[yellow]About to launch browser with URL:[/yellow] {params.get('url')}")
                if not Confirm.ask("\nProceed with browser launch?"):
                    return {"success": False, "error": "Browser launch cancelled by user"}
            result = {"success": True, "action": "launch", "url": params.get("url")}
        
        elif action in ["click", "type", "scroll_down", "scroll_up"]:
            if not yes:
                console.print(f"\n[yellow]About to perform browser action:[/yellow] {action}")
                if "coordinate" in params:
                    console.print(f"At coordinates: {params['coordinate']}")
                if "text" in params:
                    console.print(f"With text: {params['text']}")
                if not Confirm.ask("\nProceed with browser action?"):
                    return {"success": False, "error": "Browser action cancelled by user"}
            result = {
                "success": True,
                "action": action,
                "coordinate": params.get("coordinate"),
                "text": params.get("text")
            }
        
        elif action == "close":
            if not yes:
                console.print("\n[yellow]About to close browser[/yellow]")
                if not Confirm.ask("\nProceed with browser close?"):
                    return {"success": False, "error": "Browser close cancelled by user"}
            result = {"success": True, "action": "close"}
        
        else:
            result = {"success": False, "error": f"Unknown browser action: {action}"}
    
    else:
        # For other tools, use default confirmation
        if not yes:
            console.print(f"\n[yellow]About to execute {tool}[/yellow]")
            if not Confirm.ask("\nProceed?"):
                return {"success": False, "error": f"{tool} cancelled by user"}
        result = tool_manager.execute_tool(tool, params)
    
    # Store tool use in session if successful
    if result and result.get("success"):
        result["tool"] = tool
        result["parameters"] = params
    
    return result

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
        
        # Format prompt
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
                    
                    # If browser test was performed, show results
                    if "browser_test" in result:
                        console.print("\n[green]Browser test completed[/green]")
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
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def version():
    """Show the version of Kazuri."""
    console.print("Kazuri version: 0.1.0")

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()
