from typing import Dict, List


def memfs_writer_factory(storage: Dict[str, str]):
    """메모리 기반 파일 시스템용 write_file 구현 팩토리."""
    def _write_file(path: str, content: str) -> None:
        storage[path] = content
    return _write_file


def memfs_reader_factory(storage: Dict[str, str]):
    """메모리 기반 파일 시스템용 read_file 구현 팩토리."""
    def _read_file(path: str) -> str:
        return storage.get(path, "")
    return _read_file


def memfs_listdir_factory(storage: Dict[str, str]):
    """메모리 기반 파일 시스템용 list_dir 구현 팩토리."""
    def _list_dir(prefix: str) -> List[str]:
        return [p for p in storage.keys() if p.startswith(prefix)]
    return _list_dir


def memfs_ensuredir(_: str) -> None:
    """메모리 기반이므로 실제 디렉터리 생성은 필요 없음."""
    return None