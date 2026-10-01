"""Explicit one-way RM-0 release state transitions."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from release.errors import VerificationError

STATES = (
    "DRAFT",
    "RELEASE_CANDIDATE",
    "VERIFIED",
    "SIGNED",
    "RELEASE_PROMOTED",
    "REJECTED",
)
NEXT = {
    "DRAFT": "RELEASE_CANDIDATE",
    "RELEASE_CANDIDATE": "VERIFIED",
    "VERIFIED": "SIGNED",
    "SIGNED": "RELEASE_PROMOTED",
}
UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def validate_promotion_record(
    manifest: dict[str, Any], promotion_record: dict[str, Any] | None
) -> None:
    if not isinstance(promotion_record, dict) or set(promotion_record) != {
        "promotion"
    }:
        raise VerificationError("separate promotion record is required")
    promotion = promotion_record["promotion"]
    if not isinstance(promotion, dict) or set(promotion) != {
        "artifact_digest",
        "promoted_at",
        "registry_reference",
        "promotion_event_id",
    }:
        raise VerificationError("promotion record has an invalid shape")
    artifact = manifest.get("payload", {}).get("artifact", {})
    digest = artifact.get("digest")
    repository = artifact.get("repository")
    if promotion["artifact_digest"] != digest:
        raise VerificationError("promotion artifact digest does not match manifest")
    if promotion["registry_reference"] != f"{repository}@{digest}":
        raise VerificationError("promotion registry reference does not match artifact")
    if not all(
        isinstance(promotion[field], str) and promotion[field]
        for field in ("promoted_at", "promotion_event_id")
    ):
        raise VerificationError("promotion record is incomplete")
    if not UTC_TIMESTAMP.fullmatch(promotion["promoted_at"]):
        raise VerificationError("promotion timestamp must be an ISO-8601 UTC value")
    try:
        datetime.fromisoformat(promotion["promoted_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationError("promotion timestamp is invalid") from exc


def validate_state_requirements(
    manifest: dict[str, Any],
    promotion_record: dict[str, Any] | None = None,
    *,
    signature_valid: bool = False,
    verification_gates_passed: bool = False,
) -> None:
    payload = manifest.get("payload") if isinstance(manifest, dict) else None
    if not isinstance(payload, dict):
        raise VerificationError("manifest payload is required")
    status = payload.get("status")
    if status not in STATES:
        raise VerificationError("unknown release state")
    if status in ("VERIFIED", "SIGNED", "RELEASE_PROMOTED"):
        if not verification_gates_passed:
            raise VerificationError("provenance verification gates have not passed")
    if status in ("SIGNED", "RELEASE_PROMOTED") and not signature_valid:
        raise VerificationError("a valid signature is required for this state")
    if status == "RELEASE_PROMOTED":
        validate_promotion_record(manifest, promotion_record)


def validate_transition(
    current: str,
    target: str,
    *,
    verification_gates_passed: bool = False,
    signature_valid: bool = False,
    promotion_evidence_valid: bool = False,
) -> None:
    if current not in STATES or target not in STATES:
        raise VerificationError("unknown release state")
    if current == "RELEASE_PROMOTED" or current == "REJECTED":
        raise VerificationError("terminal state cannot transition")
    if target == "REJECTED":
        return
    if NEXT.get(current) != target:
        raise VerificationError(f"invalid release transition: {current} -> {target}")
    if target == "VERIFIED" and not verification_gates_passed:
        raise VerificationError("verification gates must pass before VERIFIED")
    if target == "SIGNED" and not signature_valid:
        raise VerificationError("valid signature required before SIGNED")
    if target == "RELEASE_PROMOTED" and not promotion_evidence_valid:
        raise VerificationError("promotion evidence required before promotion")
