from typing import Any, Dict, List
import logging


def noop_shell(commands: List[str]) -> Dict[str, Any]:
    """더미 셸 실행기.

    - 실제로 명령을 실행하지 않고, 입력 명령 목록을 stdout 필드에 그대로 돌려준다.
    - LangGraph 파이프라인에서 컴파일/실행 단계를 흉내 내거나 디버깅용으로 사용한다.
    """
    logging.info("Running shell step (noop)...")
    return {
        "returncode": 0,
        "stdout": "\n".join(commands),
        "stderr": "",
    }