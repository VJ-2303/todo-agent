import json

TOOLS = [
    {
        "name": "list_files",
        "description": "List files and directories in a given directory path.",
        "parameters": {"directory": "string (optional, default to '.')"},
    },
    {
        "name": "find_files",
        "description": "Recursively search for files matching a glob pattern (e.g. '*.py', '*config*') up to max_depth.",
        "parameters": {
            "pattern": "string (optional, glob pattern, default '*')",
            "directory": "string (optional, root directory, default '.')",
            "max_depth": "integer (optional, max subdirectory depth, default 5)",
        },
    },
    {
        "name": "grep_search",
        "description": "Search for exact text or regex patterns across files in a directory with line numbers.",
        "parameters": {
            "query": "string (required, the search query or regex)",
            "path": "string (optional, directory or file path, default '.')",
            "is_regex": "boolean (optional, whether query is regex, default false)",
            "file_pattern": "string (optional, glob filter like '*.py', default '*')",
        },
    },
    {
        "name": "replace_in_file",
        "description": "Surgically replace an exact code block with new text in a file. Must match exactly once.",
        "parameters": {
            "path": "string (required, target file path)",
            "target": "string (required, exact existing text to replace)",
            "replacement": "string (required, new replacement text)",
        },
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
