from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

    @classmethod
    def from_str(cls, value: str) -> "TaskStatus":
        if not value:
            return cls.PENDING
        normalized = value.strip().lower()

        if normalized == "completed":
            return cls.COMPLETED
        return cls.PENDING


@dataclass
class TodoItem:
    id: int
    title: str
    status: TaskStatus = TaskStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "status": self.status}


@dataclass
class ChatMessage:
    role: MessageRole
    content: str
    step_num: int | None = None

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class AgentDecision:
    thought: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)
    raw_json: str = ""

    @property
    def is_final_answer(self) -> bool:
        """Helper property: True if the model is declaring the task completed."""
        return self.action == "final_answer"

    @property
    def is_clarification(self) -> bool:
        """Helper property: True if the model is asking the user a question."""
        return self.action == "ask_user"


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None
    truncated: bool = False

    def to_observation_text(self, action_name: str) -> str:
        """
        Generates clean, standardized observation text for message history.
        """
        if not self.success:
            return (
                f"OBSERVATION from {action_name} [FAILED]:\n{self.error or self.output}"
            )
        return f"OBSERVATION from {action_name}:\n{self.output}"


@dataclass
class AgentState:
    task: str
    max_steps: int = 30
    current_step: int = 0
    is_finished: bool = False
    final_result: str | None = None
    messages: list[ChatMessage] = field(default_factory=list)
    todos: list[TodoItem] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str, step_num: int | None = None):
        self.messages.append(ChatMessage(role=role, content=content, step_num=step_num))

    def get_llm_messages(self) -> list[dict[str, str]]:
        return [msg.to_dict() for msg in self.messages]

    def set_todos(self, items: list[dict[str, Any]]) -> str:
        """Initializes or replaces the active subtask list."""
        self.todos = [
            TodoItem(
                id=item.get("id", idx + 1),
                title=str(item.get("title", f"Task {idx + 1}")).strip(),
                status=TaskStatus.from_str(str(item.get("status", "pending"))),
            )
            for idx, item in enumerate(items)
        ]
        return self.get_todos_summary()

    def update_todo(self, todo_id: int, status: str) -> bool:
        """Updates status for a specific todo item."""
        for item in self.todos:
            if item.id == todo_id:
                item.status = TaskStatus.from_str(status)
                return True
        return False

    def add_todo(self, title: str) -> TodoItem:
        """Dynamically appends a new subtask."""
        new_id = (max([t.id for t in self.todos], default=0)) + 1
        new_item = TodoItem(
            id=new_id,
            title=title.strip(),
            status=TaskStatus.PENDING,
        )
        self.todos.append(new_item)
        return new_item

    def get_todos_summary(self) -> str:
        """Returns a concise checklist summary of active todos."""
        if not self.todos:
            return "No active tasks in plan."
        lines = []
        for item in self.todos:
            sym = "[✓]" if item.status == TaskStatus.COMPLETED else "[ ]"
            lines.append(f"{sym} #{item.id}: {item.title} ({item.status.value})")
        return "\n".join(lines)

    def reset(self):
        self.messages.clear()
        self.todos.clear()
        self.current_step = 0
        self.is_finished = False
        self.final_result = None
