# ADR-AURA-NSM-001 — Trust and Verification for Namespace Migration

**Status:** PROPOSED — NOT RATIFIED  
**Version:** 1.0  
**Date:** 2026-10-23  
**Decision scope:** AURA Namespace Migration Record, F-04 verification, and the future CI verification contract  
**Implementation status:** DESIGN ONLY — no verifier, trust root, signing role, or CI gate is established by this ADR  
**Authority:** No authority or ratification competence is inferred from repository ownership, branch creation, commit authorship, or PR participation.

## 1. Context

F-04 records a namespace mismatch between the current repository identity **vaidt/aura-guard-v1.3** and a historical fixture value that identifies **AuraIDToken/aura-guard-v1.3**. The stated project history treats AuraIDToken as a historical identifier and vaidt as the current namespace. That claim must be represented as a scoped, evidence-backed mapping; it must not silently rewrite historical records or imply that account ownership, civil identity, legal continuity, or protocol authority has been proven.

The required control has two distinct decisions:

1. **Cryptographic verification:** Are the exact payload bytes, signatures, identity claims, digests, and transparency evidence valid under a trust policy obtained independently of the candidate change?
2. **Governance authorization:** Does an independently verifiable, competent authority have the power to ratify this exact mapping, and is the required approval threshold met?

A successful answer to the first question does not answer the second.

This repository is a release-management consumer and evidence location, not an authority source for AURA Protocol semantics. This ADR does not resolve unrelated governance conflicts, F-02 branch protection, or protocol authority continuity.

## 2. Decision

Adopt the following architecture as the proposed design for future implementation:

- **TUF** distributes and versions the verifier's trusted metadata and delegates narrowly scoped signing/authorization roles.
- **Sigstore** verifies keyless CI attestations by checking the expected OIDC issuer, exact workflow identity, certificate chain, and required transparency evidence.
- **DSSE + in-toto Statement v1** binds a typed attestation to immutable subject digests and authenticates the exact payload.
- **RFC 8785 JSON Canonicalization Scheme (JCS)** provides deterministic serialization for the migration Statement payload and any JSON object whose digest is defined over canonical JSON.
- **A separate ratification role and threshold** decide whether the migration is authorized. CI identity is not ratification authority by default.

This decision is a proposed technical design only. It does not create a TUF root, authorize a key, define a ratification threshold, grant an individual competence, or mark F-04 resolved.

## 3. Trust boundaries and responsibilities

### 3.1 TUF — policy distribution and key lifecycle

The verifier MUST bootstrap its initial trusted TUF root through a channel independent of the candidate pull request. The initial root key set and threshold MUST be provisioned or pinned out-of-band by an approved process. A candidate branch MUST NOT be able to replace the verifier's root, trust policy, trusted role list, or minimum accepted metadata version used to validate that same candidate.

TUF metadata MUST be verified for signatures, role thresholds, version continuity, and expiry. Clients MUST refuse metadata rollback and expired metadata. Root rotation MUST follow the selected, explicitly pinned TUF specification and its root-update procedure. Root private keys SHOULD remain offline and be separated from routine CI credentials.

Distinct delegated roles MUST be defined for at least:
- trust-policy publication and root/key rotation;
- routine CI attestation identity;
- namespace migration ratification.

A key authorized for routine CI signing MUST NOT thereby gain namespace-migration ratification competence. TUF role delegation is a technical trust mechanism; the legal or constitutional competence to establish those roles must be proved independently before the policy becomes authoritative.

Because ephemeral CI runners may not retain trusted metadata state between runs, rollback protection must be defined explicitly. The implementation MUST use a trusted persistent checkpoint or an independently delivered minimum metadata version/digest, or another documented mechanism providing equivalent protection. A value taken only from the candidate branch is insufficient.

The TUF specification version, client implementation, supported algorithms, metadata schema, and trust-root distribution channel MUST be pinned in the eventual implementation change. This ADR does not choose or publish production key material.

