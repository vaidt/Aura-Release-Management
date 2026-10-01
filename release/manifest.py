"""Manifest schema validation, digest preparation, and CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from release.canonicalize import compute_inputs_digest, load_json_bytes
from release.cli import RMArgumentParser, UsageError, report_failure
from release.errors import RefusalError, VerificationError

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / (
    "AURA_RELEASE_MANIFEST_M0.schema.json"
)
INPUT_FIELDS = {
    "specification_commit_sha",
    "golden_corpus_sha256",
    "vnext_commit_sha",
    "tck_commit_sha",
    "assurance_commit_sha",
}


def validate_manifest_schema(manifest: Any) -> None:
    try:
        schema = load_json_bytes(SCHEMA_PATH.read_bytes())
        errors = sorted(
            Draft202012Validator(schema).iter_errors(manifest),
            key=lambda error: (list(map(str, error.absolute_path)), error.message),
        )
    except OSError as exc:
        raise RefusalError("manifest schema is unavailable") from exc
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise VerificationError(f"schema error at {location}: {error.message}")


def prepare_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict) or not isinstance(
        manifest.get("payload"), dict
    ):
        raise VerificationError("manifest must contain an object payload")
    payload = manifest["payload"]
    inputs = payload.get("release_inputs")
    if isinstance(inputs, dict) and INPUT_FIELDS.issubset(inputs):
        if set(inputs) != INPUT_FIELDS:
            raise VerificationError("release_inputs contains unexpected fields")
        payload["release_inputs_digest"] = compute_inputs_digest(inputs)
    validate_manifest_schema(manifest)
    return manifest


def _parser() -> RMArgumentParser:
    parser = RMArgumentParser(description="Prepare an RM-0 release manifest")
    parser.add_argument("input", help="input manifest JSON file")
    parser.add_argument("--output", help="write prepared JSON to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        source = Path(args.input)
        manifest = prepare_manifest(load_json_bytes(source.read_bytes()))
        rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (UsageError, RefusalError, OSError, VerificationError) as exc:
        return report_failure(exc)


if __name__ == "__main__":
    raise SystemExit(main())
