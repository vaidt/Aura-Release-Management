"""Offline verification of RM-0 repository and evidence provenance."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from release.canonicalize import load_json_bytes
from release.cli import (
    RMArgumentParser,
    UsageError,
    read_json_file,
    report_failure,
    report_success,
)
from release.errors import RefusalError, VerificationError

POLICY_PATH = (
    Path(__file__).resolve().parent.parent / "policy" / "trusted_repositories.json"
)
SPECIFICATION_REF = "refs/tags/M0-BASELINE-v1.0"
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ROLES = ("specification", "implementation", "tck", "assurance")
EVIDENCE_FIELDS = {
    "specification": {"repository", "ref", "commit_sha"},
    "implementation": {
        "repository",
        "commit_sha",
        "artifact_attestation_path",
    },
    "tck": {"repository", "commit_sha", "evidence_path"},
    "assurance": {"repository", "commit_sha", "evidence_path"},
}


def load_trust_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict) or set(policy) != {
        "repositories",
        "artifact_repositories",
    }:
        raise VerificationError("trust policy has an invalid shape")
    repositories = policy["repositories"]
    if not isinstance(repositories, dict) or set(repositories) != set(ROLES):
        raise VerificationError("trust policy must define all protected roles")
    if any(
        not isinstance(repository, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
        for repository in repositories.values()
    ):
        raise VerificationError("trust policy contains an invalid repository")
    artifacts = policy["artifact_repositories"]
    if not isinstance(artifacts, list) or any(
        not isinstance(repository, str) or not repository
        for repository in artifacts
    ):
        raise VerificationError("trust policy artifact allowlist is invalid")
    if len(artifacts) != len(set(artifacts)):
        raise VerificationError("trust policy artifact allowlist contains duplicates")
    return policy


def _run_git(repository_path: Path, *arguments: str) -> bytes:
    executable = os.environ.get("GIT_EXECUTABLE", "git")
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    try:
        result = subprocess.run(
            [
                executable,
                "-C",
                str(repository_path),
                "--no-optional-locks",
                *arguments,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RefusalError("local Git inspection is unavailable") from exc
    if result.returncode != 0:
        raise VerificationError("local Git provenance check failed")
    return result.stdout


def _check_repository_identity(path: Path, repository: str) -> None:
    remote = _run_git(path, "config", "--get", "remote.origin.url").decode(
        "utf-8", errors="strict"
    ).strip()
    accepted = {
        f"https://github.com/{repository}.git",
        f"https://github.com/{repository}",
        f"git@github.com:{repository}.git",
        f"ssh://git@github.com/{repository}.git",
    }
    if remote not in accepted:
        raise VerificationError("local Git origin does not match trusted repository")


def _check_commit(
    path: Path, sha: str, *, clean: bool = False, require_head: bool = False
) -> None:
    if not GIT_SHA.fullmatch(sha):
        raise VerificationError("invalid Git commit SHA")
    _run_git(path, "cat-file", "-e", f"{sha}^{{commit}}")
    if require_head and _run_git(path, "rev-parse", "--verify", "HEAD^{commit}").decode(
        "ascii", errors="strict"
    ).strip() != sha:
        raise VerificationError("vNEXT checkout is not at the declared commit")
    if clean and _run_git(path, "status", "--porcelain", "--untracked-files=all"):
        raise VerificationError("vNEXT working tree is not clean")


def _check_specification_ref(path: Path, expected_sha: str) -> None:
    resolved = _run_git(
        path, "rev-parse", "--verify", f"{SPECIFICATION_REF}^{{commit}}"
    ).decode("ascii", errors="strict").strip()
    if resolved != expected_sha:
        raise VerificationError("specification tag does not resolve to declared SHA")


def _safe_tree_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\x00" in value
    ):
        raise VerificationError("invalid evidence path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise VerificationError("evidence path must stay within its Git tree")
    return path.as_posix()


def _read_committed_file(repository: Path, sha: str, relative_path: Any) -> bytes:
    safe_path = _safe_tree_path(relative_path)
    return _run_git(
        repository,
        "show",
        "--no-ext-diff",
        "--no-textconv",
        "--format=",
        f"{sha}:{safe_path}",
    )


def _exact_object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise VerificationError(f"{label} evidence has an invalid shape")
    return value


def verify_provenance(
    manifest: dict[str, Any],
    evidence: Any,
    policy: Any,
    repository_paths: dict[str, str | Path] | None,
) -> None:
    trusted = load_trust_policy(policy)
    if not trusted["artifact_repositories"]:
        raise RefusalError("no trusted artifact repository is configured")
    if not isinstance(evidence, dict) or set(evidence) != set(ROLES):
        raise VerificationError("provenance evidence must define all protected roles")
    if not isinstance(repository_paths, dict) or set(repository_paths) != set(ROLES):
        raise RefusalError("local paths for all four trusted repositories are required")

    payload = manifest["payload"]
    inputs = payload["release_inputs"]
    specification = payload["specification"]
    artifact = payload["artifact"]
    declared_provenance = payload["provenance"]
    role_shas = {
        "specification": inputs["specification_commit_sha"],
        "implementation": inputs["vnext_commit_sha"],
        "tck": inputs["tck_commit_sha"],
        "assurance": inputs["assurance_commit_sha"],
    }
    records: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for role in ROLES:
        record = _exact_object(evidence[role], EVIDENCE_FIELDS[role], role)
        records[role] = record
        if record["repository"] != trusted["repositories"][role]:
            raise VerificationError(f"untrusted repository for {role}")
        if record["commit_sha"] != role_shas[role]:
            raise VerificationError(f"provenance SHA mismatch for {role}")
        path = Path(repository_paths[role]).expanduser()
        if not path.is_dir():
            raise RefusalError(f"local repository is unavailable for {role}")
        paths[role] = path
        _check_repository_identity(path, trusted["repositories"][role])
        _check_commit(
            path,
            role_shas[role],
            clean=(role == "implementation"),
            require_head=(role == "implementation"),
        )

    spec = records["specification"]
    if (
        specification["repository"] != trusted["repositories"]["specification"]
        or spec["ref"] != SPECIFICATION_REF
        or specification["ref"] != SPECIFICATION_REF
        or specification["commit_sha"] != role_shas["specification"]
    ):
        raise VerificationError("specification identity does not match trusted policy")
    _check_specification_ref(paths["specification"], role_shas["specification"])

    implementation_bytes = _read_committed_file(
        paths["implementation"],
        role_shas["implementation"],
        records["implementation"]["artifact_attestation_path"],
    )
    implementation_attestation = load_json_bytes(implementation_bytes)
    _exact_object(
        implementation_attestation,
        {"artifact_repository", "artifact_digest"},
        "implementation artifact",
    )
    implementation_digest = hashlib.sha256(implementation_bytes).hexdigest()
    if (
        implementation_digest
        != declared_provenance["implementation"]["evidence_sha256"]
    ):
        raise VerificationError("implementation evidence digest mismatch")
    if artifact["repository"] not in trusted["artifact_repositories"]:
        raise VerificationError("untrusted OCI artifact repository")
    if (
        implementation_attestation["artifact_repository"] != artifact["repository"]
        or implementation_attestation["artifact_digest"] != artifact["digest"]
    ):
        raise VerificationError("artifact attestation does not match manifest artifact")

    tck_bytes = _read_committed_file(
        paths["tck"], role_shas["tck"], records["tck"]["evidence_path"]
    )
    tck_report = _exact_object(
        load_json_bytes(tck_bytes),
        {"matrix_version", "artifact_digest", "golden_corpus_sha256"},
        "TCK",
    )
    tck_provenance = declared_provenance["tck"]
    tck_digest = hashlib.sha256(tck_bytes).hexdigest()
    if (
        not isinstance(tck_report["matrix_version"], str)
        or not tck_report["matrix_version"]
        or not SHA256.fullmatch(tck_digest)
        or tck_digest != tck_provenance["evidence_sha256"]
        or tck_report["matrix_version"] != tck_provenance["matrix_version"]
        or tck_report["artifact_digest"] != artifact["digest"]
        or tck_report["artifact_digest"] != tck_provenance["tested_artifact_digest"]
        or tck_report["golden_corpus_sha256"]
        != inputs["golden_corpus_sha256"]
        or tck_report["golden_corpus_sha256"]
        != tck_provenance["golden_corpus_sha256"]
    ):
        raise VerificationError("TCK evidence does not match the release inputs")

    assurance_bytes = _read_committed_file(
        paths["assurance"],
        role_shas["assurance"],
        records["assurance"]["evidence_path"],
    )
    assurance_digest = hashlib.sha256(assurance_bytes).hexdigest()
    if assurance_digest != declared_provenance["assurance"]["evidence_sha256"]:
        raise VerificationError("assurance evidence digest mismatch")


def parse_repository_arg(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise UsageError("--repository must be role=local-path")
    role, path = value.split("=", 1)
    if role not in ROLES or not path:
        raise UsageError("--repository must name a protected role and local path")
    return role, path


def _parser() -> argparse.ArgumentParser:
    parser = RMArgumentParser(description="Verify RM-0 provenance evidence")
    parser.add_argument("manifest", help="manifest JSON file")
    parser.add_argument("--evidence", help="separate provenance evidence JSON file")
    parser.add_argument(
        "--repository",
        action="append",
        default=[],
        metavar="ROLE=PATH",
        help="local Git repository path; repeat once per protected role",
    )
    parser.add_argument("--policy", default=str(POLICY_PATH))
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not args.evidence:
            raise RefusalError("separate provenance evidence file is required")
        paths: dict[str, str] = {}
        for value in args.repository:
            role, path = parse_repository_arg(value)
            if role in paths:
                raise UsageError(f"duplicate repository path for {role}")
            paths[role] = path
        manifest = read_json_file(args.manifest)
        evidence = read_json_file(args.evidence)
        policy = read_json_file(args.policy)
        from release.manifest import validate_manifest_schema

        validate_manifest_schema(manifest)
        verify_provenance(manifest, evidence, policy, paths)
        return report_success({"provenance": "PASS"})
    except (UsageError, RefusalError, VerificationError, OSError, ValueError) as exc:
        return report_failure(exc)


if __name__ == "__main__":
    raise SystemExit(main())
