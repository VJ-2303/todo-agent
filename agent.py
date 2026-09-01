import json

import config
from dispatcher import execute_tool
from llm import LLMClient
from models import AgentState, MessageRole
from parser import parse_agent_response
from prompts import build_system_prompt
from ui import (
    ask_user_questions,
    console,
    show_chat_response,
    show_final_answer,
    show_thought,
    show_todos_board,
    show_tool_call,
    show_tool_status,
)


class StarAgent:
    def __init__(self):
        self.state = AgentState(task="", max_steps=config.MAX_STEPS)
        self.llm = LLMClient()

    def reset(self):
        self.state.reset()

    def step(self, step_num: int = 1) -> tuple[bool, str]:
        try:
            with console.status("[dim]Thinking...[/dim]", spinner="dots"):
                llm_response = self.llm.generate(messages=self.state.get_llm_messages())
        except Exception as e:
            console.print(f"\n[bold red]✗ Connection Error:[/bold red] {e!s}")
            return True, ""

        success, decision, error_msg = parse_agent_response(llm_response.content)

        if not success or decision is None:
            self.state.add_message(
                MessageRole.ASSISTANT, llm_response.content, step_num=step_num
            )
            retry_prompt = (
                f"OBSERVATION: Invalid output format ({error_msg}). "
                'Please output strictly a single valid JSON object: {"thought": "...", "action": "tool_name", "args": {...}}'
            )
            self.state.add_message(MessageRole.USER, retry_prompt, step_num=step_num)
            console.print(
                f"  [dim yellow]⚠ Response format issue ({error_msg}) — Retrying step...[/dim yellow]"
            )
            return False, error_msg

        thought_text = decision.thought or llm_response.thinking
        show_thought(thought_text, step_num)

        assistant_payload = decision.raw_json or json.dumps(
            {
                "thought": decision.thought,
                "action": decision.action,
                "args": decision.args,
            }
        )

        if decision.is_chat:
            chat_msg = decision.args.get("message", "")
            self.state.add_message(MessageRole.ASSISTANT, assistant_payload, step_num)
            self.state.is_finished = True
            self.state.final_result = chat_msg
            show_chat_response(chat_msg)
            return True, chat_msg

        if decision.is_final_answer:
            final_msg = decision.args.get("message", "Task completed.")
            self.state.add_message(MessageRole.ASSISTANT, assistant_payload, step_num)
            self.state.is_finished = True
            self.state.final_result = final_msg
            show_final_answer(final_msg)
            return True, final_msg

        if decision.is_clarification:
            user_answer = ask_user_questions(decision.args)
            self.state.add_message(MessageRole.ASSISTANT, assistant_payload, step_num)
            self.state.add_message(
                MessageRole.USER, f"CLARIFICATION OBSERVATION:\n{user_answer}", step_num
            )
            return False, user_answer

        show_tool_call(decision.action, decision.args)
        result = execute_tool(decision.action, decision.args, state=self.state)

        show_tool_status(result.success, error_msg=result.error or "")

        if decision.action == "manage_todos" and result.success:
            show_todos_board(self.state.todos)

        self.state.add_message(MessageRole.ASSISTANT, assistant_payload, step_num)
        self.state.add_message(
            MessageRole.USER, result.to_observation_text(decision.action), step_num
        )

        return False, result.output

    def run(self, task: str) -> str:
        self.state.task = task
        step_num = 1

        if not self.state.messages:
            initial_prompt = f"{build_system_prompt()}\n\n---\nUSER TASK:\n{task}"
            self.state.add_message(MessageRole.USER, initial_prompt, step_num)
        else:
            self.state.add_message(MessageRole.USER, task, step_num)

        while step_num <= self.state.max_steps:
            self.state.current_step = step_num
            is_finished, result = self.step(step_num)

            if is_finished:
                return result
            step_num += 1

        console.print(
            "\n[bold red]Agent Stopped:[/bold red] Maximum step limit reached."
        )
        return "Task failed: Step limit reached."
