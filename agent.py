import json

from openai import OpenAI

import config
from dispatcher import execute_tool
from parser import parse_agent_response
from prompts import build_system_prompt


class TinyAgent:
    def __init__(self):
        self.max_steps = config.MAX_STEPS
        self.client = OpenAI(base_url=config.API_BASE_URL, api_key=config.API_KEY)
        self.messages = []
        self.reset()

    def reset(self):
        self.messages = [{"role": "system", "content": build_system_prompt()}]

    def step(self) -> tuple[bool, str]:
        response = self.client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=self.messages,
            temperature=config.TEMPERATURE,
        )
        raw_output = response.choices[0].message.content or ""
        success, decision, error_msg = parse_agent_response(raw_output)

        if not success:
            self.messages.append({"role": "assitant", "content": raw_output})
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

        print(f"Thought : {thought}\n")

        if action == "final_answer":
            final_msg = args.get("message", "Task completed.")
            return True, final_msg

        observation = execute_tool(action, args)

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
                print(f"[Agent Finished]: {result}\n")
                return result

        print("[Agent Stopped]: Maximum step limit reached without completion.\n")
        return "Task failed: Step limit reached."
