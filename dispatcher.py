import config
from models import AgentState, ToolResult
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


def execute_tool(
    action: str, args: dict | None = None, state: AgentState | None = None
) -> ToolResult:
    """
    Finds the requested tool in TOOL_MAP and executes it with the given arguments.
    Returns a typed ToolResult with accurate success detection.
    """
    tool_args = args if isinstance(args, dict) else {}

    if action == "manage_todos":
        if state is None:
            return ToolResult(
                success=False,
                output="Error: Agent state not available for manage_todos.",
                error="State unavailable",
            )
        return execute_manage_todos(state, tool_args)

    if action not in TOOL_MAP:
        available = list(TOOL_MAP.keys()) + ["manage_todoss"]
        err = f"Error: Tool '{action}' is not recognized. Available tools: {available}"
        return ToolResult(success=False, output=err, error=err)

    tool_func = TOOL_MAP[action]

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


def execute_manage_todos(state: AgentState, args: dict) -> ToolResult:
    """Executes task management actions and modifies AgentState."""
    action_type = str(args.get("action", "list")).strip().lower()

    if action_type == "init":
        todos_data = args.get("todos", [])
        if not isinstance(todos_data, list) or not todos_data:
            return ToolResult(
                success=False,
                output="Error: 'todos' list is required when action is 'init'.",
                error="Invalid arguments",
            )
        summary = state.set_todos(todos_data)
        return ToolResult(
            success=True,
            output=f"Initialized {len(state.todos)} subtasks:\n{summary}",
        )

    elif action_type == "update":
        todo_id = args.get("todo_id")
        status = args.get("status")

        if todo_id is None or status is None:
            return ToolResult(
                success=False,
                output="Error: 'todo_id' and 'status' are required when action is 'update'.",
                error="Missing arguments",
            )

        try:
            numeric_id = int(todo_id)
        except ValueError:
            return ToolResult(
                success=False,
                output=f"Error: 'todo_id' must be an integer, got '{todo_id}'.",
                error="Invalid ID type",
            )

        updated = state.update_todo(numeric_id, str(status))
        if not updated:
            return ToolResult(
                success=False,
                output=f"Error: Subtask #{numeric_id} does not exist.",
                error="Task not found",
            )

        return ToolResult(
            success=True,
            output=f"Updated subtask #{numeric_id} to '{status}'.\n\nCurrent Tasks:\n{state.get_todos_summary()}",
        )

    elif action_type == "add":
        title = str(args.get("title", "")).strip()
        if not title:
            return ToolResult(
                success=False,
                output="Error: 'title' is required when action is 'add'.",
                error="Missing title",
            )
        new_item = state.add_todo(title)
        return ToolResult(
            success=True,
            output=f"Added subtask #{new_item.id}: '{new_item.title}'.\n\nCurrent Tasks:\n{state.get_todos_summary()}",
        )

    elif action_type == "list":
        return ToolResult(
            success=True,
            output=f"Current Tasks:\n{state.get_todos_summary()}",
        )

    return ToolResult(
        success=False,
        output=f"Error: Unknown action '{action_type}'. Valid actions are: 'init', 'update', 'add', 'list'.",
        error="Invalid action",
    )
