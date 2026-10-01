# Aura Release Management — RM-0

RM-0 is a local release-control pilot. It is a release orchestrator and
provenance/manifest verifier, not an Aura Protocol implementation, protocol
authority, policy engine, TCK, or product implementation. It does not define or
change protocol semantics.

## Architecture and trust boundaries

`release/manifest.py` validates and prepares manifests against the closed
JSON Schema in `schemas/`. `release/canonicalize.py` defines the byte encoding
used for payload signatures and derived digests. `release/provenance.py`
checks declared repository identities and commit objects against the
control-plane policy, locally available Git repositories, and evidence files
read from the declared commits. `release/state_machine.py` enforces the
one-way release lifecycle. `release/signing.py` implements Ed25519 signatures,
and `release/verify.py` combines the checks without promoting or rebuilding
artifacts.

The manifest and evidence records are untrusted claims. The trusted repository
policy is a control-plane input in `policy/trusted_repositories.json`; trusted
public keys are supplied separately to the verifier. Provenance verification
is deliberately offline: repository paths are explicit CLI inputs, Git is
invoked with fixed argument vectors (never a manifest-provided command), and
no URL is fetched. All four local repositories must be available for
VERIFIED-or-later states. The verifier checks the exact specification tag and
commit, commit existence in every repository, a clean vNEXT worktree, the
vNEXT artifact attestation committed at its declared SHA, and TCK/assurance
evidence committed at their declared SHAs.
For each local clone it also checks that the configured `origin` URL matches
the trusted GitHub repository identity. That local URL check is a consistency
check, not independent cryptographic proof of who supplied the clone; trust
still rests on the configured control-plane inputs and immutable object IDs.

The RM-0 evidence contract is intentionally narrow. The vNEXT commit must
contain the JSON file named by `implementation.artifact_attestation_path`:

```json
{
  "artifact_repository": "<allowlisted OCI repository>",
  "artifact_digest": "sha256:<64 lowercase hex characters>"
}
```

The manifest's `provenance.implementation.evidence_sha256` is the SHA-256 of
that committed file's raw bytes. Its presence in the declared vNEXT commit
tree binds the artifact attestation to that immutable commit without requiring
an impossible self-referential commit SHA inside the commit itself.

The TCK commit must contain the closed JSON object named by `tck.evidence_path`,
with exactly the `matrix_version`, `artifact_digest`, and
`golden_corpus_sha256` string fields.
Its raw-file SHA-256 is the signed `provenance.tck.evidence_sha256`. The
verifier also requires an explicit local `--golden-corpus` file and hashes its
raw bytes in streaming chunks; that derived SHA-256 must match both
`release_inputs.golden_corpus_sha256` and the TCK evidence. The
assurance file named by `assurance.evidence_path` is opaque; its raw-file
SHA-256 is the signed `provenance.assurance.evidence_sha256`. Evidence paths
must be relative paths inside their respective Git trees. RM-0 does not infer
semantics for TCK matrices or assurance content.

## Manifest lifecycle

The only forward transitions are:

```text
DRAFT → RELEASE_CANDIDATE → VERIFIED → SIGNED → RELEASE_PROMOTED
              any non-promoted state → REJECTED
```

No transition may be skipped or reversed. Candidate manifests require all
candidate inputs. VERIFIED requires every local provenance and digest gate.
SIGNED requires a valid Ed25519 signature over the canonical payload.
RELEASE_PROMOTED additionally requires a separate local promotion record
whose artifact digest and registry reference match the exact signed artifact.
The manifest status field alone never proves a transition or promotion.
REJECTED is terminal; RM-0 has no manual override.

The artifact digest tested by the TCK must exactly equal the artifact digest
in the manifest. RM-0 does not rebuild artifacts or publish/promote them.

## Canonicalization and digests

