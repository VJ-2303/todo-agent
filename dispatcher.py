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


def execute_tool(action: str, args: dict | None = None) -> ToolResult:
    """
    Finds the requested tool in TOOL_MAP and executes it with the given arguments.
    Returns a typed ToolResult with accurate success detection.
    """
    if action not in TOOL_MAP:
        available = list(TOOL_MAP.keys())
        err = f"Error: Tool '{action}' is not recognized. Available tools: {available}"
        return ToolResult(success=False, output=err, error=err)

    tool_func = TOOL_MAP[action]
    tool_args = args if isinstance(args, dict) else {}

    try:
        raw_text = str(tool_func(**tool_args))
        truncated_text, is_truncated = truncate_observation(raw_text)

        # Accurate success evaluation:
        # 1. Any error returned by tool functions starting with "Error:"
        # 2. For shell commands, verify zero exit code ("Exit Code: 0")
        if action == "run_command":
            is_success = truncated_text.startswith("Exit Code: 0")
        else:
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
