import unittest

from release.errors import VerificationError
from release.state_machine import (
    STATES,
    validate_promotion_record,
    validate_state_requirements,
    validate_transition,
)


class StateMachineTests(unittest.TestCase):
    def test_every_valid_forward_transition(self):
        validate_transition("DRAFT", "RELEASE_CANDIDATE")
        validate_transition(
            "RELEASE_CANDIDATE", "VERIFIED", verification_gates_passed=True
        )
        validate_transition("VERIFIED", "SIGNED", signature_valid=True)
        validate_transition(
            "SIGNED", "RELEASE_PROMOTED", promotion_evidence_valid=True
        )

    def test_every_invalid_or_skipping_transition_fails(self):
        valid = {
            ("DRAFT", "RELEASE_CANDIDATE"),
            ("RELEASE_CANDIDATE", "VERIFIED"),
            ("VERIFIED", "SIGNED"),
            ("SIGNED", "RELEASE_PROMOTED"),
        }
        for current in STATES:
            for target in STATES:
                if (current, target) in valid or target == "REJECTED":
                    continue
                with self.subTest(current=current, target=target):
                    with self.assertRaises(VerificationError):
                        validate_transition(current, target)

    def test_any_nonterminal_state_can_be_rejected_and_rejection_is_terminal(self):
        for state in STATES:
            if state in ("RELEASE_PROMOTED", "REJECTED"):
                continue
            validate_transition(state, "REJECTED")
        with self.assertRaises(VerificationError):
            validate_transition("REJECTED", "DRAFT")
        with self.assertRaises(VerificationError):
            validate_transition("RELEASE_PROMOTED", "REJECTED")

    def test_gates_are_required_and_promotion_is_not_self_authorizing(self):
        with self.assertRaises(VerificationError):
            validate_transition("RELEASE_CANDIDATE", "VERIFIED")
        with self.assertRaises(VerificationError):
            validate_transition("VERIFIED", "SIGNED")
        with self.assertRaises(VerificationError):
            validate_transition("SIGNED", "RELEASE_PROMOTED")
        manifest = {
            "payload": {
                "status": "RELEASE_PROMOTED",
                "artifact": {
                    "repository": "registry.example/aura/app",
                    "digest": "sha256:" + "a" * 64,
                },
            }
        }
        with self.assertRaises(VerificationError):
            validate_promotion_record(manifest, None)
        with self.assertRaises(VerificationError):
            validate_state_requirements(
                manifest,
                signature_valid=True,
                verification_gates_passed=True,
            )

    def test_promotion_record_must_bind_exact_digest_and_registry_reference(self):
        manifest = {
            "payload": {
                "artifact": {
                    "repository": "registry.example/aura/app",
                    "digest": "sha256:" + "a" * 64,
                }
            }
        }
        record = {
            "promotion": {
                "artifact_digest": "sha256:" + "a" * 64,
                "promoted_at": "2026-10-01T00:00:00Z",
                "registry_reference": "registry.example/aura/app@sha256:" + "a" * 64,
                "promotion_event_id": "local-event-1",
            }
        }
        validate_promotion_record(manifest, record)
        record["promotion"]["artifact_digest"] = "sha256:" + "b" * 64
        with self.assertRaises(VerificationError):
            validate_promotion_record(manifest, record)
        record["promotion"]["artifact_digest"] = "sha256:" + "a" * 64
        record["promotion"]["promoted_at"] = "not-a-timestamp"
        with self.assertRaises(VerificationError):
            validate_promotion_record(manifest, record)


if __name__ == "__main__":
    unittest.main()
