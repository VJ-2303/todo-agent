import os

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

import config

console = Console()


def show_banner():
    """Displays a sleek modern startup header with runtime metadata."""
    model_name = config.MODEL_NAME or "default-model"
    dir_name = os.path.basename(os.getcwd()) or "workspace"

    banner_grid = Table.grid(expand=True, padding=(0, 1))
    banner_grid.add_column(justify="left", ratio=3)
    banner_grid.add_column(justify="right", ratio=2)

    banner_grid.add_row(
        "[bold bright_white]⚡ Tiny Terminal Coding Agent[/bold bright_white]",
        f"[dim]model:[/dim] [bold bright_cyan]{escape(model_name)}[/bold bright_cyan]  [dim]dir:[/dim] [bold bright_yellow]{escape(dir_name)}[/bold bright_yellow]",
    )
    banner_grid.add_row(
        "[dim]Autonomous ReAct Engineering Assistant[/dim]",
        "[dim]Commands: [bold cyan]/help[/bold cyan] · [bold cyan]/tools[/bold cyan] · [bold cyan]/reset[/bold cyan] · [bold cyan]/exit[/bold cyan][/dim]",
    )

    console.print()
    console.print(
        Panel(
            banner_grid,
            box=box.ROUNDED,
            border_style="bright_blue",
            padding=(0, 1),
        )
    )
    console.print()


def summarize_args(action: str, args: dict) -> tuple[str, str]:
    """
    Extracts high-signal arguments and returns a styled badge tag + formatted details.
    """
    if action == "read_file":
        target = escape(str(args.get("path", "unknown")))
        return (
            "[bold black on bright_cyan] READ [/bold black on bright_cyan]",
            f"[bright_white]{target}[/bright_white]",
        )

    if action == "write_file":
        target = escape(str(args.get("path", "unknown")))
        return (
            "[bold black on bright_green] WRITE [/bold black on bright_green]",
            f"[bright_white]{target}[/bright_white]",
        )

    if action == "replace_in_file":
        target = escape(str(args.get("path", "unknown")))
        return (
            "[bold black on bright_yellow] EDIT [/bold black on bright_yellow]",
            f"[bright_white]{target}[/bright_white] [dim](surgical edit)[/dim]",
        )

    if action == "run_command":
        cmd = str(args.get("command", ""))
        flattened_cmd = " ".join(cmd.split())
        if len(flattened_cmd) > 70:
            flattened_cmd = flattened_cmd[:67] + "..."
        return (
            "[bold black on yellow] RUN [/bold black on yellow]",
            f"[yellow]{escape(flattened_cmd)}[/yellow]",
        )

    if action == "grep_search":
        query = escape(str(args.get("query", "")))
        path = escape(str(args.get("path", ".")))
        return (
            "[bold black on bright_magenta] GREP [/bold black on bright_magenta]",
            f"query [bright_magenta]'{query}'[/bright_magenta] in [dim]{path}[/dim]",
        )

    if action == "find_files":
        pattern = escape(str(args.get("pattern", "*")))
        directory = escape(str(args.get("directory", ".")))
        return (
            "[bold black on cyan] FIND [/bold black on cyan]",
            f"pattern [bright_cyan]'{pattern}'[/bright_cyan] in [dim]{directory}[/dim]",
        )

    if action == "list_files":
        directory = escape(str(args.get("directory", ".")))
        return (
            "[bold black on blue] LIST [/bold black on blue]",
            f"dir [bright_white]{directory}[/bright_white]",
        )

    if action == "search_web":
        query = escape(str(args.get("query", "")))
        return (
            "[bold black on bright_magenta] WEB [/bold black on bright_magenta]",
            f"search [bright_magenta]'{query}'[/bright_magenta]",
        )

    if action == "fetch_web_page":
        url = escape(str(args.get("url", "")))
        return (
            "[bold black on bright_cyan] FETCH [/bold black on bright_cyan]",
            f"[bright_cyan]{url}[/bright_cyan]",
        )

    return (
        f"[bold black on white] {escape(action.upper())} [/bold black on white]",
        f"[dim]{escape(str(args))}[/dim]",
    )


def show_thought(thought: str, step_num: int | None = None):
    """Renders agent thought with a high-contrast step badge."""
    if step_num:
        step_badge = f"[bold black on bright_cyan] STEP {step_num:02d} [/bold black on bright_cyan] "
    else:
        step_badge = ""

    console.print(f"\n{step_badge}[bright_cyan]💭 {escape(thought)}[/bright_cyan]")


def show_tool_call(action: str, args: dict):
    """Displays a clean tree-connected action line for tool execution."""
    badge, summary = summarize_args(action, args)
    console.print(f"  [dim]└──[/dim] {badge} {summary}")


def show_tool_status(success: bool, error_msg: str = ""):
    """Displays concise execution status for tool calls."""
    if success:
        console.print("     [dim green]✓ Done[/dim green]")
    else:
        console.print(
            f"     [bold red]✗ Failed:[/bold red] [dim red]{escape(error_msg)}[/dim red]"
        )


def ask_user_questions(args: dict) -> str:
    """
    Renders structured interactive question cards to the user and collects answers.
    """
    questions = args.get("questions", [])

    if not questions:
        return "No questions provided."

    console.print()
    console.print(
        Panel(
            "[bold bright_white]The agent needs your input before proceeding:[/bold bright_white]",
            title="[bold bright_yellow]❓ Clarification Requested[/bold bright_yellow]",
            border_style="bright_yellow",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )
    responses = []

    for index, q_item in enumerate(questions, start=1):
        q_text = q_item.get("question", "Clarification needed:")
        options = q_item.get("options", [])

        console.print(
            f"\n[bold bright_white]Question {index}:[/bold bright_white] [bold bright_cyan]{q_text}[/bold bright_cyan]"
        )
        if options:
            for opt_idx, opt in enumerate(options, start=1):
                console.print(
                    f"  [bold black on bright_green] {opt_idx} [/bold black on bright_green] {opt}"
                )

            while True:
                user_choice = console.input(
                    "\n  [bold bright_yellow]❯ Select option or type custom answer: [/bold bright_yellow]"
                ).strip()
                if not user_choice:
                    console.print("  [dim red]Answer cannot be empty.[/dim red]")
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
                user_choice = console.input(
                    "\n  [bold bright_yellow]❯ Your answer: [/bold bright_yellow]"
                ).strip()
                if user_choice:
                    final_answer = user_choice
                    break
                console.print("  [dim red]Answer cannot be empty.[/dim red]")

        responses.append(f"{index}. {q_text} -> {final_answer}")
        console.print(f"  [dim green]✓ Recorded: {final_answer}[/dim green]")

    console.print()
    return "USER RESPONSES:\n" + "\n".join(responses)


def show_final_answer(message: str):
    """Renders the final agent response in a polished rounded Markdown canvas."""
    console.print()
    console.print(
        Panel(
            Markdown(message),
            title="[bold bright_green]✨ Task Complete[/bold bright_green]",
            border_style="bright_green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()