`AURA-RM-CANON/1` is a deliberately restricted deterministic JSON profile,
**not** an RFC 8785 implementation. It encodes UTF-8 without a BOM, emits no
insignificant whitespace, sorts object keys by Unicode code-point order, uses
fixed JSON separators and `ensure_ascii=False`, and uses deterministic JSON
string escaping. Duplicate object keys, invalid Unicode scalar strings,
non-finite values, floating-point values, and integers outside the exact
IEEE-754 safe-integer range are rejected. Restricting numbers to safe integers
avoids claiming cross-runtime float serialization compatibility.

`payload_canonical_sha256` is SHA-256 of the `payload` encoded with this
profile. `release_inputs_digest` is SHA-256 of the `release_inputs` object
encoded with the same profile. It is a deterministic aggregate digest, **not a
Merkle root**. The verifier independently re-derives both digests.

Git identities must be exactly 40 lowercase hexadecimal characters;
SHA-256 values exactly 64 lowercase hexadecimal characters; OCI digests must
be `sha256:` followed by exactly 64 lowercase hexadecimal characters.
Abbreviated SHAs, branch names, tags in place of commit SHAs, and other digest
algorithms are refused.

## Signing and security

The signing API accepts raw Ed25519 private-key bytes from its caller. The
signing CLI reads a base64-encoded key only from
`AURA_RM_ED25519_PRIVATE_KEY_B64`; it never logs or stores that key. Production
private keys must not be committed, and CI does not acquire signing secrets.
Verification keys are supplied through
`AURA_RM_TRUSTED_PUBLIC_KEYS_JSON` as a key-id-to-base64-public-key mapping.
The trust policy has no artifact repository allowlisted by default; a
control-plane administrator must explicitly configure one before provenance
verification can pass.

Malformed data, missing evidence, policy mismatches, invalid signatures,
unknown fields, failed gates, and unavailable local Git objects fail closed.
The CLIs emit JSON results and use exit code 1 for release/verification
failure, 64 for usage errors, and 65 when the requested operation cannot be
executed due to missing or unavailable control-plane inputs.

## RM-0 limitations and deferred work

RM-0 verifies local provenance evidence and release-manifest integrity. It
does **not** establish regulatory compliance, full Aura Protocol conformance,
production readiness, cloud immutability, WORM guarantees, production
registry promotion, or authority beyond referenced governance evidence.
Repository ownership is not authority. No historical Aura repository is
treated as an authority source, and RM-0 makes no historical compatibility
claim.

S3, GCP Storage, Azure Blob, Object Lock/WORM, cloud registry integration,
OCI registry promotion, deployment, Kubernetes, systemd, cross-repository
writes, external authority resolution, production signing, and a true Merkle
tree are **DEFERRED**. Golden corpus and APS contents and protocol semantics
are not modified. RM-0 is not a production release or deployment system.

## Local use

Python 3.12.8 is supported. Install the exact locked dependency set and run
the tests:

```sh
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python -m pytest
python -m ruff check .
```

Prepare/validate a manifest (derived input digest is refreshed when inputs are
complete):

```sh
python -m release.manifest examples/AURA_RELEASE_MANIFEST_M0.example.json
```

Verify a DRAFT without asserting provenance:

```sh
python -m release.verify examples/AURA_RELEASE_MANIFEST_M0.example.json
```

For VERIFIED-or-later manifests, pass the separate evidence JSON, the local
Golden Corpus file, and all four local repository paths with repeated
`--repository role=path` options.
SIGNED-or-later verification also needs the trusted-public-key environment
variable. RELEASE_PROMOTED additionally needs a separate
`--promotion-record` JSON file. `release.provenance` and `release.signing`
provide corresponding standalone commands; signing a VERIFIED manifest also
requires provenance evidence and the private-key environment variable.

No production deployment, cloud operation, external repository mutation,
production promotion, or claim of `RELEASE_PROMOTED` or `AURA CONFORMANT` is
made by this pilot.
