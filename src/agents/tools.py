"""
Thin wrappers for tool interactions. Real implementations must be provided by caller
and injected as callables. This avoids hard dependency on network or SDKs.

Expected injected tools (callables):
- llm_chat(prompt: str, system: str | None = None) -> dict | str
- run_shell(commands: list[str]) -> dict { 'returncode': int, 'stdout': str, 'stderr': str }
- write_file(path: str, content: str) -> None
- read_file(path: str) -> str
- list_dir(path: str) -> list[str]
- ensure_dir(path: str) -> None
- generate_image(model: str, prompt: str) -> bytes
"""

from typing import Callable, Dict, Any, List


class Toolbelt:
    def __init__(
        self,
        llm_chat: Callable[[str, str | None], Any],
        run_shell: Callable[[List[str]], Dict[str, Any]],
        write_file: Callable[[str, str], None],
        read_file: Callable[[str], str],
        list_dir: Callable[[str], List[str]],
        ensure_dir: Callable[[str], None],
        generate_image: Callable[[str, str], bytes],
    ) -> None:
        self.llm_chat = llm_chat
        self.run_shell = run_shell
        self.write_file = write_file
        self.read_file = read_file
        self.list_dir = list_dir
        self.ensure_dir = ensure_dir
        self.generate_image = generate_image
