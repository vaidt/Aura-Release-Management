"""Ed25519 signing and independent manifest signature verification."""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from release.canonicalize import compute_payload_digest
from release.cli import (
    RMArgumentParser,
    UsageError,
    read_json_file,
    report_failure,
)
from release.errors import RefusalError, VerificationError
from release.manifest import validate_manifest_schema


def _decode_base64(value: Any, label: str, expected_size: int) -> bytes:
    if not isinstance(value, str):
        raise VerificationError(f"{label} must be base64 text")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise VerificationError(f"{label} is malformed base64") from exc
    if len(decoded) != expected_size or base64.b64encode(decoded).decode("ascii") != value:
        raise VerificationError(f"{label} has an invalid encoding or length")
    return decoded


def sign_manifest(
    manifest: dict[str, Any], private_key_bytes: bytes, key_id: str
) -> dict[str, Any]:
    if not isinstance(manifest, dict) or not isinstance(
        manifest.get("payload"), dict
    ):
        raise VerificationError("manifest payload is required for signing")
    validate_manifest_schema(manifest)
    if not isinstance(key_id, str) or not key_id:
        raise VerificationError("signing key identifier is required")
    if len(private_key_bytes) != 32:
        raise VerificationError("Ed25519 private key must be 32 raw bytes")
    if manifest["payload"].get("status") != "VERIFIED":
        raise VerificationError("only a VERIFIED manifest can be signed")
    signed = copy.deepcopy(manifest)
    signed["payload"]["status"] = "SIGNED"
    digest = compute_payload_digest(signed["payload"])
    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature = key.sign(bytes.fromhex(digest))
    signed["signature"] = {
        "algorithm": "Ed25519",
        "key_id": key_id,
        "payload_canonical_sha256": digest,
        "value": base64.b64encode(signature).decode("ascii"),
    }
    return signed


def verify_signature(
    manifest: dict[str, Any], trusted_public_keys: dict[str, bytes] | None
) -> None:
    signature = manifest.get("signature") if isinstance(manifest, dict) else None
    if not isinstance(signature, dict):
        raise VerificationError("manifest signature is required")
    if signature.get("algorithm") != "Ed25519":
        raise VerificationError("unsupported signature algorithm")
    key_id = signature.get("key_id")
    if not isinstance(key_id, str) or not key_id:
        raise VerificationError("signature key identifier is invalid")
    if not isinstance(trusted_public_keys, dict) or not trusted_public_keys:
        raise RefusalError("trusted Ed25519 public keys are required")
    public_key_bytes = trusted_public_keys.get(key_id)
    if public_key_bytes is None:
        raise VerificationError("signature key is not trusted")
    if len(public_key_bytes) != 32:
        raise VerificationError("trusted Ed25519 public key must be 32 raw bytes")
    payload = manifest.get("payload")
    if not isinstance(payload, dict):
        raise VerificationError("manifest payload is required")
    digest = compute_payload_digest(payload)
    if signature.get("payload_canonical_sha256") != digest:
        raise VerificationError("canonical payload digest does not match signature")
    signature_bytes = _decode_base64(signature.get("value"), "signature", 64)
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature_bytes, bytes.fromhex(digest)
        )
    except InvalidSignature as exc:
        raise VerificationError("Ed25519 signature verification failed") from exc


def _key_from_environment() -> tuple[bytes, str]:
    encoded = os.environ.get("AURA_RM_ED25519_PRIVATE_KEY_B64")
    key_id = os.environ.get("AURA_RM_ED25519_KEY_ID")
    if not encoded or not key_id:
        raise RefusalError("signing key and key identifier environment are required")
    return _decode_base64(encoded, "private key", 32), key_id


def _parser() -> argparse.ArgumentParser:
    parser = RMArgumentParser(description="Sign a verified RM-0 manifest")
    parser.add_argument("manifest", help="VERIFIED manifest JSON file")
    parser.add_argument("--evidence", help="separate provenance evidence JSON file")
    parser.add_argument(
        "--repository",
        action="append",
        default=[],
        metavar="ROLE=PATH",
        help="local Git repository path; repeat once per protected role",
    )
    parser.add_argument("--golden-corpus", help="local Golden Corpus file to hash")
    parser.add_argument("--policy")
    parser.add_argument("--output", help="output signed manifest path")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not args.evidence:
            raise RefusalError("separate provenance evidence file is required")
        private_key, key_id = _key_from_environment()
        from release.provenance import POLICY_PATH, parse_repository_arg

        paths: dict[str, str] = {}
        for value in args.repository:
            role, path = parse_repository_arg(value)
            if role in paths:
                raise UsageError(f"duplicate repository path for {role}")
            paths[role] = path
        manifest = read_json_file(args.manifest)
        evidence = read_json_file(args.evidence)
        policy = read_json_file(args.policy or POLICY_PATH)
        from release.verify import verify_manifest

        if not isinstance(manifest, dict) or not isinstance(
            manifest.get("payload"), dict
        ):
            raise VerificationError("manifest payload is required")
        if manifest["payload"].get("status") != "VERIFIED":
            raise VerificationError("only a VERIFIED manifest can be signed")
        verify_manifest(
            manifest,
            evidence=evidence,
            policy=policy,
            repository_paths=paths,
            golden_corpus_path=args.golden_corpus,
        )
        signed = sign_manifest(manifest, private_key, key_id)
        public_key = Ed25519PrivateKey.from_private_bytes(
            private_key
        ).public_key()
        from cryptography.hazmat.primitives import serialization

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        verify_signature(signed, {key_id: public_bytes})
        output = json.dumps(signed, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except SystemExit as exc:
        return int(exc.code)
    except (UsageError, RefusalError, VerificationError, OSError, ValueError) as exc:
        return report_failure(exc)


if __name__ == "__main__":
    raise SystemExit(main())
