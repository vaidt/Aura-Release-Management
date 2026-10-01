"""Shared fail-closed CLI helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from release.canonicalize import load_json_bytes
from release.errors import RefusalError, RMError


class UsageError(Exception):
    """An invalid command-line invocation."""


class RMArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def read_json_file(path: str | Path) -> Any:
    try:
        return load_json_bytes(Path(path).read_bytes())
    except OSError as exc:
        raise RefusalError(f"cannot read required input: {path}") from exc


def report_failure(error: Exception) -> int:
    print(json.dumps({"ok": False, "error": str(error)}), file=sys.stdout)
    if isinstance(error, UsageError):
        return 64
    if isinstance(error, RefusalError):
        return 65
    if isinstance(error, OSError):
        return 65
    if isinstance(error, (RMError, ValueError)):
        return 1
    return 65


def report_success(result: dict[str, Any]) -> int:
    print(json.dumps({"ok": True, **result}, sort_keys=True), file=sys.stdout)
    return 0