### 3.2 Sigstore — CI workload identity

Sigstore may authenticate the provenance of an automated CI attestation. The verifier MUST check the exact OIDC issuer and certificate identity, verify the certificate chain under the configured Sigstore trust root, and verify required transparency-log inclusion/checkpoint evidence according to the pinned Sigstore bundle and verifier format.

For GitHub Actions, the issuer expected for the approved workload is **https://token.actions.githubusercontent.com**. The accepted certificate identity MUST be an exact, reviewable workflow identity for the intended repository, workflow path, and protected ref. The exact identity string MUST be measured from a controlled reference run and recorded in trusted policy; it MUST NOT be guessed, broadly wildcarded, or copied from untrusted pull-request metadata.

Only the designated protected workflow may produce attestations accepted as official CI evidence. A pull-request-controlled workflow, a fork, a feature branch, an arbitrary workflow in the repository, or an identity mismatch MUST NOT be accepted as a ratification signer. CI attestations establish the identity of the signing workload under the configured identity provider; they do not establish human identity or governance authority.

The exact issuer/identity policy and trust bundle MUST be supplied by the trusted control plane and MUST NOT be replaceable by the change being verified.

### 3.3 DSSE and in-toto — payload integrity and binding

The signed attestation MUST use an in-toto Statement v1 envelope in DSSE. Before implementation, the project MUST allocate and ratify a stable predicateType URI and publish the closed schema for its predicate. This ADR does not reserve a production URI.

The Statement subject list MUST identify the immutable artifacts being discussed through SHA-256 digests of their exact, preserved bytes. At minimum, the evidence must identify the relevant historical fixture. If a revised fixture is required, it must identify the new fixture separately and link it to the old one by an explicit version/supersession relationship. Repository paths and branch names alone are not immutable subjects.

The predicate MUST carry the namespace mapping record, the restricted scope of the alias, the record ID/version, the evidence index, and explicit limitations. At minimum, the limitations MUST state that the mapping alone:
- does not prove that two GitHub accounts are controlled by the same natural person;
- does not prove legal identity, ownership, or legal succession;
- does not establish continuity of protocol-custodian or ratification authority;
- does not authorize any other repository or namespace mapping.

The migration Statement payload MUST be serialized using RFC 8785 JCS before signing. The DSSE envelope's payload type and the exact payload bytes MUST be verified, and the DSSE signature MUST be checked using DSSE's pre-authentication encoding (PAE) semantics. The implementation MUST NOT substitute a hash of a re-formatted payload or verify only a detached signature without validating the declared payload type and bytes.

The SHA-256 value recorded for canonical Statement JSON is the digest of the exact JCS byte sequence used as the DSSE payload. Evidence-file digests that are defined over raw file bytes MUST instead hash those raw bytes; the record must label the digest domain unambiguously. A raw-byte digest and a canonical-JSON digest MUST NOT be conflated.

### 3.4 Separate ratification attestation

A proposed migration Statement MUST remain immutable with status **PROPOSED**. Ratification MUST be represented by a separate signed decision/attestation whose subject binds the exact SHA-256 digest of that proposal. A later approval MUST NOT rewrite the earlier proposed payload from PROPOSED to RATIFIED.

The ratification decision MUST include:
- the proposal record ID/version and exact digest;
- the exact source and target owner/repository identifiers and mapping scope;
- the disposition, decision timestamp, and effective date if approved;
- the ratification role and the independently established authority evidence;
- signer key IDs, signature-validation evidence, and threshold result;
- the historical fixture digest and any revised fixture digest, where applicable;
- explicit scope and limitations.

The required role, authorized key set, approval threshold, and competence evidence MUST be established by a separately authorized governance process before the gate can accept a ratification. This ADR deliberately does not invent a 2-of-3 threshold or nominate signers. Missing or ambiguous authority evidence means authorization is not granted.

## 4. Required record and evidence package

The future record schema MUST require, at minimum:

