import json

from openai import OpenAI

import config
from dispatcher import execute_tool
from parser import parse_agent_response
from prompts import build_system_prompt
from ui import (
    console,
    show_final_answer,
    show_thought,
    show_tool_call,
    show_tool_status,
)


class TinyAgent:
    def __init__(self):
        self.max_steps = config.MAX_STEPS
        self.client = OpenAI(base_url=config.API_BASE_URL, api_key=config.API_KEY)
        self.messages = []
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": build_system_prompt()}]

    def step(self) -> tuple[bool, str]:
        with console.status("[dim]Thinking...[/dim]", spinner="dots"):
            response = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=self.messages,
                temperature=config.TEMPERATURE,
            )
        raw_output = response.choices[0].message.content or ""
        success, decision, error_msg = parse_agent_response(raw_output)

        if not success:
            self.messages.append({"role": "assistant", "content": raw_output})
            self.messages.append(
                {
                    "role": "user",
                    "content": f"OBSERVATION: Invalid output format. Error: {error_msg}",
                }
            )
            return False, error_msg

        thought = decision.get("thought", "No Thought provided")
        action = decision.get("action", "")
        args = decision.get("args", {})

        show_thought(thought)

        if action == "final_answer":
            final_msg = args.get("message", "Task completed.")
            self.messages.append({"role": "assistant", "content": json.dumps(decision)})
            return True, final_msg

        show_tool_call(action, args)
        observation = execute_tool(action, args)

        is_tool_success = not observation.startswith("Error:")
        show_tool_status(is_tool_success)

        self.messages.append({"role": "assistant", "content": json.dumps(decision)})
        self.messages.append(
            {"role": "user", "content": f"OBSERVATION from {action}:\n{observation}"}
        )
        return False, observation

    def run(self, task: str) -> str:
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


if __name__ == "__main__":
    agent = TinyAgent()
    task = "List the files in the directory, then give a final answer."
    agent.run(task)
