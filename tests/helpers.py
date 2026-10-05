from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from release.canonicalize import compute_inputs_digest

REPOSITORIES = {
    "specification": "vaidt/aura-specification",
    "implementation": "vaidt/Aura-vNEXT",
    "tck": "vaidt/Aura-Conformance-Kit",
    "assurance": "vaidt/Aura-Guard",
}
ARTIFACT_REPOSITORY = "registry.example/aura/app"
ARTIFACT_DIGEST = "sha256:" + "a" * 64


def _git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _write(path: Path, relative: str, content: bytes) -> None:
    destination = path / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def _commit(path: Path) -> str:
    _git(path, "add", ".")
    _git(
        path,
        "-c",
        "user.name=RM Test",
        "-c",
        "user.email=rm@example.test",
        "commit",
        "-m",
        "fixture",
    )
    return _git(path, "rev-parse", "HEAD")


def _init(path: Path) -> None:
    path.mkdir()
    _git(path, "init", "-q")


def _set_origin(path: Path, repository: str) -> None:
    _git(path, "remote", "add", "origin", f"https://github.com/{repository}.git")


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def make_context(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    corpus_bytes = b"RM-0 Golden Corpus fixture\n"
    golden_corpus_path = root / "golden-corpus.bin"
    golden_corpus_path.write_bytes(corpus_bytes)
    corpus_digest = hashlib.sha256(corpus_bytes).hexdigest()
    repositories = {role: root / role for role in REPOSITORIES}
    for role, path in repositories.items():
        _init(path)
        _set_origin(path, REPOSITORIES[role])
    _write(repositories["specification"], "baseline.txt", b"spec fixture\n")
    shas = {"specification": _commit(repositories["specification"])}
    _git(
        repositories["specification"],
        "tag",
        "M0-BASELINE-v0.1.0-DRAFT",
        shas["specification"],
    )

    implementation_attestation = _json_bytes(
        {
            "artifact_repository": ARTIFACT_REPOSITORY,
            "artifact_digest": ARTIFACT_DIGEST,
        }
    )
    _write(
        repositories["implementation"],
        "release-artifact.json",
        implementation_attestation,
    )
    shas["implementation"] = _commit(repositories["implementation"])

    tck_evidence = _json_bytes(
        {
            "matrix_version": "M0-test-1",
            "artifact_digest": ARTIFACT_DIGEST,
            "golden_corpus_sha256": corpus_digest,
        }
    )
    _write(repositories["tck"], "rm-evidence.json", tck_evidence)
    shas["tck"] = _commit(repositories["tck"])

    assurance_evidence = b"RM-0 assurance evidence fixture\n"
    _write(repositories["assurance"], "rm-evidence.bin", assurance_evidence)
    shas["assurance"] = _commit(repositories["assurance"])

    inputs = {
        "specification_commit_sha": shas["specification"],
        "golden_corpus_sha256": corpus_digest,
        "vnext_commit_sha": shas["implementation"],
        "tck_commit_sha": shas["tck"],
        "assurance_commit_sha": shas["assurance"],
    }
    policy = {
        "repositories": REPOSITORIES.copy(),
        "artifact_repositories": [ARTIFACT_REPOSITORY],
    }
    evidence = {
        "specification": {
            "repository": REPOSITORIES["specification"],
            "ref": "refs/tags/M0-BASELINE-v0.1.0-DRAFT",
            "commit_sha": shas["specification"],
        },
        "implementation": {
            "repository": REPOSITORIES["implementation"],
            "commit_sha": shas["implementation"],
            "artifact_attestation_path": "release-artifact.json",
        },
        "tck": {
            "repository": REPOSITORIES["tck"],
            "commit_sha": shas["tck"],
            "evidence_path": "rm-evidence.json",
        },
        "assurance": {
            "repository": REPOSITORIES["assurance"],
            "commit_sha": shas["assurance"],
            "evidence_path": "rm-evidence.bin",
        },
    }
    manifest = {
        "payload": {
            "manifest_type": "AURA_RELEASE_MANIFEST",
            "manifest_version": "1.2",
            "protocol_profile": "AURA-M0",
            "release_version": "0.1.0",
            "status": "VERIFIED",
            "release_inputs": inputs,
            "release_inputs_digest": compute_inputs_digest(inputs),
            "specification": {
                "repository": REPOSITORIES["specification"],
                "ref": "refs/tags/M0-BASELINE-v0.1.0-DRAFT",
                "commit_sha": shas["specification"],
            },
            "artifact": {
                "type": "oci_container",
                "repository": ARTIFACT_REPOSITORY,
                "digest": ARTIFACT_DIGEST,
            },
            "build": {
                "orchestrator": "Aura-Release-Management",
                "workflow_run_id": "test-run",
                "toolchain": {"python": "3.12.8"},
            },
            "provenance": {
                "implementation": {
                    "evidence_sha256": hashlib.sha256(
                        implementation_attestation
                    ).hexdigest()
                },
                "tck": {
                    "matrix_version": "M0-test-1",
                    "evidence_sha256": hashlib.sha256(tck_evidence).hexdigest(),
                    "tested_artifact_digest": ARTIFACT_DIGEST,
                    "golden_corpus_sha256": corpus_digest,
                },
                "assurance": {
                    "evidence_sha256": hashlib.sha256(
                        assurance_evidence
                    ).hexdigest()
                },
            },
        }
    }
    return {
        "manifest": manifest,
        "evidence": evidence,
        "policy": policy,
        "repositories": repositories,
        "shas": shas,
        "golden_corpus": golden_corpus_path,
    }
