import fnmatch
import os
import re
import subprocess

from ddgs import DDGS
from trafilatura import extract, fetch_url


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


def replace_in_file(path: str, target: str, replacement: str) -> str:
    if not os.path.exists(path):
        return f"Error: File '{path}' does not exist."
    if not os.path.isfile(path):
        return f"Error: Path '{path}' is a directory, not a file."

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        match_count = content.count(target)

        if match_count == 0:
            return f"Error: Target string not found in '{path}'."

        if match_count > 1:
            return f"Error: Target string matched {match_count} times in {path}. Provide more surrounding context lines."

        new_content = content.replace(target, replacement, 1)

        with open(path, "w", encoding="utf-8") as f:
            _ = f.write(new_content)
        return f"Successfully replaced target content in '{path}'"

    except UnicodeDecodeError:
        return f"Error: File '{path}' is a binary file or uses an unsupported encoding."
    except Exception as e:
        return f"Error: Failed to replace content in '{path}': {e!s}"


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def grep_search(
    query: str,
    path: str = ".",
    is_regex: bool = False,
    file_pattern: str = "*",
    max_results: int = 50,
) -> str:
    """
    Searches for a keyword or regex pattern across files in a directory.
    Returns matching file paths, line numbers, and line contents.

    Parameters:
        query (str): Text string or regular expression to search for.
        path (str): Root directory or single file path to search within.
        is_regex (bool): If True, treats query as a regex pattern. Default is False.
        file_pattern (str): Glob filter for file names (e.g. '*.py', '*.json'). Default is '*'.
        max_results (int): Maximum number of matching lines to return. Default is 50.

    Returns:
        str: Formatted list of matches or descriptive message.
    """
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist."

    # Prepare compiled regex pattern
    try:
        flags = 0
        pattern = (
            re.compile(query, flags)
            if is_regex
            else re.compile(re.escape(query), flags)
        )
    except re.error as e:
        return f"Error: Invalid regular expression '{query}': {e!s}"

    matches = []

    # Handle searching a single file directly
    if os.path.isfile(path):
        target_files = [path]
    else:
        target_files = []
        for root, dirs, files in os.walk(path):
            # Prune ignored directories in-place
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORED_DIRECTORIES and not d.startswith(".")
            ]
            for file in files:
                if fnmatch.fnmatch(file, file_pattern):
                    target_files.append(os.path.join(root, file))

    # Scan collected files
    for file_path in target_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, start=1):
                    if pattern.search(line):
                        clean_line = line.strip()
                        matches.append(f"{file_path}:{line_num}: {clean_line}")
                        if len(matches) >= max_results:
                            break
        except Exception:  # noqa: S112
            continue

        if len(matches) >= max_results:
            break

    if not matches:
        return f"No matches found for query '{query}' in '{path}' (filter: '{file_pattern}')."

    result_text = "\n".join(matches)
    if len(matches) >= max_results:
        result_text += f"\n\n[Note: Output capped at {max_results} results.]"

    return result_text


def find_files(
    pattern: str = "*",
    directory: str = ".",
    max_depth: int = 5,
    max_results: int = 50,
) -> str:
    """
    Recursively finds files matching a glob pattern within a directory.

    Parameters:
        pattern (str): Glob pattern to match against filenames (e.g. '*.py', '*config*').
        directory (str): Root directory to search from. Default is '.'.
        max_depth (int): Maximum subdirectory depth to traverse. Default is 5.
        max_results (int): Maximum number of file paths to return. Default is 50.

    Returns:
        str: Newline-separated list of relative file paths.
    """
    if not os.path.exists(directory):
        return f"Error: Directory '{directory}' does not exist."

    if not os.path.isdir(directory):
        return f"Error: Path '{directory}' is not a directory."

    matched_paths = []
    base_depth = directory.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(directory):
        # Calculate current depth relative to root directory
        current_depth = root.count(os.sep) - base_depth
        if current_depth >= max_depth:
            dirs.clear()  # Stop descending deeper
            continue

        # Prune hidden and junk directories in-place
        dirs[:] = [
            d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")
        ]

        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                rel_path = os.path.relpath(os.path.join(root, filename), directory)
                matched_paths.append(rel_path)
                if len(matched_paths) >= max_results:
                    break

        if len(matched_paths) >= max_results:
            break

    if not matched_paths:
        return f"No files matching pattern '{pattern}' found in '{directory}'."

    output = "\n".join(matched_paths)
    if len(matched_paths) >= max_results:
        output += f"\n\n[Note: Output capped at {max_results} files.]"

    return output


def search_web(query: str, max_results: int = 5) -> str:
    """Searches DuckDuckGo and returns formatted titles, URLs, and snippets."""
    try:
        results = []
        with DDGS() as ddgs:
            for idx, r in enumerate(ddgs.text(query, max_results=max_results), start=1):
                title = r.get("title", "No Title")
                url = r.get("href", "")
                snippet = r.get("body", "")
                results.append(f"{idx}. [{title}]({url})\n   {snippet}")

        if not results:
            return f"No search results found for query: '{query}'"
        return "WEB SEARCH RESULTS:\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error: Web search failed: {e!s}"


def fetch_web_page(url: str, max_chars: int = 8000) -> str:
    """Fetches a webpage and converts its main body into clean Markdown."""
    try:
        downloaded = fetch_url(url)
        if not downloaded:
            return f"Error: Could not download content from '{url}'."

        markdown_content = extract(
            downloaded,
            output_format="markdown",
            include_links=True,
            favor_precision=True,
        )
        if not markdown_content:
            return f"Error: Could not extract readable text from '{url}'."

        if len(markdown_content) > max_chars:
            markdown_content = (
                markdown_content[:max_chars]
                + "\n\n[Warning: Web page content truncated to preserve context window]"
            )

        return f"PAGE CONTENT FROM {url}:\n\n{markdown_content}"
    except Exception as e:
        return f"Error: Failed to fetch webpage '{url}': {e!s}"
