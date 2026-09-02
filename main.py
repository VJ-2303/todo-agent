import os
import queue
import threading
import traceback

os.environ["LITELLM_LOG"] = "ERROR"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

from rich.markup import escape
from rich.table import Table
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.suggester import SuggestFromList
from textual.widgets import Input, Label, RichLog, Static

import config
import ui
from agent import StarAgent
from models import TaskStatus, TodoItem
from schemas import TOOLS
from ui import show_banner, show_todos_board

SLASH_COMMANDS = [
    "/help",
    "/tools",
    "/todos",
    "/tasks",
    "/reset",
    "/clear",
    "/exit",
    "/quit",
]


def get_help_table() -> Table:
    cmd_table = Table(
        title="Slash Commands", show_header=True, header_style="bold cyan"
    )
    cmd_table.add_column("Command", style="bold yellow")
    cmd_table.add_column("Description")
    cmd_table.add_row("/help", "Display available commands and registered tools")
    cmd_table.add_row("/tools", "Display registered tools")
    cmd_table.add_row("/todos, /tasks", "Display the active task progress board")
    cmd_table.add_row("/reset, /clear", "Reset conversational memory back to default")
    cmd_table.add_row("/exit, /quit", "Exit StarAgent")
    return cmd_table


def get_tools_table() -> Table:
    tool_table = Table(
        title="Available Agent Tools", show_header=True, header_style="bold blue"
    )
    tool_table.add_column("Tool Name", style="bold green")
    tool_table.add_column("Purpose")
    for tool in TOOLS:
        tool_table.add_row(str(tool["name"]), str(tool["description"]))
    return tool_table


class StarAgentApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #000000;
    }

    #main_container {
        height: 1fr;
        width: 100%;
        background: #000000;
    }

    #log {
        width: 70%;
        height: 100%;
        background: #000000;
        border: none;
        padding: 1 2;
        scrollbar-size: 1 1;
        scrollbar-color: #222222;
        scrollbar-background: #000000;
        scrollbar-color-hover: #333333;
        scrollbar-background-hover: #000000;
        scrollbar-color-active: #444444;
        scrollbar-background-active: #000000;
    }

    #sidebar {
        width: 30%;
        height: 100%;
        background: #000000;
        border-left: solid #1e293b;
        padding: 1 2;
    }

    #sidebar_header {
        color: #2dd4bf;
        text-style: bold;
        padding-bottom: 1;
    }

    #todos_view {
        color: #e2e8f0;
    }

    #prompt_input {
        width: 100%;
        height: 3;
        border: tall #222222;
        background: #000000;
        color: #e2e8f0;
        padding: 0 1;
    }

    #prompt_input .input--suggestion {
        color: #475569;
    }

    #prompt_input:hover {
        border: tall #222222;
        background: #000000;
    }

    #prompt_input:focus {
        border: tall #333333;
        background: #000000;
    }

    #footer_bar {
        height: 1;
        width: 100%;
        background: #000000;
        color: #64748b;
        padding: 0 2;
    }
    """

    def __init__(self):
        super().__init__()
        self.agent = StarAgent()
        self.clarification_queue = queue.Queue()
        self.is_waiting_clarification = False
        self.is_busy = False

    def get_footer_text(self, status: str = "ready") -> str:
        model = config.MODEL_NAME or "default"
        cwd = os.path.basename(os.getcwd()) or "workspace"
        return f"[dim #64748b]StarAgent — model: [/dim #64748b][#38bdf8]{model}[/#38bdf8] [dim #64748b]| dir: [/dim #64748b][#94a3b8]{cwd}[/#94a3b8] [dim #64748b]| [/dim #64748b]{status}"

    def compose(self) -> ComposeResult:
        with Horizontal(id="main_container"):
            yield RichLog(id="log", auto_scroll=True, markup=True, wrap=True)
            with Vertical(id="sidebar"):
                yield Static("[bold #2dd4bf]TASK PLAN[/bold #2dd4bf]", id="sidebar_header")
                yield Static("[dim #475569]No active tasks[/dim #475569]", id="todos_view")
        yield Input(
            placeholder="Type your instruction or /help, /todos, /exit...",
            suggester=SuggestFromList(SLASH_COMMANDS, case_sensitive=False),
            id="prompt_input",
        )
        yield Label(self.get_footer_text("[dim #475569]ready[/dim #475569]"), id="footer_bar")

    def update_todos_view(self, todos: list[TodoItem]) -> None:
        """Updates the right-hand Task Plan panel in place."""
        if not todos:
            content = "[dim #475569]No active tasks[/dim #475569]"
        else:
            lines = []
            completed = sum(1 for t in todos if t.status == TaskStatus.COMPLETED)
            total = len(todos)
            for item in todos:
                if item.status == TaskStatus.COMPLETED:
                    lines.append(f"[#34d399][✓][/#34d399] #{item.id}: [dim strike #64748b]{escape(item.title)}[/dim strike #64748b]")
                else:
                    lines.append(f"[dim #475569][ ][/dim #475569] #{item.id}: [#e2e8f0]{escape(item.title)}[/#e2e8f0]")
            lines.append(f"\n[dim #64748b]Progress: {completed}/{total}[/dim #64748b]")
            content = "\n".join(lines)

        try:
            widget = self.query_one("#todos_view", Static)
            if threading.current_thread() is threading.main_thread():
                widget.update(content)
            else:
                self.call_from_thread(widget.update, content)
        except Exception:
            pass

    def write_to_log(self, renderable="") -> None:
        """Thread-safe logging helper for RichLog."""
        if renderable is None:
            return
        try:
            log = self.query_one(RichLog)
            if threading.current_thread() is threading.main_thread():
                log.write(renderable)
            else:
                self.call_from_thread(log.write, renderable)
        except Exception:
            pass

    def update_status(self, text: str) -> None:
        try:
            footer = self.query_one("#footer_bar", Label)
            content = self.get_footer_text(text)
            if threading.current_thread() is threading.main_thread():
                footer.update(content)
            else:
                self.call_from_thread(footer.update, content)
        except Exception:
            pass

    def on_mount(self) -> None:
        ui.set_output_sink(self.write_to_log)
        ui.set_input_provider(self._request_user_clarification)
        ui.set_todos_sink(self.update_todos_view)
        show_banner()

    def _request_user_clarification(self, prompt_text: str = "") -> str:
        prompt_input = self.query_one(Input)
        self.is_waiting_clarification = True
        self.call_from_thread(
            setattr, prompt_input, "placeholder", f"[?] {prompt_text}"
        )
        self.update_status("[yellow]waiting for user clarification...[/yellow]")
        answer = self.clarification_queue.get()
        self.is_waiting_clarification = False
        self.call_from_thread(
            setattr,
            prompt_input,
            "placeholder",
            "Type your instruction or /help, /todos, /exit...",
        )
        self.update_status("[cyan]running...[/cyan]")
        return answer

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        event.input.value = ""

        if not user_text:
            return

        log = self.query_one(RichLog)

        # If agent is waiting on clarification question:
        if self.is_waiting_clarification:
            log.write(f"[dim yellow]> {user_text}[/dim yellow]")
            self.clarification_queue.put(user_text)
            return

        if self.is_busy:
            log.write("[dim yellow][!] Agent is busy processing previous task. Please wait.[/dim yellow]")
            return

        # Print user message to scrollable log
        log.write(f"\n[bold green]> {user_text}[/bold green]")

        command = user_text.lower()
        if command in ("/exit", "/quit"):
            self.exit()
            return
        elif command == "/clear":
            log.clear()
            show_banner()
            return
        elif command == "/reset":
            self.agent.reset()
            self.update_todos_view([])
            log.clear()
            show_banner()
            log.write("[green][+] Conversation memory and logs have been reset.[/green]\n")
            return
        elif command == "/help":
            log.write(get_help_table())
            return
        elif command == "/tools":
            log.write(get_tools_table())
            return
        elif command in ("/todos", "/tasks"):
            if self.agent.state.todos:
                show_todos_board(self.agent.state.todos)
            else:
                log.write("[dim]No active tasks in memory.[/dim]\n")
            return
        elif command.startswith("/"):
            log.write(
                f"[bold red]Unknown command:[/bold red] {user_text}. Type [bold cyan]/help[/bold cyan] for options.\n"
            )
            return

        # Run agent in background thread so UI stays responsive and scrollable
        self.is_busy = True
        self.update_status("[yellow]thinking (generating)...[/yellow]")
        self.run_agent_task(user_text)

    @work(thread=True)
    def run_agent_task(self, task: str) -> None:
        try:
            self.agent.run(task)
        except Exception as e:
            self.write_to_log(f"\n[bold red]Execution Error:[/bold red] {e}\n[dim]{traceback.format_exc()}[/dim]")
        finally:
            self.is_busy = False
            self.update_status("[dim]ready[/dim]")


def main():
    app = StarAgentApp()
    app.run()


if __name__ == "__main__":
    main()
