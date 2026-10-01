import base64
import copy
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from release.errors import VerificationError
from release.signing import sign_manifest, verify_signature
from tests.helpers import make_context


class SigningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.context = make_context(Path(self.temp.name))
        self.private_key = Ed25519PrivateKey.generate()
        self.private_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.public_bytes = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_ed25519_signature_passes(self):
        signed = sign_manifest(self.context["manifest"], self.private_bytes, "test")
        self.assertEqual(signed["payload"]["status"], "SIGNED")
        verify_signature(signed, {"test": self.public_bytes})

    def test_payload_mutation_fails(self):
        signed = sign_manifest(self.context["manifest"], self.private_bytes, "test")
        signed["payload"]["release_version"] = "0.1.1"
        with self.assertRaises(VerificationError):
            verify_signature(signed, {"test": self.public_bytes})

    def test_signature_mutation_fails(self):
        signed = sign_manifest(self.context["manifest"], self.private_bytes, "test")
        value = base64.b64decode(signed["signature"]["value"])
        signed["signature"]["value"] = base64.b64encode(
            bytes([value[0] ^ 1]) + value[1:]
        ).decode("ascii")
        with self.assertRaises(VerificationError):
            verify_signature(signed, {"test": self.public_bytes})

    def test_wrong_key_fails(self):
        signed = sign_manifest(self.context["manifest"], self.private_bytes, "test")
        wrong = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        with self.assertRaises(VerificationError):
            verify_signature(signed, {"test": wrong})

    def test_key_identifier_must_be_trusted(self):
        signed = sign_manifest(self.context["manifest"], self.private_bytes, "test")
        with self.assertRaises(VerificationError):
            verify_signature(signed, {"other": self.public_bytes})

    def test_signing_cannot_skip_verified_state(self):
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["status"] = "DRAFT"
        with self.assertRaises(VerificationError):
            sign_manifest(manifest, self.private_bytes, "test")


if __name__ == "__main__":
    unittest.main()
