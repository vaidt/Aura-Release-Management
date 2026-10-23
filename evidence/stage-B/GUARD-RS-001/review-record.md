# AURA Stage B — GUARD-RS-001 evidence capture and review record

**Capture revision:** 2 — integrity correction  
**Status:** GOVERNANCE_REVIEW_PENDING  
**Classification:** non-normative technical evidence; not an acceptance or release decision

## Integrity correction

The initial capture commit d1cdbaf0e28c0924a466c496a1e460eca0c7cd9f contains invalid SHA-256 metadata because its digest routine omitted constants. Do not rely on hashes from that commit. This commit replaces the ZIP, manifests, sidecars and review record. The corrected SHA-256 implementation passed the standard abc known vector, and the current files are read back and re-verified. The initial commit remains in PR history for transparency and is superseded by this revision.

## Repository placement

Target: vaidt/Aura-Release-Management/evidence/stage-B/GUARD-RS-001/. Selected from the 17 repositories visible to the current vaidt account because it contains AURA release-control and an RM-1 governance-gate report. The absent vaidt/aura-governance name is not a blocker.

## Source identities

| Role | ID / SHA |
|---|---|
| Run | 39980864075 |
| Job | 120511056573 — GUARD-RS-001 concurrent HTTP stress + replay |
| PR head | dd08cf46677153295511b2691e3da0aea5d13c25 |
| PR base | e0ed7a8b381b725fe65bd86716894bfdf17d3a94 |
| Runner checkout / synthetic merge commit | dc777266a08ecae57f2aed3b37e7593e7a93001d |
| Merge parents | e0ed7a8b381b725fe65bd86716894bfdf17d3a94, dd08cf46677153295511b2691e3da0aea5d13c25 |

The PR head, base, and runner checkout commit are distinct. GitHub metadata confirms the synthetic merge commit has the PR head and base as parents.

## Corrected digests

- ZIP: GUARD-RS-001_JOB_LOG_CAPTURE_39980864075_120511056573.zip
- ZIP SHA-256: e556c6e9e99b2436e70beda77bc46dcc36cabef7d7d30157af7c96c8539b91df
- ZIP size: 45278 bytes
- External manifest SHA-256: c9c618e82e3b2e7015a41218de3cdffb53ffae8c5078e91194c2f0b900de1cca
- Full returned job-log text, UTF-8 SHA-256: efecbcdc8fe0fb92089bcb337e84bfcbe0ad0a8c02941cb7b2fe965c42ef34f0 (39182 bytes)
- Referenced D-3 artifact SHA-256: 024988956db987c883ce7071b6d2a2ac3de095f1e7a293ef3cddb8a2d1efb261 (artifact ID 12512947814; not embedded)

The ZIP and manifest sidecars carry these values. The payload manifest lists member hashes and byte lengths except itself; its digest is bound by the external manifest.

## Capture limitation

The integration returned decoded job-log text, not the original compressed GitHub log archive. The hash binds the UTF-8 serialization including BOM, not the native compressed bytes. The D-3 artifact hash was verified separately against downloaded bytes; it is referenced, not embedded.

## Technical result

- 17/17 Check Runs for the PR head: success.
- 500/500 HTTP requests succeeded; at most 200 workers; 500 JSONL entries; unique and continuous response sequences.
- Replay: status ok, 500 entries, 10 segments; lineage and segment verification both true.

## Open findings

- F-02 OPEN. Combined status has no entries; branch protection returns 403 to the integration. Authorized UI/admin verification required.
- F-04 OPEN / reassessment required. D-3 output says vaidt/aura-guard-v1.3; the D-3 fixture retains AuraIDToken/aura-guard-v1.3. Preserve historical bytes; resolve by explicit mapping or an approved new fixture and rerun.

PR #13 remains Draft; ci_execution_wired = false; AURA release remains NO-GO. No merge authorization is implied.

Source URLs:
https://github.com/vaidt/aura-guard-v1.3/actions/runs/39980864075
https://github.com/vaidt/aura-guard-v1.3/actions/runs/39980864075/job/120511056573
https://github.com/vaidt/aura-guard-v1.3/pull/13
https://api.github.com/repos/vaidt/aura-guard-v1.3/actions/artifacts/12512947814
