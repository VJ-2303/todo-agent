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

    if action == "run_command":
        cmd = args.get("command", "")
        flattened_cmd = " ".join(cmd.split())
        if len(flattened_cmd) > 65:
            flattened_cmd = flattened_cmd[:62] + "..."
        return f"[bold yellow]cmd:[/bold yellow] [dim]{flattened_cmd}[/dim]"

    if action == "list_files":
        directory = args.get("directory", ".")
        return f"[bold cyan]dir:[/bold cyan] {directory}"

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
