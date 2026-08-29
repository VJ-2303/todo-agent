from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def show_banner():
    """Displays the startup header."""
    console.print(
        Panel(
            "[bold white]Tiny Terminal Coding Agent[/bold white]\n"
            "[dim]Autonomous ReAct assistant powered by local LLM[/dim]\n"
            "[dim]Commands: [bold cyan]/help[/bold cyan], [bold cyan]/reset[/bold cyan], [bold cyan]/exit[/bold cyan][/dim]",
            title="[bold green]Workspace Active[/bold green]",
            border_style="green",
            expand=False,
        )
    )


def summarize_args(action: str, args: dict) -> str:
    """Extracts high-signal information and flattens newlines."""
    if action in ("write_file", "read_file"):
        target = args.get("path", "unknown")
        return f"[bold cyan]target:[/bold cyan] {target}"

    if action == "replace_in_file":
        target = args.get("path", "unknown")
        return f"[bold cyan]target:[/bold cyan] {target} [dim](surgical edit)[/dim]"

    if action == "grep_search":
        query = args.get("query", "")
        path = args.get("path", ".")
        return f"[bold magenta]query:[/bold magenta] '{query}' [dim]in {path}[/dim]"

    if action == "find_files":
        pattern = args.get("pattern", "*")
        directory = args.get("directory", ".")
        return f"[bold cyan]pattern:[/bold cyan] {pattern} [dim]in {directory}[/dim]"

    if action == "run_command":
        cmd = args.get("command", "")
        flattened_cmd = " ".join(cmd.split())
        if len(flattened_cmd) > 65:
            flattened_cmd = flattened_cmd[:62] + "..."
        return f"[bold yellow]cmd:[/bold yellow] [dim]{flattened_cmd}[/dim]"

    if action == "list_files":
        directory = args.get("directory", ".")
        return f"[bold cyan]dir:[/bold cyan] {directory}"
    if action == "search_web":
        query = args.get("query", "")
        return f"[bold magenta]search:[/bold magenta] '{query}'"

    if action == "fetch_web_page":
        url = args.get("url", "")
        return f"[bold cyan]url:[/bold cyan] {url}"

    return f"[dim]{str(args)}[/dim]"


def show_thought(thought: str, step_num: int = None):
    """Renders reasoning with an optional compact step counter."""
    step_prefix = f"[bold dim][{step_num}][/bold dim] " if step_num else ""
    console.print(f"\n{step_prefix}[dim italic cyan]💭 {thought}[/dim italic cyan]")


def show_tool_call(action: str, args: dict):
    """Displays a single compact line for tool execution."""
    summary = summarize_args(action, args)
    console.print(f"   [bold blue]⚙ {action}[/bold blue] ➔ {summary}")


def show_tool_status(success: bool, error_msg: str = ""):
    """Displays status only when a failure occurs to reduce vertical noise."""
    if not success:
        console.print(f"   [bold red]✗ Failed:[/bold red] [dim]{error_msg}[/dim]")


def ask_user_questions(args: dict) -> str:
    questions = args.get("questions", [])

    if not questions:
        return "No questions provided."

    console.print()
    console.print(
        Panel(
            "[bold yellow]The agent needs clarification before proceeding:[/bold yellow]",
            title="[bold cyan]Clarification Requested[/bold cyan]",
            border_style="yellow",
        )
    )
    responses = []

    for index, q_item in enumerate(questions, start=1):
        q_text = q_item.get("question", "Clarification needed:")
        options = q_item.get("options", [])

        console.print(
            f"\n[bold white]Question {index}:[/bold white] [bold cyan]{q_text}[/bold cyan]"
        )
        if options:
            for opt_idx, opt in enumerate(options, start=1):
                console.print(f"  [bold green][{opt_idx}][/bold green] {opt}")

            while True:
                user_choice = console.input(
                    "[bold yellow]Enter choice number or custom answer: [/bold yellow]"
                ).strip()
                if not user_choice:
                    console.print("[dim red]Answer cannot be empty.[/dim red]")
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
                    "[bold yellow]Your answer: [/bold yellow]"
                ).strip()
                if user_choice:
                    final_answer = user_choice
                    break
                console.print("[dim red]Answer cannot be empty.[/dim red]")

        responses.append(f"{index}. {q_text} -> {final_answer}")


def show_final_answer(message: str):
    """Renders the final response in a clean bordered Markdown panel."""
    console.print()
    console.print(
        Panel(
            Markdown(message),
            title="[bold green]🤖 Agent Response[/bold green]",
            border_style="green",
        )
    )
    console.print()
