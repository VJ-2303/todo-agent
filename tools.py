import os
import subprocess


def list_files(directory=".") -> str:
    """List files and directories in the specified path."""

    try:
        entries = os.listdir(directory)

        if not entries:
            return f"Directory '{directory}' is empty."
        return "\n".join(entries)
    except Exception as e:
        return f"Error: listing directory '{directory}' : {e!s}"


def read_file(path: str) -> str:
    """Reads and returns the content of a file."""

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: reading file '{path}' : {e!s}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates directories if they do not exist."""

    try:
        parent = os.path.dirname(path)

        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}."
    except Exception as e:
        return f"Error: writing to file {path} : {e!s}"


def run_command(command: str) -> str:
    """Executes a shell command on Linux and returns stdout and stderr."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = [f"Exit Code: {result.returncode}"]
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr.strip()}")
        if len(output) == 1:
            output.append("(No output produced)")
        return "\n\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Command '{command} timed out after 30 seconds.'"
    except Exception as e:  # noqa: BLE001
        return f"Error: executing command '{command}': {e!s}"
