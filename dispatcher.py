import config
from tools import (
    find_files,
    grep_search,
    list_files,
    read_file,
    replace_in_file,
    run_command,
    write_file,
)

TOOL_MAP = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "run_command": run_command,
    "replace_in_file": replace_in_file,
    "grep_search": grep_search,
    "find_files": find_files,
}


def truncate_observation(
    text: str, max_chars: int = config.MAX_OBSERVATION_LIMIT
) -> str:
    if len(text) <= max_chars:
        return text
    omitted_count = len(text) - max_chars
    notice = f"\n\n[Warning: Output truncated. {omitted_count} characters omitted to preserve context window]"
    return text[:max_chars] + notice


def execute_tool(action: str, args: dict) -> str:
    """
    Finds the requested tool in TOOL_MAP and executes it with the given arguments.
    Returns the string result (observation) or an informative error message.
    """

    if action not in TOOL_MAP:
        return f"Error: Tool '{action}' is not recognized. Available tools: {list(TOOL_MAP.keys())}"

    tool_func = TOOL_MAP[action]

    try:
        result = tool_func(**args)
        return truncate_observation(str(result))
    except TypeError as e:
        return f"Error executing '{action}': Incorrect arguments provided ({e})."
    except Exception as e:
        return f"Error executing '{action}': {str(e)}"
