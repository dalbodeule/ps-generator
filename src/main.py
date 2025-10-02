from typing import Any, Dict, List
import os
import logging
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from agents import AuthoringState, AuthoringConfig, build_authoring_graph
from agents.tools import Toolbelt
from dotenv import load_dotenv


load_dotenv()

def _real_llm(prompt: str, system: str | None = None) -> Any:
    logging.info("Starting LLM step...")
    llm = ChatOpenAI(
        model="gpt-5",
        temperature=0.2,
    )

    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    logging.info("LLM step completed")
    return response.content


def _noop_shell(commands: List[str]) -> Dict[str, Any]:
    logging.info("Running shell step...")
    return {"returncode": 0, "stdout": "\n".join(commands), "stderr": ""}


def _memfs_writer_factory(storage: Dict[str, str]):
    def _write_file(path: str, content: str) -> None:
        storage[path] = content
    return _write_file


def _memfs_reader_factory(storage: Dict[str, str]):
    def _read_file(path: str) -> str:
        return storage.get(path, "")
    return _read_file


def _memfs_listdir_factory(storage: Dict[str, str]):
    def _list_dir(prefix: str) -> List[str]:
        return [p for p in storage.keys() if p.startswith(prefix)]
    return _list_dir


def _memfs_ensuredir(_: str) -> None:
    return None


def _fake_image(_: str, __: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n"  # PNG 헤더 바이트


def main() -> None:
    # 0) Setup OpenAI API
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key: ")

    # 1) Initialize problem configuration
    description = input("Enter problem description: ")

    # 2) LangGraph style pipeline setup
    graph = build_authoring_graph()

    # 3) Prepare Toolbelt (memory filesystem/dummy runner)
    storage: Dict[str, str] = {}
    tb = Toolbelt(
        llm_chat=_real_llm,
        run_shell=_noop_shell,
        write_file=_memfs_writer_factory(storage),
        read_file=_memfs_reader_factory(storage),
        list_dir=_memfs_listdir_factory(storage),
        ensure_dir=_memfs_ensuredir,
        generate_image=_fake_image,
    )

    # 4) Initialize state and config
    state = AuthoringState(description)
    cfg = AuthoringConfig()
    final_state = graph(state, cfg, tb)

    # 5) Output generated problem files
    for path, content in storage.items():
        print(f"Generated {path}:")
        print(content)
        print("-" * 80)


if __name__ == "__main__":
    main()