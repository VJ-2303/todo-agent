import os

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

import config
from models import TaskStatus, TodoItem

console = Console()

_output_sink = None
_input_provider = None
_todos_sink = None


def set_output_sink(sink_fn):
    """Sets a custom output callback (e.g. for Textual RichLog)."""
    global _output_sink
    _output_sink = sink_fn


def set_input_provider(provider_fn):
    """Sets a custom input provider callback (e.g. for Textual interactive questions)."""
    global _input_provider
    _input_provider = provider_fn


def set_todos_sink(sink_fn):
    """Sets a custom callback for rendering todos to a dedicated panel."""
    global _todos_sink
    _todos_sink = sink_fn


def print_out(renderable=""):
    """Routes rendering to output sink if registered, otherwise to console."""
    if _output_sink:
        _output_sink(renderable)
    else:
        console.print(renderable)


def show_banner():
    """Displays a clean, minimal developer startup header."""
    model_name = config.MODEL_NAME or "default-model"
    dir_name = os.path.basename(os.getcwd()) or "workspace"

    print_out(
        f"[bold #38bdf8]StarAgent[/bold #38bdf8] [dim #64748b]({escape(model_name)} @ {escape(dir_name)})[/dim #64748b]"
    )
    print_out(
        "[dim #475569]Type your instruction below or use /help for commands.[/dim #475569]"
    )
    print_out("[dim #1e293b]" + "─" * 60 + "[/dim #1e293b]")


def show_chat_response(message: str):
    """Renders direct conversational markdown from the agent."""
    print_out()
    print_out("[bold #38bdf8]StarAgent:[/bold #38bdf8]")
    print_out(Markdown(message))
    print_out()


def summarize_args(action: str, args: dict) -> tuple[str, str, str]:
    """Returns (tag, color_hex, summary)"""
    if action == "read_file":
        return "read", "#38bdf8", escape(str(args.get("path", "unknown")))

    if action == "write_file":
        return "write", "#34d399", escape(str(args.get("path", "unknown")))

    if action == "replace_in_file":
        return "edit", "#fbbf24", escape(str(args.get("path", "unknown")))

    if action == "run_command":
        cmd = str(args.get("command", ""))
        flattened_cmd = " ".join(cmd.split())
        if len(flattened_cmd) > 60:
            flattened_cmd = flattened_cmd[:57] + "..."
        return "run", "#a78bfa", escape(flattened_cmd)

    if action == "grep_search":
        query = escape(str(args.get("query", "")))
        path = escape(str(args.get("path", ".")))
        return "grep", "#22d3ee", f"'{query}' in {path}"

    if action == "find_files":
        pattern = escape(str(args.get("pattern", "*")))
        directory = escape(str(args.get("directory", ".")))
        return "find", "#38bdf8", f"'{pattern}' in {directory}"

    if action == "list_files":
        directory = escape(str(args.get("directory", ".")))
        return "list", "#818cf8", escape(directory)

    if action == "search_web":
        query = escape(str(args.get("query", "")))
        return "web", "#c084fc", f"'{query}'"

    if action == "fetch_web_page":
        url = escape(str(args.get("url", "")))
        return "fetch", "#2dd4bf", url

    if action == "manage_todos":
        act = str(args.get("action", "list"))
        if act == "update":
            tid = args.get("todo_id", "?")
            st = args.get("status", "?")
            return "todos", "#2dd4bf", f"update #{tid} -> {st}"
        elif act == "init":
            count = len(args.get("todos", []))
            return "todos", "#2dd4bf", f"init {count} subtasks"
        elif act == "add":
            title = escape(str(args.get("title", "")))
            return "todos", "#2dd4bf", f"add '{title}'"
        return "todos", "#2dd4bf", "list tasks"

    return action, "#94a3b8", escape(str(args))


