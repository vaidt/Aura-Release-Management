import unittest

from release.canonicalize import (
    canonicalize_json,
    compute_payload_digest,
    load_json_bytes,
)
from release.errors import VerificationError


class CanonicalizationTests(unittest.TestCase):
    def test_key_order_and_whitespace_do_not_change_canonical_bytes_or_digest(self):
        first = {"z": [1, {"b": True, "a": "value"}], "a": 2}
        second = {"a": 2, "z": [1, {"a": "value", "b": True}]}
        self.assertEqual(canonicalize_json(first), canonicalize_json(second))
        self.assertEqual(compute_payload_digest(first), compute_payload_digest(second))
        pretty = load_json_bytes(b'{ "z" : [1, {"b":true,"a":"value"}], "a":2 }')
        self.assertEqual(canonicalize_json(pretty), canonicalize_json(first))

    def test_utf8_and_deterministic_strings(self):
        encoded = canonicalize_json({"text": "café/雪"})
        self.assertEqual(encoded, '{"text":"café/雪"}'.encode("utf-8"))
        self.assertNotIn(b"\\u", encoded)

    def test_non_finite_floats_and_other_floats_are_rejected(self):
        for value in (float("nan"), float("inf"), 1.5):
            with self.subTest(value=value):
                with self.assertRaises(VerificationError):
                    canonicalize_json({"number": value})
        with self.assertRaises(VerificationError):
            load_json_bytes(b'{"number":NaN}')

    def test_duplicate_keys_and_invalid_unicode_are_rejected(self):
        with self.assertRaises(VerificationError):
            load_json_bytes(b'{"key":1,"key":2}')
        with self.assertRaises(VerificationError):
            canonicalize_json({"invalid": "\ud800"})

    def test_payload_digest_is_reproducible(self):
        payload = {"manifest_type": "AURA_RELEASE_MANIFEST", "version": 1}
        self.assertEqual(
            compute_payload_digest(payload), compute_payload_digest(payload.copy())
        )


if __name__ == "__main__":
    unittest.main()
