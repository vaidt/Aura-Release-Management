"""Fail-closed RM-0 release manifest verifier and CLI."""

from __future__ import annotations

import argparse
import base64
import binascii
import os
import re
from typing import Any

from release.canonicalize import compute_inputs_digest, load_json_bytes
from release.cli import (
    RMArgumentParser,
    UsageError,
    read_json_file,
    report_failure,
    report_success,
)
from release.errors import RefusalError, VerificationError
from release.manifest import INPUT_FIELDS, validate_manifest_schema
from release.provenance import POLICY_PATH, parse_repository_arg, verify_provenance
from release.signing import verify_signature
from release.state_machine import validate_state_requirements

SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_public_keys_from_environment() -> dict[str, bytes]:
    value = os.environ.get("AURA_RM_TRUSTED_PUBLIC_KEYS_JSON")
    if not value:
        raise RefusalError("trusted public keys are required for signature verification")
    try:
        entries = load_json_bytes(value.encode("utf-8"))
    except VerificationError as exc:
        raise RefusalError("trusted public-key environment input is malformed") from exc
    if not isinstance(entries, dict) or not entries:
        raise RefusalError("trusted public-key mapping is empty")
    keys: dict[str, bytes] = {}
    for key_id, encoded in entries.items():
        if not isinstance(key_id, str) or not key_id:
            raise RefusalError("trusted public-key identifier is invalid")
        if not isinstance(encoded, str):
            raise RefusalError("trusted public key must be base64 text")
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RefusalError("trusted public key is malformed base64") from exc
        if (
            len(decoded) != 32
            or base64.b64encode(decoded).decode("ascii") != encoded
        ):
            raise RefusalError("trusted public key has invalid encoding or length")
        keys[key_id] = decoded
    return keys


def verify_manifest(
    manifest: Any,
    *,
    evidence: Any = None,
    policy: Any = None,
    repository_paths: dict[str, str] | None = None,
    public_keys: dict[str, bytes] | None = None,
    promotion_record: Any = None,
) -> dict[str, Any]:
    validate_manifest_schema(manifest)
    payload = manifest["payload"]
    status = payload["status"]
    if status == "REJECTED":
        raise VerificationError("REJECTED manifests cannot pass verification")

    release_inputs = payload.get("release_inputs")
    digest = payload.get("release_inputs_digest")
    if release_inputs is not None:
        if not isinstance(release_inputs, dict):
            raise VerificationError("release_inputs must be an object")
        if INPUT_FIELDS.issubset(release_inputs):
            actual_digest = compute_inputs_digest(release_inputs)
            if digest is not None and digest != actual_digest:
                raise VerificationError("release_inputs_digest mismatch")
        elif digest is not None:
            raise VerificationError("cannot verify digest of incomplete release_inputs")

    gates_passed = False
    if status in ("VERIFIED", "SIGNED", "RELEASE_PROMOTED"):
        if evidence is None:
            raise RefusalError("separate provenance evidence is required")
        trusted_policy = policy if policy is not None else read_json_file(POLICY_PATH)
        verify_provenance(manifest, evidence, trusted_policy, repository_paths)
        if payload["specification"]["commit_sha"] != release_inputs[
            "specification_commit_sha"
        ]:
            raise VerificationError("specification commit does not match release inputs")
        gates_passed = True

    signature_valid = False
    if "signature" in manifest:
        verify_signature(manifest, public_keys)
        signature_valid = True
    if status in ("SIGNED", "RELEASE_PROMOTED") and not signature_valid:
        raise VerificationError("signature is required for this release state")
    validate_state_requirements(
        manifest,
        promotion_record,
        signature_valid=signature_valid,
        verification_gates_passed=gates_passed,
    )
    return {
        "status": status,
        "verification_gates_passed": gates_passed,
        "signature_valid": signature_valid,
        "promotion_evidence_valid": status == "RELEASE_PROMOTED",
    }


def _parser() -> argparse.ArgumentParser:
    parser = RMArgumentParser(description="Verify an RM-0 release manifest")
    parser.add_argument("manifest", help="manifest JSON file")
    parser.add_argument("--evidence", help="separate provenance evidence JSON file")
    parser.add_argument("--promotion-record", help="separate local promotion record JSON")
    parser.add_argument("--policy", default=str(POLICY_PATH))
    parser.add_argument(
        "--repository",
        action="append",
        default=[],
        metavar="ROLE=PATH",
        help="local Git repository path; repeat once per protected role",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        paths: dict[str, str] = {}
        for value in args.repository:
            role, path = parse_repository_arg(value)
            if role in paths:
                raise UsageError(f"duplicate repository path for {role}")
            paths[role] = path
        manifest = read_json_file(args.manifest)
        evidence = read_json_file(args.evidence) if args.evidence else None
        policy = read_json_file(args.policy)
        promotion = (
            read_json_file(args.promotion_record) if args.promotion_record else None
        )
        status = (
            manifest.get("payload", {}).get("status")
            if isinstance(manifest, dict)
            else None
        )
        keys = (
            load_public_keys_from_environment()
            if status in ("SIGNED", "RELEASE_PROMOTED")
            or (isinstance(manifest, dict) and "signature" in manifest)
            else None
        )
        result = verify_manifest(
            manifest,
            evidence=evidence,
            policy=policy,
            repository_paths=paths,
            public_keys=keys,
            promotion_record=promotion,
        )
        return report_success(result)
    except (UsageError, RefusalError, VerificationError, OSError, ValueError) as exc:
        return report_failure(exc)


if __name__ == "__main__":
    raise SystemExit(main())