| Field group | Required contents |
|---|---|
| Identity | Record type, schema version, stable record ID, status, creation time |
| Namespace relation | Platform, relation type, exact source owner/repository, exact target owner/repository, explicit scope |
| Limitations | Non-inheritance of identity, legal status, ownership, and governance authority |
| Historical evidence | Immutable repository/commit/path identifiers where available; SHA-256 over exact historical fixture bytes; provenance references |
| Fixture policy | Preserve historical bytes; never overwrite; new revision has a new version and digest; link the new revision to the old record and migration decision |
| Canonicalization | RFC 8785 JCS profile, payload type, digest algorithm, digest domain |
| Attestation | in-toto Statement version, predicate type, DSSE envelope/bundle reference, signer identity or key ID |
| Ratification reference | Separate decision record and its digest; empty while unratified |
| Audit | Tool/version information, verification result, evidence timestamp, and reviewer disposition |

Unknown or contradictory fields relevant to authorization MUST cause rejection. Any extensions must be explicitly handled by the schema and policy; the verifier must not infer authorization from an unknown field.

## 5. CI gate contract

Implementation SHOULD expose at least two non-interchangeable results:

- **AURA_NAMESPACE_ATTESTATION_VERIFY:** verifies trusted policy retrieval, TUF metadata, schema, canonicalization, subject digests, DSSE/PAE signature, Sigstore identity and required transparency evidence.
- **AURA_NAMESPACE_MIGRATION_AUTHORIZATION:** verifies that a separate ratification attestation binds the exact proposal digest and satisfies the approved role, authority evidence, scope, effective date, and threshold.

A technical PASS MUST NOT be translated into a governance PASS. The gate MUST return a machine-readable result that distinguishes verification failure, insufficient authorization, missing evidence, and valid-but-unratified proposal.

The verifier MUST fail closed for at least these cases:
- untrusted or candidate-supplied root/trust policy; TUF signature/threshold failure; expired metadata; rollback or stale trusted checkpoint;
- unknown or disallowed OIDC issuer, workflow identity, ref, certificate chain, or signer key;
- missing, invalid, or policy-required-but-unverifiable transparency evidence;
- DSSE payload-type mismatch, invalid PAE signature, malformed envelope, non-canonical payload when JCS is required, schema failure, duplicate JSON property names, or digest mismatch;
- historical bytes changed, absent historical digest, unexpected subject, mismatched repository owner/name, or unapproved fixture revision;
- missing ratification, wrong role, insufficient threshold, expired/revoked key, missing competence evidence, or a ratification that refers to a different proposal digest;
- an attempt by the candidate PR to change the policy or trust root used to authorize that same change.

Negative tests MUST cover each case above. Cross-implementation JCS/digest/DSSE verification SHOULD be tested independently before the gate is relied upon. All verifier and signing-tool versions, policy versions, schemas, and test vectors MUST be pinned in the implementation PR. The gate MUST expose stable result codes and preserve diagnostic evidence without logging private keys or credentials.

## 6. F-04 closure criteria

F-04 may be closed only when the following conjunction is evidenced and independently reviewed:

1. A schema-valid namespace migration Statement identifies the exact historical and current repository identities and explicitly limits the scope of the alias.
2. Historical fixture bytes and digest have been preserved and independently verified. No old fixture is overwritten, reserialized, or silently normalized.
3. The proposal payload is RFC 8785 JCS canonicalized, its digest domain is explicit, and its DSSE/in-toto attestation passes independent verification against trust policy obtained outside the PR.
4. The identity mapping is supported by primary evidence sufficient for the claimed repository-alias relation. Repository-name similarity or the presence of a GitHub account alone is insufficient.
5. A separate valid ratification attestation binds the exact proposal digest and is signed by the role and threshold established by an independently evidenced governance instrument. The ratifier's competence is not inferred from a valid signature alone.
6. The verifier determines whether the existing fixture is intentionally historical or semantically must be updated. If an update is required, publish a new fixture revision with a unique digest, explicit supersession/migration reference, and passing regression/conformance tests; preserve the old fixture and its digest.
7. Positive and negative gate tests pass, verification output is archived, and an independent review confirms the exact artifacts and digests.
8. The F-04 disposition is recorded through the authorized governance workflow. The ADR, a green CI run, an open PR, or a repository commit alone does not close the blocker.

