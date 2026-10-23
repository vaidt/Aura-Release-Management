# Integrity correction record — GUARD-RS-001

Initial capture commit d1cdbaf0e28c0924a466c496a1e460eca0c7cd9f used a defective SHA-256 implementation with omitted constants; its SHA-256 claims are invalid. This correction and the current capture revision supersede that attempt.

The corrected routine passed the SHA-256 abc known vector. Archive, log, member, and manifest hashes were recomputed. After this commit, the ZIP must be read back and verified by recomputing its hash, checking all ZIP member CRC32 values and lengths, recomputing member SHA-256 values, and confirming the external manifest binds the downloaded archive hash. The previous commit remains in history for transparency.

The log is full decoded connector-returned text, not the original compressed GitHub log HTTP bytes.
