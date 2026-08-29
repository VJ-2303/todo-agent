import sys

from rich.panel import Panel
from rich.table import Table

from agent import TinyAgent
from schemas import TOOLS
from ui import console, show_banner


def print_help():
    """Renders available slash commands"""
    cmd_table = Table(
        title="Slash Commands", show_header=True, header_style="bold cyan"
    )
    cmd_table.add_column("Command", style="bold yellow")
    cmd_table.add_column("Description")
    cmd_table.add_row("/help", "Display available commands and registered tools")
    cmd_table.add_row("/tools", "Display registered tools")
    cmd_table.add_row("/reset, /clear", "Reset conversational memory back to default")
    cmd_table.add_row("/exit, /quit", "Exit the agent terminal")
    console.print(cmd_table)
    console.print()


def print_tools():
    tool_table = Table(
        title="Available Agent Tools", show_header=True, header_style="bold blue"
    )
    tool_table.add_column("Tool Name", style="bold green")
    tool_table.add_column("Purpose")
    for tool in TOOLS:
        tool_table.add_row(tool["name"], tool["description"])
    console.print(tool_table)
    console.print()


def main():
    show_banner()
    agent = TinyAgent()

    while True:
        try:
            user_input = console.input("[bold green]❯ [/bold green]").strip()

            if not user_input:
                continue

            command = user_input.lower()
            if command in ("/exit", "/quit"):
                console.print("\n[dim]Shutting down Tiny Agent. Goodbye![/dim]")
                break

            elif command in ("/reset", "/clear"):
                agent.reset()
                continue

            elif command == "/help":
                print_help()
                continue
            elif command == "/tools":
                print_tools()
                continue

            elif command.startswith("/"):
                console.print(
                    f"[bold red]Unknown command:[/bold red] {user_input}. Type [bold cyan]/help[/bold cyan] for options."
                )
                continue

            agent.run(user_input)
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[dim]Interrupted by user. Exiting...[/dim]")
            sys.exit(0)


if __name__ == "__main__":
    main()
