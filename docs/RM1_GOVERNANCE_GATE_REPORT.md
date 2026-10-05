# AURA-RM-001 — RM-1 Governance Gate Report

**MODE:** READ-ONLY FORENSIC; FAIL-CLOSED  
**REPOSITORY:** `vaidt/Aura-Release-Management`  
**COMMIT:** `ef978ae01d1eb6de0a86a6c7f0f2de74006e06e4` (`copilot/rm-1-governance-recovery`)  
**DATE:** 2026-10-01  
**SCOPE:** Fresh review of the local RM-0 state and current governance artifacts needed to decide G0. No M0 admission or downstream work was performed.

## EVIDENCE

### Machine-readable governance artifact inventory

The entries below distinguish artifact claims from independently checked facts. Git blob IDs identify the file contents in the cited repository tree; they are not SHA-256 digests of raw file bytes.

```json
[
  {
    "artifact_id": "GENESIS_DECLARATION.txt",
    "issuer_claim": "Undersigned holder of the key; declares Original Creator and appoints Kamil Krasiński Chief Architect",
    "authority_claim": "Constitutional Genesis Authority; competence to ratify protocol changes and resolve P-008",
    "signature_present": true,
    "signature_verification": "PROVEN: ssh-keygen -Y verify succeeded in namespace aura-genesis for the key fingerprint SHA256:u9HaNYWZGQYvGET5ZaX2c/V56MzL0Xo7Ilg9M1pZRwU",
    "effective_date": "2026-09-24",
    "scope": "Genesis authority and appointment",
    "current_status": "Current file in aura-specification tree 5ba3567b79c7ac7ff37e0508219c12dab349ca2d",
    "ratification_status": "NOT STATED",
    "normative_effect": "Claims constitutive authority; signature verifies against the repository-declared key, but real-world identity/control is NOT INDEPENDENTLY VERIFIED",
    "supersession_status": "Text says it supersedes previous unverified historical claims",
    "conflicts": "Self-rooted identity/authority claim has no independent external identity attestation in the inspected evidence",
    "classification": "CONSTITUTIVE CLAIM; CRYPTOGRAPHIC SIGNATURE VERIFIED",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:GENESIS_DECLARATION.txt (blob 9c19e97270a4539ea7788a0553db2a800a573c44); signature blob 82f114a695c5b30094500452c8770cb4d6d572f5; allowed_signers blob fa4fa29ed870f350f38157e9a1e15fe9654a6f86"
  },
  {
    "artifact_id": "AURA-BIND-ROOT-v1.1",
    "issuer_claim": "Kamil Krasiński",
    "authority_claim": "Binds the named identity and GitHub accounts to the declared ssh-ed25519 root key",
    "signature_present": true,
    "signature_verification": "PROVEN: ssh-keygen -Y verify succeeded in namespace aura-governance for fingerprint SHA256:u9HaNYWZGQYvGET5ZaX2c/V56MzL0Xo7Ilg9M1pZRwU",
    "effective_date": "NOT STATED",
    "scope": "Root identity and key binding",
    "current_status": "RATIFIED (claim); current version v1.1",
    "ratification_status": "NOT STATED",
    "normative_effect": "Claims that decrees signed under aura-genesis and aura-governance carry authority; key-to-person identity is NOT INDEPENDENTLY VERIFIED",
    "supersession_status": "Explicitly supersedes AURA-BIND-ROOT-v1.0",
    "conflicts": "Authority depends on the repository's Genesis trust root",
    "classification": "SIGNED AUTHORITY-BINDING CLAIM",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:AUTHORITY_BINDING_RECORD_v1.1.md (blob f9dbbcc138a2e0d1bdb34aea2a238394a28ed2cd); signature blob eed7842fc54f5bfeaaafecca63f5dfbe24823b79"
  },
  {
    "artifact_id": "AURA-M1-CLOSURE-RECORD-v1.0",
    "issuer_claim": "Chief Architect, Kamil Krasiński, bound by AUTHORITY_BINDING_RECORD_v1.1.md",
    "authority_claim": "M1 governance closure and consolidation of Wave 1 decisions",
    "signature_present": true,
    "signature_verification": "PROVEN: ssh-keygen -Y verify succeeded in namespace aura-governance for fingerprint SHA256:u9HaNYWZGQYvGET5ZaX2c/V56MzL0Xo7Ilg9M1pZRwU",
    "effective_date": "NOT STATED",
    "scope": "M1 governance closure; records P-008, NOT_APPLICABLE, and Error Taxonomy as executed",
    "current_status": "RATIFIED (claim)",
    "ratification_status": "EXECUTED (claim)",
    "normative_effect": "Claims M1 closed and P-008 executed; the signature authenticates the file under the declared key but does not by itself establish procedural effectiveness",
    "supersession_status": "No explicit supersession clause for the pending P-008 record; the index describes that record as historical",
    "conflicts": "Records P-008 as EXECUTED while citing a P-008 record whose signed contents say PENDING_EXECUTION",
    "classification": "INTENDED CONSTITUTIVE CLOSURE; EFFECT CONFLICTED",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:AURA_M1_CLOSURE_RECORD_v1.0.md (blob 2a729379f8d306a1f371db26d0ec4577cf8701b6); signature blob e36a2ff03e39e3614c298dfb42c90964f058d65e"
  },
  {
    "artifact_id": "AURA-DEC-P008-v1.0",
    "issuer_claim": "Chief Architect, Kamil Krasiński",
    "authority_claim": "P-008 Verification Result Semantics",
    "signature_present": true,
    "signature_verification": "PROVEN: ssh-keygen -Y verify succeeded in namespace aura-governance for fingerprint SHA256:u9HaNYWZGQYvGET5ZaX2c/V56MzL0Xo7Ilg9M1pZRwU",
    "effective_date": "2026-09-24 (stated)",
    "scope": "P-008 result semantics, GV-V-001, GV-V-002, and P-008-scoped assertions",
    "current_status": "READY_FOR_EXECUTION",
    "ratification_status": "PENDING_EXECUTION",
    "normative_effect": "Claims EFFECTIVE normative effect while also recording PENDING_EXECUTION; effect is not unambiguous",
    "supersession_status": "Says it supersedes prior normative P-008 proposals; does not supersede prior execution evidence",
    "conflicts": "Directly conflicts with the M1 closure's EXECUTED state; the P-008 blob cited by M1 is this signed pending-state record",
    "classification": "CONFLICT",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:AURA_P008_RATIFICATION_RECORD_v1.0.md (blob 077a9b8a16dfdb7b700d7d1ec3e19f9c476c4f1e); signature blob 54059184b417e13183da97ef8db05d9b506cf8e6; cited commit bf83556139422f341d6b75f48b6b9a2412ef941a"
  },
  {
    "artifact_id": "GOVERNANCE_STATUS_INDEX.md",
    "issuer_claim": "Repository navigation/status index; no individual issuer or signature stated",
    "authority_claim": "Routes readers to records described as current records of reference",
    "signature_present": false,
    "signature_verification": "NOT APPLICABLE: no detached signature found in the inspected tree",
    "effective_date": "NOT STATED",
    "scope": "Navigation for governance, ratification, and closure records",
    "current_status": "Present in current specification tree",
    "ratification_status": "NOT STATED",
    "normative_effect": "Expressly an index; non-constitutive for resolving the P-008 execution state",
    "supersession_status": "Routes P-008 readers to the M1 closure; labels the standalone P-008 record historical",
    "conflicts": "Its reading rule cannot independently resolve the contradiction between signed constitutive records",
    "classification": "NON-CONSTITUTIVE",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:GOVERNANCE_STATUS_INDEX.md (blob e23bac1fc1cf99ea1efa32255f8f77fafce77135)"
  },
  {
    "artifact_id": "AURA_WAVE1_CONTRACT_CLOSURE_ERRATA_v1.1.md",
    "issuer_claim": "Technical reconciliation artifact; no cryptographic signer stated",
    "authority_claim": "Technical/schema reconciliation only",
    "signature_present": false,
    "signature_verification": "NOT APPLICABLE: no detached signature found in the inspected tree",
    "effective_date": "2026-09-24 (stated)",
    "scope": "Wave 1 CLI/result/error taxonomy reconciliation",
    "current_status": "TECHNICAL RECONCILIATION; PROPOSED / NOT RATIFIED",
    "ratification_status": "NOT RATIFIED",
    "normative_effect": "Explicitly NON-CONSTITUTIVE; says it does not establish authority continuity or M1 closure",
    "supersession_status": "Technical clarification only; no P-008 supersession",
    "conflicts": "Does not resolve P-008 execution",
    "classification": "NON-CONSTITUTIVE",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:AURA_WAVE1_CONTRACT_CLOSURE_ERRATA_v1.1.md (blob 512cecd04d27f79f2122583b55c15510fd805694)"
  },
  {
    "artifact_id": "DQ-006-CLOSURE-001",
    "issuer_claim": "Closure package citing APS-200, APS-300, ADR-CK003-DQ006, and CONF-003",
    "authority_claim": "DQ-006 canonicalization and evidence-closure status",
    "signature_present": false,
    "signature_verification": "NOT APPLICABLE: no detached signature found in the inspected tree",
    "effective_date": "Original closure 2026-08-19; reconciled 2026-08-20 (stated)",
    "scope": "Canonical serialization/hash-domain decision and cross-implementation evidence",
    "current_status": "OPEN; specification decision stated closed, conformance evidence partial",
    "ratification_status": "Ratification required per the package",
    "normative_effect": "Does not resolve P-008; reports unresolved cross-corpus precedence and open evidence/ratification residuals",
    "supersession_status": "Supersedes earlier DQ-006 closure records within its stated scope",
    "conflicts": "Not a P-008 execution record; provides no P-008 disposition",
    "classification": "NON-CONSTITUTIVE FOR P-008",
    "evidence_ref": "vaidt/aura-specification@5ba3567b79c7ac7ff37e0508219c12dab349ca2d:closures/DQ-006_CLOSURE_PACKAGE.md (blob b72b8b10a49def105e822a917d7e277bd8cc094c)"
  }
]
```

