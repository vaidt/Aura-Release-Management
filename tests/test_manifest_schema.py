import copy
import unittest

from release.canonicalize import compute_inputs_digest
from release.errors import VerificationError
from release.manifest import validate_manifest_schema
from tests.helpers import make_context


def draft_manifest():
    return {
        "payload": {
            "manifest_type": "AURA_RELEASE_MANIFEST",
            "manifest_version": "1.2",
            "protocol_profile": "AURA-M0",
            "release_version": "0.1.0",
            "status": "DRAFT",
        }
    }


class ManifestSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile

        cls.temp = tempfile.TemporaryDirectory()
        cls.context = make_context(__import__("pathlib").Path(cls.temp.name))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_valid_states_and_draft(self):
        validate_manifest_schema(draft_manifest())
        candidate = copy.deepcopy(self.context["manifest"])
        candidate["payload"]["status"] = "RELEASE_CANDIDATE"
        validate_manifest_schema(candidate)
        verified = copy.deepcopy(self.context["manifest"])
        validate_manifest_schema(verified)
        for status in ("SIGNED", "RELEASE_PROMOTED"):
            signed = copy.deepcopy(verified)
            signed["payload"]["status"] = status
            signed["signature"] = {
                "algorithm": "Ed25519",
                "key_id": "test-key",
                "payload_canonical_sha256": "c" * 64,
                "value": "AA==",
            }
            validate_manifest_schema(signed)

    def test_invalid_git_sha_and_oci_digest(self):
        invalid_sha = copy.deepcopy(self.context["manifest"])
        invalid_sha["payload"]["release_inputs"]["tck_commit_sha"] = "abc"
        with self.assertRaises(VerificationError):
            validate_manifest_schema(invalid_sha)
        invalid_digest = copy.deepcopy(self.context["manifest"])
        invalid_digest["payload"]["artifact"]["digest"] = "sha512:" + "a" * 128
        with self.assertRaises(VerificationError):
            validate_manifest_schema(invalid_digest)

    def test_missing_required_and_unknown_fields_fail(self):
        missing = copy.deepcopy(self.context["manifest"])
        del missing["payload"]["release_inputs"]["tck_commit_sha"]
        with self.assertRaises(VerificationError):
            validate_manifest_schema(missing)
        unknown = draft_manifest()
        unknown["payload"]["untrusted_claim"] = True
        with self.assertRaises(VerificationError):
            validate_manifest_schema(unknown)

    def test_malformed_signature_fails(self):
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["status"] = "SIGNED"
        manifest["signature"] = {
            "algorithm": "Ed25519",
            "key_id": "test-key",
            "payload_canonical_sha256": "c" * 64,
            "value": "***",
        }
        with self.assertRaises(VerificationError):
            validate_manifest_schema(manifest)

    def test_manifest_preparation_recomputes_inputs_digest(self):
        from release.manifest import prepare_manifest

        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["release_inputs_digest"] = "0" * 64
        prepared = prepare_manifest(manifest)
        self.assertEqual(
            prepared["payload"]["release_inputs_digest"],
            compute_inputs_digest(prepared["payload"]["release_inputs"]),
        )


if __name__ == "__main__":
    unittest.main()
