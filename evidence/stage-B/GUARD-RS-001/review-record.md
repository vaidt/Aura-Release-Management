# AURA Stage B — GUARD-RS-001 evidence capture and review record

**Status:** `GOVERNANCE_REVIEW_PENDING`  
**Classification:** non-normative technical evidence capture; not an approval or release decision  
**Prepared:** 2026-10-23T17:49:35.819Z

## Repository placement

This evidence change targets `vaidt/Aura-Release-Management` under `evidence/stage-B/GUARD-RS-001/`. Among the 17 repositories visible to the connected `vaidt` account, this is the strongest match for a non-normative release-review evidence package: it already contains the AURA-RM release-control documentation and an RM-1 Governance Gate Report. The named `vaidt/aura-governance` repository does not exist in the visible list; no further work is blocked on that absent name.

## Immutable identities

| Role | Full SHA / ID |
|---|---|
| Workflow run | `39980864075` |
| Job | `120511056573` — `GUARD-RS-001 concurrent HTTP stress + replay` |
| PR head | `dd08cf46677153295511b2691e3da0aea5d13c25` |
| PR base | `e0ed7a8b381b725fe65bd86716894bfdf17d3a94` |
| Runner checkout / synthetic merge commit | `dc777266a08ecae57f2aed3b37e7593e7a93001d` |
| Merge commit parents | `e0ed7a8b381b725fe65bd86716894bfdf17d3a94`, `dd08cf46677153295511b2691e3da0aea5d13c25` |

GitHub metadata shows the synthetic merge commit has the PR head and base commits as parents. The run's `head_sha` identifies the PR head; the runner log says it checked out the synthetic merge commit. These identifiers are not interchangeable.

## Captured archive

- ZIP: `GUARD-RS-001_JOB_LOG_CAPTURE_39980864075_120511056573.zip`
- ZIP SHA-256: `f09b6cade51f2be776cbc529b67b2b0d140865f222f6161bd4dbcbc29b53a391`
- ZIP byte length: `47104`
- External manifest SHA-256: `ee20adad4244a70c7192e9ecae2da75fcbd31040c97eee4f2db35c51a268208e`
- Full connector-returned job-log text, UTF-8 serialization SHA-256: `d16f3eb589d9aea49263851db709a6aabf235898977226bef5202df4845f05d4` (39182 bytes)
- Referenced D-3 artifact SHA-256: `024988956db987c883ce7071b6d2a2ac3de095f1e7a293ef3cddb8a2d1efb261` (artifact ID `12512947814`; not duplicated inside this ZIP)

The package includes a member manifest with SHA-256 and byte lengths for the capture record, identity-lineage note, README, and log; it excludes itself by design. The external manifest binds the ZIP's actual hash.

## Capture limitation

The GitHub integration returned decoded job-log text, which is preserved fully and encoded as UTF-8 (including the returned BOM). It did not expose the original compressed HTTP log archive bytes. Accordingly, the recorded log hash binds this exact captured UTF-8 serialization and must not be described as a byte-for-byte hash of GitHub's native compressed log file. The D-3 ZIP's hash was independently checked against downloaded bytes, but that ZIP is referenced rather than embedded because a manual Base64 transfer failed validation and was rejected.

## Technical result

- Run and job identity/status verified against GitHub metadata.
- 17/17 Check Runs for the PR head reported `success`.
- GUARD-RS-001: 500 requests sent and 500 succeeded; maximum 200 workers; 500 JSONL entries; unique and contiguous response sequences.
- Replay: `status=ok`, 500 entries, 10 segments; lineage and segment validation both `true`.
- Head chain hash: `59e14c99968caa32ee5bd5a8e934c15a301ab0006b81170ce78983978c488ccd`.
- Head segment-chain hash: `90b10cfc91d860b534b9ba0f4ddb4b7cc94d2d309d59b5107d9496915ffecb15`.

## Outstanding issues

- **F-02 OPEN.** 17 Check Runs are successful, but the classic combined status had no status entries; the branch-protection endpoint returns HTTP 403 to the integration. This is not proof that protection is absent. Authorized UI/admin verification is still needed.
- **F-04 OPEN / REASSESSMENT REQUIRED.** D-3 output field `repository` is `vaidt/aura-guard-v1.3`, while the fixture's `target.repository` is `AuraIDToken/aura-guard-v1.3`. Project-owner context identifies the latter as historical. Do not silently alter prior evidence: add an explicit legacy-to-current mapping or approve a new fixture revision and rerun the appropriate verification.

## Governance boundary

This archive is technical evidence, not an acceptance decision. PR #13 stays Draft; `ci_execution_wired = false`; release status remains `NO-GO`. Store this evidence on the proposed branch and keep the accompanying PR in Draft pending formal review.

## Source links

- [Workflow run](https://github.com/vaidt/aura-guard-v1.3/actions/runs/39980864075)
- [GUARD-RS-001 job](https://github.com/vaidt/aura-guard-v1.3/actions/runs/39980864075/job/120511056573)
- [PR #13](https://github.com/vaidt/aura-guard-v1.3/pull/13)
- [D-3 artifact metadata](https://api.github.com/repos/vaidt/aura-guard-v1.3/actions/artifacts/12512947814)