### Verification and local-state evidence

- `ssh-keygen -Y verify` independently accepted the detached signatures for `GENESIS_DECLARATION.txt` (`aura-genesis` namespace), `AUTHORITY_BINDING_RECORD_v1.1.md`, `AURA_M1_CLOSURE_RECORD_v1.0.md`, and `AURA_P008_RATIFICATION_RECORD_v1.0.md` (`aura-governance` namespace) against the key in `allowed_signers`. This proves signature validity under the repository-declared key, not real-world identity, exclusive key control, or the truth/effectiveness of the signed claims.
- The P-008 source commit `bf83556139422f341d6b75f48b6b9a2412ef941a` has commit message “Ratify P-008…”, but its P-008 file explicitly says `READY_FOR_EXECUTION` and `PENDING_EXECUTION`. The current M1 closure cites that same source artifact and says its ratification state is `EXECUTED`.
- `GOVERNANCE_STATUS_INDEX.md` calls M1 the current record of reference and P-008 historical. The index is unsigned and non-constitutive; its routing statement does not establish a constitutive transition from pending to executed.
- Current specification main commit: `5ba3567b79c7ac7ff37e0508219c12dab349ca2d`. Its tag listing was empty. The TCK tag listing was empty. The vNEXT tree has no M0 baseline tag; GitHub reports its default ref as `claude/aura-vnext-genesis-xerti8` at `bdec831c165b3a5465bc25f325ed801558cbf81a`.
- Local RM-0 state: clean branch `copilot/rm-1-governance-recovery`, HEAD `ef978ae01d1eb6de0a86a6c7f0f2de74006e06e4`, no local tags. `git show --show-signature HEAD` could not verify the GitHub merge signature because the public key was unavailable. The tracked tree has no M0 baseline, TCK admission record, Golden Corpus, governance gate report, or production-release evidence before this report.
- [`README.md`](../README.md) identifies RM-0 as a release-management consumer, not protocol authority or TCK, and says corpus contents and protocol semantics are not modified. [`schemas/AURA_RELEASE_MANIFEST_M0.schema.json`](../schemas/AURA_RELEASE_MANIFEST_M0.schema.json) binds the consumer schema to `refs/tags/M0-BASELINE-v1.0`; no such tag is present locally or in the inspected specification tag listing.

