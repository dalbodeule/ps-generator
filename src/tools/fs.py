import os
from typing import List


def _ensure_parent_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def write_file(path: str, content: str) -> None:
    """실제 로컬 파일 시스템에 텍스트 파일을 기록한다."""
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_bytes(path: str, data: bytes) -> None:
    """실제 로컬 파일 시스템에 바이너리 데이터를 기록한다 (이미지 등)."""
    _ensure_parent_dir(path)
    with open(path, "wb") as f:
        f.write(data)


def read_file(path: str) -> str:
    """로컬 파일 시스템에서 텍스트 파일을 읽어온다."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def list_dir(prefix: str) -> List[str]:
    """prefix 아래의 파일 경로들을 재귀적으로 나열한다."""
    result: List[str] = []
    if not os.path.isdir(prefix):
        return result
    for root, _, files in os.walk(prefix):
        for name in files:
            result.append(os.path.join(root, name))
    return result


def ensure_dir(path: str) -> None:
    """디렉터리가 없으면 생성한다."""
    if path:
        os.makedirs(path, exist_ok=True)