def show_thought(thought: str, step_num: int | None = None):
    """Renders agent thought with clean step indicator."""
    step_prefix = f"[dim #64748b]step {step_num:02d}[/dim #64748b] " if step_num else ""
    print_out(f"\n{step_prefix}[dim #94a3b8] thinking: {escape(thought)}[/dim #94a3b8]")


def show_tool_call(action: str, args: dict):
    """Displays a clean tree-connected action line for tool execution."""
    tag, color, summary = summarize_args(action, args)
    print_out(
        f"  [dim #334155]└──[/dim #334155] [bold {color}]{tag}[/bold {color}] [#e2e8f0]{summary}[/#e2e8f0]"
    )


def show_tool_status(success: bool, error_msg: str = ""):
    """Displays concise execution status for tool calls."""
    if success:
        print_out("      [#34d399]→ ok[/#34d399]")
    else:
        print_out(
            f"      [#f87171]→ error:[/#f87171] [dim #fca5a5]{escape(error_msg)}[/dim #fca5a5]"
        )


def ask_user_questions(args: dict) -> str:
    """
    Renders structured interactive question prompts to the user and collects answers.
    """
    questions = args.get("questions", [])

    if not questions:
        return "No questions provided."

    print_out("\n[bold #fbbf24]Clarification Requested:[/bold #fbbf24]")
    responses = []

    for index, q_item in enumerate(questions, start=1):
        q_text = q_item.get("question", "Clarification needed:")
        options = q_item.get("options", [])

        print_out(
            f"\n[bold white]Question {index}:[/bold white] [#38bdf8]{escape(q_text)}[/#38bdf8]"
        )
        if options:
            for opt_idx, opt in enumerate(options, start=1):
                print_out(f"  [dim #64748b]{opt_idx}.[/dim #64748b] {opt}")

            while True:
                if _input_provider:
                    user_choice = _input_provider(
                        f"Question {index} (1-{len(options)} or custom): "
                    ).strip()
                else:
                    user_choice = console.input(
                        f"\n  [bold #fbbf24]> Select (1-{len(options)}) or type answer: [/bold #fbbf24]"
                    ).strip()
                if not user_choice:
                    print_out("  [dim #f87171]Answer cannot be empty.[/dim #f87171]")
                    continue
                if user_choice.isdigit():
                    selected_num = int(user_choice)
                    if 1 <= selected_num <= len(options):
                        final_answer = options[selected_num - 1]
                        break
                final_answer = user_choice
                break
        else:
            while True:
                if _input_provider:
                    user_choice = _input_provider(f"Question {index}: ").strip()
                else:
                    user_choice = console.input(
                        "\n  [bold #fbbf24]> Your answer: [/bold #fbbf24]"
                    ).strip()
                if user_choice:
                    final_answer = user_choice
                    break
                print_out("  [dim #f87171]Answer cannot be empty.[/dim #f87171]")

        responses.append(f"{index}. {q_text} -> {final_answer}")
        print_out(f"  [dim #34d399]→ recorded: {final_answer}[/dim #34d399]")

    print_out()
    return "USER RESPONSES:\n" + "\n".join(responses)


def show_todos_board(todos: list[TodoItem]):
    """Renders a sleek, minimal subtask checklist in the dedicated panel or log."""
    if _todos_sink:
        _todos_sink(todos)
        return

    if not todos:
        return

    print_out("\n[bold #2dd4bf]Task Plan:[/bold #2dd4bf]")
    for item in todos:
        if item.status == TaskStatus.COMPLETED:
            print_out(
                f"  [#34d399][✓][/#34d399] #{item.id}: [dim strike #64748b]{escape(item.title)}[/dim strike #64748b]"
            )
        else:
            print_out(
                f"  [dim #475569][ ][/dim #475569] #{item.id}: [#e2e8f0]{escape(item.title)}[/#e2e8f0]"
            )
    print_out()


def show_final_answer(message: str):
    """Renders the final agent response in clean markdown."""
    print_out()
    print_out("[bold #34d399]StarAgent (completed):[/bold #34d399]")
    print_out(Markdown(message))
    print_out()
