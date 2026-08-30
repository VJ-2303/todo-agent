import json

import config
from dispatcher import execute_tool
from llm import LLMClient
from parser import parse_agent_response
from prompts import build_system_prompt
from ui import (
    ask_user_questions,
    console,
    show_final_answer,
    show_thought,
    show_tool_call,
    show_tool_status,
)


class TinyAgent:
    def __init__(self):
        self.max_steps = config.MAX_STEPS
        self.llm = LLMClient()
        self.messages = []
        self.reset()

    def reset(self):
        self.messages = []

    def step(self) -> tuple[bool, str]:
        try:
            with console.status("[dim]Thinking...[/dim]", spinner="dots"):
                llm_response = self.llm.generate(self.messages)
        except Exception as e:
            console.print(f"\n[bold red]✗ Connection Error:[/bold red] {e!s}")
            return True, str(e)
        success, decision, error_msg = parse_agent_response(llm_response.content)

        if not success:
            self.messages.append({"role": "assistant", "content": llm_response.content})
            self.messages.append(
                {
                    "role": "user",
                    "content": f"OBSERVATION: Invalid output format. Error: {error_msg}",
                }
            )
            return False, error_msg

        thought = (
            decision.get("thought") or llm_response.thinking or "Execution next step"
        )
        action = decision.get("action", "")
        args = decision.get("args", {})

        show_thought(thought)

        if action == "final_answer":
            final_msg = args.get("message", "Task completed.")
            self.messages.append({"role": "assistant", "content": json.dumps(decision)})
            return True, final_msg

        if action == "ask_user":
            user_answers = ask_user_questions(args)
            self.messages.append({"role": "assistant", "content": json.dumps(decision)})
            self.messages.append(
                {
                    "role": "user",
                    "content": f"CLARIFICATION OBSERVATION:\n{user_answers}",
                }
            )
            return False, user_answers

        show_tool_call(action, args)
        observation = execute_tool(action, args)

        is_tool_success = not observation.startswith("Error:")
        show_tool_status(
            is_tool_success, error_msg=observation if not is_tool_success else ""
        )

        self.messages.append({"role": "assistant", "content": json.dumps(decision)})
        self.messages.append(
            {"role": "user", "content": f"OBSERVATION from {action}:\n{observation}"}
        )
        return False, observation

    def run(self, task: str) -> str:
        if not self.messages:
            initial_prompt = f"{build_system_prompt()}\n\n---\nUSER TASK:\n{task}"
            self.messages.append({"role": "user", "content": initial_prompt})
        else:
            self.messages.append({"role": "user", "content": task})

        for current_step in range(1, self.max_steps + 1):
            is_finished, result = self.step()

            if is_finished:
                show_final_answer(result)
                return result

        console.print(
            "\n[bold red]Agent Stopped:[/bold red] Maximum step limit reached."
        )
        return "Task failed: Step limit reached."
