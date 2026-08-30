import config
from models import ToolResult
from tools import (
    fetch_web_page,
    find_files,
    grep_search,
    list_files,
    read_file,
    replace_in_file,
    run_command,
    search_web,
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
    "search_web": search_web,
    "fetch_web_page": fetch_web_page,
}


def truncate_observation(
    text: str, max_chars: int = config.MAX_OBSERVATION_LIMIT
) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    omitted_count = len(text) - max_chars
    notice = f"\n\n[Warning: Output truncated. {omitted_count} characters omitted to preserve context window]"
    return text[:max_chars] + notice, True


def execute_tool(action: str, args: dict) -> ToolResult:
    """
    Finds the requested tool in TOOL_MAP and executes it with the given arguments.
    Returns the string result (observation) or an informative error message.
    """

    if action not in TOOL_MAP:
        available = list(TOOL_MAP.keys())
        err = f"Error: Tool {action} is not recognized. Available tools: {available}"
        return ToolResult(success=False, output=err, error=err)

    tool_func = TOOL_MAP[action]

    try:
        raw_text = str(tool_func(**args))
        truncated_text, is_truncated = truncate_observation(raw_text)
        is_success = not truncated_text.startswith("Error:")

        return ToolResult(
            success=is_success,
            output=truncated_text,
            error=truncated_text if not is_success else None,
            truncated=is_truncated,
        )
    except TypeError as e:
        err = f"Error executing '{action}': Incorrect arguments provided ({e})."
        return ToolResult(success=False, output=err, error=err)
    except Exception as e:
        err = f"Error executing '{action}': {e!s}"
        return ToolResult(success=False, output=err, error=err)
