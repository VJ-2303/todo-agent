import json
import re
from typing import Any


def extract_json_block(raw_text: str) -> str | None:
    """
    Finds and extracts the outermost JSON block from text,
    ignoring markdown code fences and conversational filler.
    """
    text = raw_text.strip()

    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"<\|channel\|>[\s\S]*?<\|message\|>", "", text).strip()

    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, text, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        if extracted.startswith("{") and extracted.endswith("}"):
            return extracted

    start_idx = text.find("{")
    end_idx = text.rfind("}")

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx : end_idx + 1]

    return None


def parse_agent_response(raw_text: str) -> tuple[bool, dict[str, Any] | None, str]:
    """
    Parses the model's raw text into a validated dictionary.
    Returns:
        (success: bool, data: Optional[Dict], error_message: str)
    """
    if not raw_text or not raw_text.strip():
        return False, None, "Response was completely empty."

    candidate = extract_json_block(raw_text)
    if not candidate:
        return False, None, "No valid JSON object structure found (missing '{' or '}')."

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        try:
            sanitized = re.sub(r"(?<!\\)\n", r"\\n", candidate)
            data = json.loads(sanitized)
        except json.JSONDecodeError:
            return False, None, f"Malformed JSON syntax: {e!s}"

    if not isinstance(data, dict):
        return (
            False,
            None,
            "JSON root must be an object (dictionary), not a list or scalar.",
        )

    action = data.get("action")
    if not action:
        return False, None, "Missing required key: 'action'."

    args = data.get("args")
    if args is None:
        data["args"] = {}
    elif not isinstance(args, dict):
        return False, None, "The 'args' field must be an object/dictionary."

    return True, data, ""
