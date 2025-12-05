from typing import Dict, List
import os
import logging

from agents import AuthoringState, AuthoringConfig, build_authoring_graph
from agents.tools import Toolbelt
from dotenv import load_dotenv

from tools.llm import real_llm
from tools.shell import noop_shell
from tools.image import gemini_image
from tools import fs


load_dotenv()



def main() -> None:
    """엔트리 포인트.

    - API 키 설정
    - LangGraph 스타일 그래프 생성
    - Toolbelt 구성 (LLM, 셸, FS, 이미지 생성기)
    - 최종 결과를 메모리 FS에서 출력
    """
    # 0) Setup API keys (OpenAI for LLM, Gemini for nano banana pro images)
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key: ")
    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = input("Enter your Gemini API key (for nano banana pro images): ")

    # 1) Initialize problem configuration
    description = input("Enter problem description: ")
    # Optional explicit problem id (used for ./problems/{id} directory naming)
    problem_id_raw = input("Enter numeric problem id (leave blank for 'pending'): ").strip()
    problem_id: int | None
    if problem_id_raw.isdigit():
        problem_id = int(problem_id_raw)
    else:
        problem_id = None

    # Language and example programming language from environment (.env)
    # LANG: target natural language for problem statements (default: EN)
    # PROGM_LANG: example programming language label (default: C++/17)
    lang_env = os.getenv("LANG", "EN")
    language = lang_env.lower()
    example_prog_lang = os.getenv("PROGM_LANG", "C++/17")

    # 2) LangGraph style pipeline setup
    graph = build_authoring_graph()

    # 3) Prepare Toolbelt (real filesystem + dummy runner)
    tb = Toolbelt(
        llm_chat=real_llm,
        run_shell=noop_shell,
        write_file=fs.write_file,
        read_file=fs.read_file,
        list_dir=fs.list_dir,
        ensure_dir=fs.ensure_dir,
        generate_image=gemini_image,
        write_bytes=fs.write_bytes,
    )

    # 4) Initialize state and config
    state = AuthoringState(description)
    cfg = AuthoringConfig(
        target_language=language,
        example_prog_lang=example_prog_lang,
        problem_id=problem_id,
    )
    final_state = graph(state, cfg, tb)

    # 5) Output notice of generated problem files
    print("Problems have been written under ./problems (e.g., ./problems/{id}/problem.md).")


if __name__ == "__main__":
    main()