import json

TOOLS = [
    {
        "name": "list_files",
        "description": "List files and directories in a given directory path.",
        "parameters": {"directory": "string (optional, default to '.')"},
    },
    {
        "name": "read_file",
        "description": "Read the text content of a file at the given path.",
        "parameters": {"path": "string (required, the path to the file)"},
    },
    {
        "name": "write_file",
        "description": "Write or overwrite text content to a file at the given path.",
        "parameters": {
            "path": "string (required, the target file path)",
            "content": "string (required, the raw text content to write)",
        },
    },
    {
        "name": "run_command",
        "description": "Execute a shell command on Linux and returns stdout/stderr output.",
        "parameters": {"command": "string (required, the bash command to run)"},
    },
]


def get_tools_description() -> str:
    """Serializes the custom tool list into a formatted string for the prompt"""
    return json.dumps(TOOLS, indent=2)