If the valid mapping is ratified but the existing fixture is intentionally historical, F-04 may be closed only if the authoritative specification explicitly declares the alias-equivalence rule and the verifier checks that rule in the stated scope. The verifier MUST NOT perform a global search-and-replace or general identity inference.

## 7. Relationship to existing blockers and release state

This ADR does not close F-02. Branch-protection enforcement for all 17 required Check Runs must be verified separately by an authorized administrator using repository rules/branch-protection configuration and the actual required status-check contexts. A list of successful checks in one run is not proof that all are required by branch protection.

This ADR does not alter, supersede, or recompute any historical evidence, fixture, manifest, signature, sidecar, CI log capture, or digest. Any necessary fixture correction is a new immutable revision and separate change.

Until independent authority is proven and the ratification procedure is established:
- ADR status remains **PROPOSED — NOT RATIFIED**;
- F-04 remains OPEN;
- GOVERNANCE_REVIEW_PENDING remains unchanged;
- PR #5 and PR #13 remain Draft unless separately directed;
- ci_execution_wired remains false;
- AURA release status remains **NO-GO**.

This ADR itself is not a ratification instrument and grants no authority.

## 8. Implementation and review sequence

1. Governance review: establish the competent approving role, authority evidence, role separation, and threshold. No production trust root is created before this step.
2. Specification review: approve the closed migration predicate schema, stable predicate type URI, digest domains, status model, and evidence index.
3. Trust bootstrap: define out-of-band TUF root provisioning, rotation/recovery procedures, metadata freshness, and rollback checkpoints.
4. Verifier implementation: implement independent JCS, in-toto/DSSE, Sigstore, TUF, schema, and authorization checks using pinned dependencies.
5. Test and adversarial review: add known-answer vectors, cross-implementation tests, and fail-closed negative cases.
6. Controlled trial: verify an unratified proposal and prove that cryptographic verification can succeed while authorization correctly remains blocked.
7. Ratification and F-04 disposition: accept only a separately signed decision that satisfies the approved policy; review the final evidence package and fixture-version decision.
8. Close F-04 only through the authorized governance process. Do not promote release state as a side effect of this ADR or CI success.

## 9. Consequences

**Benefits:** clear separation between workload identity, cryptographic integrity, and governance authority; immutable historical evidence; explicit rotation and rollback controls; independently testable, fail-closed gates.

**Costs:** additional trust-policy lifecycle, offline/root-key custody, explicit metadata freshness handling for ephemeral CI, version-pinned verification tools, cross-implementation tests, and a separate ratification workflow. The architecture is not operational until all these controls are implemented and independently reviewed.

**Residual risks:** compromise of a sufficient trust-root or ratification-key threshold, incorrect primary evidence, policy implementation bugs, and an invalid initial governance authority chain. Cryptographic verification reduces specific substitution and forgery risks; it cannot independently prove real-world identity, legal continuity, or procedural legitimacy.

## 10. Normative and technical references

- RFC 8785, JSON Canonicalization Scheme: https://www.rfc-editor.org/rfc/rfc8785.html
- The Update Framework specification and metadata roles: https://theupdateframework.github.io/specification/
- Sigstore verification documentation: https://docs.sigstore.dev/cosign/verifying/verify/
- Sigstore OIDC identity verification guide: https://docs.sigstore.dev/quickstart/verification-cheat-sheet/
- in-toto Attestation Framework — Statement v1: https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md
- DSSE envelope and PAE definitions: https://github.com/secure-systems-lab/dsse

The implementation MUST pin the specific specification editions and tool versions used for conformance; these references identify the governing documents, not a claim that any implementation already exists.
