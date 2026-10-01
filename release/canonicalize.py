"""AURA-RM-CANON/1 deterministic JSON encoding and strict JSON loading."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from release.errors import VerificationError

MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _validate_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise VerificationError(f"integer outside canonical range at {path}")
        return
    if isinstance(value, float):
        raise VerificationError(f"floating-point value forbidden at {path}")
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise VerificationError(f"invalid Unicode string at {path}") from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise VerificationError(f"object key is not a string at {path}")
            _validate_value(key, f"{path}.<key>")
            _validate_value(item, f"{path}.{key}")
        return
    raise VerificationError(f"unsupported JSON value at {path}")


def canonicalize_json(value: Any) -> bytes:
    """Encode JSON under RM-CANON/1; this is not RFC 8785."""
    _validate_value(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return text.encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise VerificationError("cannot canonicalize JSON value") from exc


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def compute_payload_digest(payload: dict[str, Any]) -> str:
    return sha256_hex(canonicalize_json(payload))


def compute_inputs_digest(release_inputs: dict[str, Any]) -> str:
    return sha256_hex(canonicalize_json(release_inputs))


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise VerificationError(f"non-finite JSON number forbidden: {value}")


def load_json_bytes(data: bytes) -> Any:
    """Parse UTF-8 JSON while rejecting ambiguous or non-finite input."""
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
        _validate_value(value)
        return value
    except VerificationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise VerificationError("malformed UTF-8 JSON") from exc