## FINDINGS

1. The Genesis, authority-binding, M1-closure, and P-008 detached signatures are **PROVEN valid under the key registered in the current repository's `allowed_signers` file**. The signatures do not independently prove identity, exclusive key control, or that every assertion in each signed record is procedurally effective.
2. P-008 execution state is a **CONFLICT**: the signed P-008 record says `PENDING_EXECUTION`, while the signed M1 closure says `EXECUTED` and cites that pending-state record. Neither a signature nor a current status index by itself supplies the missing constitutive explanation, effective date, or supersession mechanism.
3. The errata is expressly non-constitutive. DQ-006 concerns canonicalization evidence and remains `OPEN`; it does not determine P-008 execution.
4. RM-0 artifacts and implementation details provide no protocol authority. No M0 admission, TCK transfer, Golden Corpus closure/digest, M0 baseline, or tag was established or created.

## CLASSIFICATION

| G0 condition | Finding |
| --- | --- |
| Authority continuity | PROVEN within the repository-declared cryptographic trust root; real-world identity/control NOT INDEPENDENTLY VERIFIED |
| Signer authorization | PROVEN as a valid signature by the key registered in `allowed_signers`; external identity/control NOT INDEPENDENTLY VERIFIED |
| P-008 execution state unambiguous | CONFLICT |
| M0 ratification competence | NOT PROVEN for an M0 admission instrument; no explicit M0 admission act or procedure was found |
| G0 overall | BLOCKED |

