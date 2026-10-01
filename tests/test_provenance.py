import copy
import tempfile
import unittest
from pathlib import Path

from release.errors import RefusalError, VerificationError
from release.provenance import verify_provenance
from tests.helpers import make_context


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.context = make_context(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def verify(self, manifest=None, evidence=None, policy=None):
        context = self.context
        verify_provenance(
            manifest if manifest is not None else context["manifest"],
            evidence if evidence is not None else context["evidence"],
            policy if policy is not None else context["policy"],
            context["repositories"],
            context["golden_corpus"],
        )

    def test_exact_commits_tag_and_repository_evidence_pass(self):
        self.verify()

    def test_modified_sha_fails(self):
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["release_inputs"]["tck_commit_sha"] = "d" * 40
        with self.assertRaises(VerificationError):
            self.verify(manifest=manifest)

    def test_untrusted_repository_fails(self):
        evidence = copy.deepcopy(self.context["evidence"])
        evidence["tck"]["repository"] = "untrusted/example"
        with self.assertRaises(VerificationError):
            self.verify(evidence=evidence)

    def test_local_repository_origin_must_match_trusted_identity(self):
        from tests.helpers import _git

        path = self.context["repositories"]["tck"]
        _git(path, "remote", "set-url", "origin", "https://github.com/untrusted/example")
        with self.assertRaisesRegex(VerificationError, "origin"):
            self.verify()

    def test_vnext_checkout_must_be_clean_at_exact_declared_commit(self):
        from tests.helpers import _git

        path = self.context["repositories"]["implementation"]
        (path / "extra.txt").write_text("new commit\n")
        _git(path, "add", "extra.txt")
        _git(
            path,
            "-c",
            "user.name=RM Test",
            "-c",
            "user.email=rm@example.test",
            "commit",
            "-m",
            "move HEAD",
        )
        with self.assertRaisesRegex(VerificationError, "declared commit"):
            self.verify()

    def test_wrong_specification_ref_fails(self):
        evidence = copy.deepcopy(self.context["evidence"])
        evidence["specification"]["ref"] = "refs/heads/main"
        with self.assertRaises(VerificationError):
            self.verify(evidence=evidence)

    def test_specification_tag_must_resolve_to_declared_sha(self):
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["release_inputs"]["specification_commit_sha"] = (
            "e" * 40
        )
        manifest["payload"]["specification"]["commit_sha"] = "e" * 40
        evidence = copy.deepcopy(self.context["evidence"])
        evidence["specification"]["commit_sha"] = "e" * 40
        with self.assertRaises(VerificationError):
            self.verify(manifest=manifest, evidence=evidence)

    def test_artifact_repository_is_allowlisted_and_exact_digest_is_tested(self):
        policy = copy.deepcopy(self.context["policy"])
        policy["artifact_repositories"] = []
        with self.assertRaises(RefusalError):
            self.verify(policy=policy)
        manifest = copy.deepcopy(self.context["manifest"])
        manifest["payload"]["artifact"]["digest"] = "sha256:" + "c" * 64
        with self.assertRaises(VerificationError):
            self.verify(manifest=manifest)

    def test_evidence_paths_cannot_escape_repository(self):
        evidence = copy.deepcopy(self.context["evidence"])
        evidence["tck"]["evidence_path"] = "../outside.json"
        with self.assertRaises(VerificationError):
            self.verify(evidence=evidence)

    def test_golden_corpus_is_hashed_from_local_bytes(self):
        self.context["golden_corpus"].write_bytes(b"modified corpus\n")
        with self.assertRaisesRegex(VerificationError, "Golden Corpus"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
