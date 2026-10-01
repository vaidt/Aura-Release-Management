import base64
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from release.canonicalize import compute_payload_digest
from release.errors import RefusalError, VerificationError
from release.verify import verify_manifest
from tests.helpers import make_context

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "AURA_RELEASE_MANIFEST_M0.example.json"


class FailClosedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.context = make_context(self.root / "repos")

    def tearDown(self):
        self.temp.cleanup()

    def test_release_input_mutation_fails_digest_check(self):
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["release_inputs"]["golden_corpus_sha256"] = "c" * 64
        with self.assertRaisesRegex(VerificationError, "release_inputs_digest"):
            verify_manifest(manifest)

    def test_missing_evidence_refuses_verified_status(self):
        with self.assertRaises(RefusalError):
            verify_manifest(self.context["manifest"])

    def test_promoted_claim_without_separate_record_fails_even_with_valid_signature(self):
        private = Ed25519PrivateKey.generate()
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["status"] = "RELEASE_PROMOTED"
        digest = compute_payload_digest(manifest["payload"])
        manifest["signature"] = {
            "algorithm": "Ed25519",
            "key_id": "test",
            "payload_canonical_sha256": digest,
            "value": base64.b64encode(private.sign(bytes.fromhex(digest))).decode(),
        }
        with self.assertRaisesRegex(VerificationError, "promotion record"):
            verify_manifest(
                manifest,
                evidence=self.context["evidence"],
                policy=self.context["policy"],
                repository_paths=self.context["repositories"],
                golden_corpus_path=self.context["golden_corpus"],
                public_keys={"test": public_bytes},
            )

    def run_cli(self, *args: str, env=None):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=env or os.environ.copy(),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_valid_draft_cli_succeeds_and_emits_json(self):
        result = self.run_cli("-m", "release.verify", str(EXAMPLE))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_malformed_cli_uses_exit_64(self):
        result = self.run_cli("-m", "release.verify")
        self.assertEqual(result.returncode, 64)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_missing_provenance_input_is_operational_refusal_65(self):
        manifest_path = self.root / "verified.json"
        manifest_path.write_text(json.dumps(self.context["manifest"]))
        result = self.run_cli("-m", "release.provenance", str(manifest_path))
        self.assertEqual(result.returncode, 65)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_invalid_release_fails_with_exit_1(self):
        manifest = {
            "payload": {
                "manifest_type": "AURA_RELEASE_MANIFEST",
                "manifest_version": "1.2",
                "protocol_profile": "AURA-M0",
                "release_version": "0.1.0",
                "status": "DRAFT",
                "release_inputs": {"specification_commit_sha": "short"},
            }
        }
        path = self.root / "invalid.json"
        path.write_text(json.dumps(manifest))
        result = self.run_cli("-m", "release.verify", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_malformed_json_is_a_nonzero_cli_failure(self):
        path = self.root / "malformed.json"
        path.write_text('{"payload":')
        result = self.run_cli("-m", "release.verify", str(path))
        self.assertEqual(result.returncode, 1)

    def test_verified_manifest_signing_and_verification_clis(self):
        private = Ed25519PrivateKey.generate()
        private_bytes = private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        manifest_path = self.root / "verified.json"
        evidence_path = self.root / "evidence.json"
        policy_path = self.root / "policy.json"
        signed_path = self.root / "signed.json"
        manifest_path.write_text(json.dumps(self.context["manifest"]))
        evidence_path.write_text(json.dumps(self.context["evidence"]))
        policy_path.write_text(json.dumps(self.context["policy"]))
        args = [
            "--evidence",
            str(evidence_path),
            "--golden-corpus",
            str(self.context["golden_corpus"]),
            "--policy",
            str(policy_path),
        ]
        for role, path in self.context["repositories"].items():
            args.extend(("--repository", f"{role}={path}"))
        signing_env = os.environ.copy()
        signing_env["AURA_RM_ED25519_PRIVATE_KEY_B64"] = base64.b64encode(
            private_bytes
        ).decode("ascii")
        signing_env["AURA_RM_ED25519_KEY_ID"] = "test-key"
        signed = self.run_cli(
            "-m",
            "release.signing",
            str(manifest_path),
            *args,
            "--output",
            str(signed_path),
            env=signing_env,
        )
        self.assertEqual(signed.returncode, 0, signed.stdout + signed.stderr)

        verify_env = os.environ.copy()
        verify_env["AURA_RM_TRUSTED_PUBLIC_KEYS_JSON"] = json.dumps(
            {"test-key": base64.b64encode(public_bytes).decode("ascii")}
        )
        verified = self.run_cli(
            "-m",
            "release.verify",
            str(signed_path),
            *args,
            env=verify_env,
        )
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        result = json.loads(verified.stdout)
        self.assertEqual(result["status"], "SIGNED")
        self.assertTrue(result["verification_gates_passed"])
        self.assertTrue(result["signature_valid"])


if __name__ == "__main__":
    unittest.main()
