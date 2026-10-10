# Known Limitations and Epistemic Boundaries
## Release v1.0: Intelligence & Legal Authority Subsystems

### Epistemic Status & Mandatory Naming Distinction
Two distinct classification labels govern this platform and must never be conflated:
1. **Software Qualification (`QUALIFIED`)**:
   Certifies that the software implementation has rigorously passed its declared mechanical, host, cross-domain, scale, and domain regression test suites (including 100% agreement across 288 direct oracle cells, 72 action queries, 48 actor queries, 56 AQ governance obligations, 18 host checks, and 30 synthetic pilot cases).
2. **Legal Correctness (`REVIEWED WITHIN DECLARED LEGAL PACK`)**:
   Reserved strictly for legal packs that have undergone authenticated, independent legal review by certified legal counsel in the governing jurisdiction. The current statutory pack provides deterministic integrity binding and schema validation over source text; it does not substitute for authenticated legal review.

---

### 1. Synthetic Profile Agreement vs. Real-World Legal Correctness
The qualification and verification suites demonstrate mechanical parity, algorithmic correctness, and exact schema compliance under synthetic test cases and scoped statutory packs. **Synthetic profile agreement does not constitute general legal correctness or definitive statutory interpretation.** Real-world operational deployment must be accompanied by certified statutory rule packs formally reviewed and signed off by qualified legal counsel in the governing jurisdiction.

### 2. Deterministic Integrity Binding vs. PKI / Asymmetric Signatures
The `ReviewerRecord.signature` attribute represents a **deterministic cryptographic integrity digest** (SHA-256 calculated over `reviewer_id`, `citation`, `source_text_sha256`, and `rules_digest`). It establishes structural integrity and tamper detection for self-contained legal packs (Invariant AQ20). It **does not** constitute an asymmetric public-key signature (e.g., Ed25519 / RSA X.509 PKI) and does not establish external cryptographic identity verification of the human reviewer.

### 3. Non-Collapsing "No Law by Silence" Principle
Under Invariant AQ07 and classical administrative law principles, the absence of an explicit statutory rule governing a particular operation does **not** imply permission, nor does it imply prohibition. Where statutory packs provide no decisive rule:
- Direct assessment produces `UNRESOLVED` (`no_applicable_law`).
- Platform certification produces `UNRESOLVED` status.
- The platform strictly bars collapsing unaddressed actions into default grants or universal bans.

### 4. Analytical Course Discovery Does Not Grant Operational Admission
The `CoursePlanner` subsystem identifies hypothetical, multi-step courses of action across the organizational network to uncover unconventional but legally admissible paths. **Analytical course exploration is strictly decoupled from operational admission.**
- Analytical candidates are labeled `CandidateCourse` with prospective admissibility scores.
- An analytical candidate **never** confers operational execution rights.
- Operational execution requires explicit formal evaluation through the authoritative `AuthorityEvaluator.certify_work()` pipeline under reviewed rule packs.

### 5. Scoped Jurisdictional Coverage
The authority evaluation engine operates strictly as a closed-world deductive classifier over the rules explicitly loaded in the evaluation context:
- Unmodeled common-law doctrines, uncodified judicial precedents, and balancing tests not captured in the rule condition language cannot be deduced.
- Conflicting multi-jurisdictional rules produce `CONFLICTING` / `UNRESOLVED` dispositions requiring human legal intervention.

### 6. Epistemic Uncertainty Propagation
When evidence for condition facts is incomplete, unverified, or contested:
- The condition verifier yields `FACT_UNRESOLVED` or `FACT_CONFLICTING`.
- Essential conditions that cannot be verified prevent `CERTIFIED` admission, holding the certificate in `UNRESOLVED` or `OBSTRUCTED`.
- The system will never guess, impute, or probabilistically assume compliance for missing evidence.
