from __future__ import annotations

import os
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_CANDIDATE_FILES = (
    _API_ROOT / ".env",
    _API_ROOT / ".env.local",
    _WORKSPACE_ROOT / ".env",
    _WORKSPACE_ROOT / ".env.local",
)


def load_local_env_files() -> None:
    for env_file in _CANDIDATE_FILES:
        if not env_file.is_file():
            continue
        _load_env_file(env_file)


def _load_env_file(env_file: Path) -> None:
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        if not normalized_key or normalized_key in os.environ:
            continue
        os.environ[normalized_key] = _strip_quotes(value.strip())


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