## DECISION

**G0 — GOVERNANCE AUTHORITY: BLOCKED.** The required conjunction fails because the signed P-008 record's execution state conflicts with the signed M1 closure's execution claim, and M0-specific admission competence is not independently established. No M0 admission was attempted.

**M0 contract: NOT ADMITTED.** **TCK admission: NOT ADMITTED.** These are not negative judgments on the candidate technical contract; the downstream gates were not reached.

## BLOCKERS

- P-008 execution remains **CONFLICTED** between the signed P-008 record and the signed M1 closure that references it.
- The current evidence does not establish the constitutive mechanism/effective date by which the M1 closure changes the pending P-008 record to executed.
- M0-specific ratification/admission competence is **NOT PROVEN** by an explicit admission instrument or procedure in the inspected evidence.
- The root authority binds a key cryptographically, but real-world identity and exclusive key control are **NOT INDEPENDENTLY VERIFIED**.

## NEXT AUTHORIZED ACTION

Obtain a governance-authorized, constitutive instrument that explicitly resolves the P-008 pending-versus-executed conflict, identifies its effective date and scope, and establishes the competence and procedure for M0 admission. Independently verify its signature and authority chain, then repeat the read-only G0 review. Until then, do not admit the vNEXT candidate, transfer TCK vectors, close a Golden Corpus, create a baseline/tag, or authorize production release.

## MUTATIONS

- During the verification phase: none.
- This report adds only [`docs/RM1_GOVERNANCE_GATE_REPORT.md`](RM1_GOVERNANCE_GATE_REPORT.md).
- No protocol semantics, governance records, signatures, other repositories, vectors, TCK corpus, manifest, Golden Corpus, baseline, or tag were changed or created. No production deployment or release was performed.
