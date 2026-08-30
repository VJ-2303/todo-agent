from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


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

    def add_message(self, role: MessageRole, content: str, step_num: int | None = None):
        self.messages.append(ChatMessage(role=role, content=content, step_num=step_num))

    def get_llm_messages(self) -> list[dict[str, str]]:
        return [msg.to_dict() for msg in self.messages]

    def reset(self):
        self.messages.clear()
        self.current_step = 0
        self.is_finished = False
        self.final_result = None
