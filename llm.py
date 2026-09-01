import os
from dataclasses import dataclass
from typing import Any

import litellm
from litellm import completion

import config

litellm.suppress_debug_info = True
litellm.drop_params = True
litellm.set_verbose = False
os.environ["LITELLM_LOG"] = "ERROR"


@dataclass
class LLMResponse:
    content: str
    thinking: str = ""
    raw_response: Any = None


class LLMClient:
    def __init__(self):
        self.model = config.MODEL_NAME
        self.api_base = config.API_BASE_URL or None
        self.api_key = config.API_KEY or None
        self.temperature = config.TEMPERATURE
        self.model_identifier = "openai/" + config.MODEL_NAME

    def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Calls the model via LiteLLM and returns clean content & thinking."""
        try:
            response = completion(
                model=self.model_identifier,
                messages=messages,
                api_base=self.api_base,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=4096,
            )

            msg = response.choices[0].message
            raw_content = msg.content or ""
            reasoning = getattr(msg, "reasoning_content", "") or ""

            clean_content = raw_content if raw_content.strip() else reasoning.strip()

            return LLMResponse(
                content=clean_content,
                thinking=reasoning,
                raw_response=response,
            )

        except litellm.exceptions.AuthenticationError as e:
            raise RuntimeError(
                f"LLM Authentication Failed: Invalid API Key ({e!s})"
            ) from e
        except litellm.exceptions.APIConnectionError as e:
            raise RuntimeError(
                f"LLM Connection Failed: Cannot reach {self.api_base or 'endpoint'} ({e!s})"
            ) from e
        except Exception as e:
            raise RuntimeError(f"LLM Request Failed: {e!s}") from e
