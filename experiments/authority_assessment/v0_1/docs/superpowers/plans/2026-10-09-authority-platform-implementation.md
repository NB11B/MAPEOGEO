# MAPEOGEO Authority Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task by task. Checkboxes track implementation progress.

**Goal:** Add explainable actor-to-actor legal-scope assessment, bounded option queries and authority-gap analysis to MAPEOGEO, with a separate UoW admission boundary.

**Architecture:** Create an additive intel_authority package under experiments/authority_assessment/v0_1. Keep the frozen intelligence reference as a pinned dependency. Use explicit host projection and a separate UoW bridge; publish analytical results through a local append-only revision store.

**Tech Stack:** Python 3.12, standard library, unittest, dataclasses, decimal, hashlib, json and sqlite3. No language-model or external service dependency in the deterministic qualification path.

**Spec:** ../specs/2026-10-09-authority-model-design.md

**Author and copyright:** Nathanael J. Bocker. © 2026 Nathanael J. Bocker. All Rights Reserved.

## Global Constraints

Each UoW has internal time; no shared clocks.

The 24 QF obligations are included in the 152 reference unittest methods.

The original five grammar disagreements remain preserved.

LegalAssessment never creates a grant or admits actual work.

A source claim, scenario or model output cannot establish actual authority.

The v0.3 reference and existing historical evidence are immutable.

The initial host adapter is read-only; external execution is excluded.

Numerical predicates use canonical finite decimal strings and declared units.

All positive results require their complete decisive trace and adequate declared scope.

Any additional supported semantics require a versioned contract and qualification change.

## Review Focus

1. Unknown or conflicting evidence in a possible exception must not create unconditional support. Owned by T03 and T04; AQ49 and AQ50.
2. A private liberty, a public power and an actual operational grant must remain distinct. Owned by T04 and T07; AQ06, AQ11 and AQ51.
3. A shared allowance must not be double-counted across separate UoWs. Owned by T06 and T07; AQ35 and AQ53.
4. A contingent plan cannot choose a branch using information unavailable at the deciding frontier. Owned by T06; AQ54.
5. A source amendment, interrupted publication or new relevant source must not corrupt historical replay or preserve an incompatible positive cache entry. Owned by T08; AQ21, AQ30, AQ43 and AQ55.

## 1 Delivery organization

Use eleven implementation tasks, T00 through T10. Tasks are complete only when their named tests pass, their interfaces match the contract catalog, and their evidence is committed separately from the frozen reference. The independent qualification owner owns expected results. Legal reviewers own accepted legal interpretations and coverage. The implementer does not settle a legal disagreement by changing the expected answer.

The recommended execution method is separate implementer and reviewer contexts for each task, with one whole-package review at the final mechanical gate. T02 and T03 can proceed in parallel after T01. Real-source review can proceed alongside the synthetic kernel once its interface is stable. T06 and T07 remain sequential because plan obligations affect the UoW bridge contract.

### Roles

| Role | Accountability |
| --- | --- |
| Architecture owner | Contract versions, scope decisions and compatibility boundaries |
| Assessment engineer | Typed records, deterministic predicates, applicability and legal evaluation |
| Workflow and host engineer | UoW bridge, causal histories, durable records and host projection |
| Legal knowledge engineer | Source provision mapping, rule formalization and coverage records |
| Qualified legal reviewer | Scope-specific review of sources, applicability, interpretation and priorities |
| Independent qualification owner | Frozen expectations, first independent results and defect adjudication |
| Product and release owner | Pilot charter, explanation usefulness and bounded release statement |

Names and calendar capacity are recorded in the kickoff charter. They are operational assignments, not missing semantic choices. The dependency sequence and release gates are fixed here; calendar commitments follow the host-source inspection and the selected legal-pilot scope.

## 2 Repository and file map

All following paths are proposed unless identified as existing. From the host repository root, create experiments/authority_assessment/v0_1. Within that project root create the files below. Keep modules small and separated by responsibility.

| File or directory | Responsibility |
| --- | --- |
| intel_authority/__init__.py and api.py | Versioned public entry points |
| intel_authority/contracts.py | Immutable typed records and semantic validation |
| intel_authority/canonical.py | Canonical records, exact decimal representation and digests |
| intel_authority/registry.py | Versioned actor, capacity, operation and interest registries |
| intel_authority/sources.py | Source and reviewed pack validation; review-boundary port |
| intel_authority/predicates.py | Four-state evidence and closed condition language |
| intel_authority/applicability.py | Reviewed scope selection and coverage diagnostics |
| intel_authority/evaluator.py | Basis paths, exceptions, conflicts and final dispositions |
| intel_authority/delegation.py | Bounded grant paths and scope attenuation |
| intel_authority/queries.py | Bounded action and actor enumeration |
| intel_authority/gaps.py | Typed blockers and conditional materiality |
| intel_authority/courses.py | Step and whole-course assessment |
| intel_authority/allocations.py | Owner-issued allowance evidence and reservations |
| intel_authority/uow_bridge.py | Separate analytical admission and action-entry checks |
| intel_authority/causal.py | Named streams, causal parents and reference-time mapping |
| intel_authority/store.py | Atomic SQLite publication and immutable revisions |
| intel_authority/reassessment.py | Dependency change detection and cache binding |
| intel_authority/projection.py | Host-neutral read-only projection contract |
| intel_authority/reporting.py and cli.py | Structured result and bounded explanation output |
| contracts/authority_contracts_v0_1.json | Contract catalog supplied with this plan |
| contracts/catalog_extension_v0_1.json | New record types, relations and allowed layers |
| fixtures/synthetic/ | Two fictional rule packs, actors, operations and source contexts |
| qualification/authority_cases_v0_1.json | The 56 named obligations supplied with this plan |
| qualification/direct_oracle_v0_1.json | Independently authored 288 expected cells |
| qualification/reverse_domains_v0_1.json | Frozen complete domains and expected selections |
| tools/capture_baseline.py | Pinned dependency capture and existing baseline commands |
| tools/freeze_expectations.py | Case, oracle, domain and source manifest freezing |
| tools/run_qualification.py | Separate counters and preserved result histories |
| tools/publish_release.py | Mechanical checks and bounded release manifest |
| tests/ | Focused owned and independent unittest modules |
| docs/ | Design, plan, source-review guide and deployment operating notes |

Create __init__.py in tools and tests. Do not silently use namespace-package behavior to mask missing imports.

Create the proposed host successor at experiments/intelligence_integration/v0_2/authority_adapter.py only after G0b identifies the actual host interface. Its companion host_mapping_contract.json records that interface, host commit, accepted semantic mappings, stream ownership and excluded lifecycle surfaces. Existing host module names are not guessed by this plan.

Store new evidence under evidence/authority_assessment/v0_1/<run_id> and frozen release artifacts under artifacts/authority_assessment/v0_1. A run_id is an opaque generated identifier; it is not a shared clock or legal effective time.

## 3 Public interfaces

Implement these exact names and argument order. Types and mandatory result fields are defined in contracts/authority_contracts_v0_1.json. Every result is serializable to a versioned JSON record. Invalid external inputs are reported through ValidationResult or result diagnostics; they must not partly publish a record.

| Interface | Contract |
| --- | --- |
| validate_case(case, registry) | ActionCase and RegistrySnapshot to ValidationResult |
| verify_pack(pack, review_context) | RulePack and ReviewContext to PackValidation |
| evaluate_condition(expression, case, evidence, context) | ConditionExpr, ActionCase, EvidenceSnapshot and AssessmentContext to EvidenceValue |
| resolve_applicability(case, packs, context) | ActionCase, RulePack sequence and AssessmentContext to ApplicabilityAssessment |
| assess_case(case, context, budget) | ActionCase, AssessmentContext and EvaluationBudget to LegalAssessment |
| enumerate_actions(query, context, budget) | ActionQuery, AssessmentContext and EvaluationBudget to CandidateResult |
| enumerate_actors(query, context, budget) | ActorQuery, AssessmentContext and EvaluationBudget to CandidateResult |
| derive_authority_gaps(assessment, question) | LegalAssessment and IntelligenceQuestionRef to AuthorityGap sequence |
| assess_course(course, context, budget) | CourseOfAction, AssessmentContext and EvaluationBudget to CourseAssessment |
| compare_courses(courses, context, comparison_policy, budget) | CourseSet, AssessmentContext, CourseComparisonPolicy and EvaluationBudget to CourseComparison |
| assess_uow_entry(proposal, admission_context) | AuthorityWorkProposal and AdmissionContext to UowEntryDecision |
| relate_events(left_ref, right_ref, snapshot) | Two EventRef values and CausalSnapshot to EventRelation |
| compare_legal_reference(mapping, occurrence_ref, context) | ReferenceTimeMapping, EventRef and AssessmentContext to LegalTimeRelation |
| publish_assessment(result, store, access_context) | LegalAssessment or CourseAssessment, RecordStore and AccessContext to PublicationReceipt |
| find_reassessment(prior, current_context, new_candidates) | AssessmentRef, AssessmentContext and DependencyRef sequence to ReassessmentResult |
| project_host_case(snapshot, mapping_contract) | HostSnapshot and HostMappingContract to ProjectionResult |

Functions that assess, enumerate, compare, validate or project are read-only. publish_assessment and reviewed import are the only analytical persistence boundaries in this release. Actual UoW transition application remains within the existing named workflow owner; the authority package does not acquire a generic mutation API.

LegalAssessment, CandidateResult, CourseAssessment and CourseComparison deliveries return a flat derived_records closure. Every fresh result reference is inspectable through that closure without a hidden write or global lookup. This transport field is excluded from logical-record hashes and stored payloads. An extracted assessment retains its content hash when the owning closure is attached for publication. Candidate and comparison envelopes remain returned outputs; publish_assessment writes a selected legal or course assessment and its required closure atomically.

## 4 Task T00 Freeze the baseline and qualification inputs

**Dependencies:** None.  
**Owner:** Qualification owner with architecture and host owners.  
**Creates:** tools/capture_baseline.py, tools/freeze_expectations.py, tests/test_baseline.py, fixtures/synthetic, qualification/direct_oracle_v0_1.json, qualification/reverse_domains_v0_1.json, baseline_manifest.json and host_mapping_contract.json.

**Consumes:** The supplied reference archive and source manifest, this design, contract catalog and named obligations.  
**Produces:** Verified reference identity; immutable qualification expectations; a declared host-source status.

- [ ] Write test_reference_digest_mismatch_rejected and test_freeze_refuses_existing_manifest. Assert a changed pinned workflow byte prevents a qualified baseline; an existing freeze cannot be overwritten.
- [ ] Run python -B -m unittest tests.test_baseline -v and retain the expected initial failure.
- [ ] Implement baseline capture with an explicit reference directory and newly generated evidence directory. Invoke existing reference commands with that directory as their working directory. Record exit codes, outputs, hashes and the original disagreement expectations.
- [ ] Have the independent owner author and review all 288 direct cells, the reverse domains and the required subcases of AQ01 through AQ56 without inspecting candidate implementation. Expected records include disposition, decisive rules, conditions, coverage and relevant affected interests.
- [ ] Freeze source, oracle, case and contract digests. A fixture amendment creates a new freeze with an adjudication record.
- [ ] Run the owned baseline tests and existing reference suite once. Record 152 methods including 24 QF obligations as separate nested counters, not an additive total.
- [ ] Inspect the actual host source and clock mapping when available; record G0b complete or host_projection_unavailable. A missing host does not block the standalone kernel.
- [ ] Commit the baseline tools, inputs and frozen expectations as one reviewed change.

**Exit G0a:** Reference, contracts and independent synthetic expectations are frozen.  
**Exit G0b:** Actual host interface and clock-domain contract are inspected before host work starts.

## 5 Task T01 Implement contracts registry and identity

**Dependencies:** G0a.  
**Creates:** contracts.py, canonical.py, registry.py, causal.py primitives, api.py exports, catalog_extension_v0_1.json, tests/test_contracts.py and tests/test_identity.py.

**Consumes:** Contract catalog and frozen base-catalog digest.  
**Produces:** Typed records, ValidationResult, deterministic digests and explicit stream identities.

- [ ] Write tests named for AQ05, AQ09, AQ13, AQ41 and AQ56. Individually mutate actor, capacity, operation, affected scope, recipients, purpose and context; require changed binding digests. Keep self-pairs valid and unfamiliar actors unresolved where syntactically valid.
- [ ] Run python -B -m unittest tests.test_contracts tests.test_identity -v; retain the initial failing record.
- [ ] Implement required-field and semantic validation. Reject duplicate JSON keys, unknown required enum values, malformed references, surrogate code points in IDs, noncanonical decimal quantities and ambiguous units.
- [ ] Define a versioned canonical serializer: UTF-8 bytes of sorted-key compact JSON, ensure_ascii true, no floating-point values, and a pinned schema identifier. List order is semantic except fields explicitly declared as sets, which are sorted by canonical element bytes.
- [ ] Keep legal actor IDs and clock IDs separate. Validate the delimiter-overlap pair and canonical round trip. Specify the history and epoch encoded by each domain.
- [ ] Implement relate_events and compare_legal_reference as separate pure primitives. Test that a reviewed interval mapping alone creates neither causal order nor knowledge of a branch guard. T07 later integrates these primitives with UoW lifecycle records.
- [ ] Verify both test modules pass and that the base-catalog digest remains unchanged.
- [ ] Commit contracts, identity and registry support.

**Acceptance:** R01 through R04 and R16 structural obligations are executable. Schema validation alone is not labeled full semantic qualification.

## 6 Task T02 Implement source and review packages

**Dependencies:** T01.  
**Creates:** sources.py, review import port, fixtures/synthetic source and review records, tests/test_sources.py.

**Consumes:** RulePack, SourceArtifact, ReviewRecord, ReviewContext and registry types.  
**Produces:** verify_pack and PackValidation, including accepted and unresolved review findings.

- [ ] Write AQ19 through AQ24 and AQ52 source-boundary cases. Require exact source-to-rule-to-review traceability. A trusted_fixture receipt is rejected for reviewed_pilot mode; an unverified reviewer receipt cannot publish an accepted pack.
- [ ] Run python -B -m unittest tests.test_sources -v and retain failure.
- [ ] Implement immutable pack loading, provision and version checks, review-kind separation, allowed source kinds, supported semantic-profile checks and source content treated only as data.
- [ ] Validate CompositionPolicy, GrantRecord, InterpretationBranch and ReferenceTimeMapping payloads. References to these records cannot be replaced with opaque labels or source-kind tags. Their outcome semantics are frozen before the independent oracle in T00.
- [ ] Supply a fixture review verifier for synthetic mode and an interface for the host's authenticated review boundary. Do not accept an untrusted reviewed flag as the host verifier.
- [ ] Record contested interpretation and coverage as explicit input branches or gaps. Do not select the newest upload as an implicit priority.
- [ ] Verify the source tests pass; commit the pack loader and review port.

**Acceptance:** A reviewed pack can be reconstructed and its trust mode is explicit. Legal content review for the real pilot remains a separate gate.

## 7 Task T03 Implement evidence and applicability

**Dependencies:** T01; uses T02 validated packs when available.  
**Creates:** predicates.py, applicability.py, tests/test_predicates.py and tests/test_applicability.py.

**Consumes:** EvidenceFact, AssessmentContext, ConditionExpr and validated RulePack records.  
**Produces:** evaluate_condition and resolve_applicability.

- [ ] Write AQ03, AQ13 through AQ15, AQ38, AQ42 and AQ49 tests. Exhaust the 16 ordered pairs for AND, 16 for OR and four NOT inputs using the design's exact support/refutation equations.
- [ ] Add comparisons of an exact case quantity to a reviewed limit and of a scoped evidenced quantity to a threshold. Assert that multiple or contradicted quantity values yield an unknown comparison with quantity_conflict, and that a proposition leaf combines all aligned accepted evidence.
- [ ] Run python -B -m unittest tests.test_predicates tests.test_applicability -v and retain failure.
- [ ] Implement the closed AST with aligned references, evidence lineage and exact unit-aware comparisons. Preserve unrelated evidence as excluded support with reasons.
- [ ] Implement included, excluded, unresolved and conflicting applicability results. Unknown scope facts remain unknown. Wrong territory or capacity is inapplicable when established, not a universal denial of the actor.
- [ ] Implement explicit legal reference-time evidence; no numeric comparison of unrelated UoW counters establishes applicability.
- [ ] Verify all focused tests pass and commit evidence and applicability.

**Acceptance:** Unknown, false and conflicting propositions remain different, including when nested inside exceptions or scope conditions.

## 8 Task T04 Implement direct authority assessment

**Dependencies:** T02 and T03.  
**Creates:** evaluator.py, delegation.py, tests/test_evaluator.py and tests/test_delegation.py.

**Consumes:** Validated cases, packs, EvidenceValue and ApplicabilityAssessment.  
**Produces:** assess_case with complete LegalAssessment records.

- [ ] Write AQ01 through AQ04, AQ07 through AQ12, AQ16 through AQ18, AQ50 and AQ51. Include one valid alternative basis alongside a failed basis, an unresolved exception, a surviving prohibition in a second regime and an explicit reviewed private-liberty default.
- [ ] Include a failed consent route plus a potentially sufficient unresolved alternative; require aggregate unresolved. Include one supported context branch and one prohibited branch; require aggregate unresolved with both branch findings retained.
- [ ] Run python -B -m unittest tests.test_evaluator tests.test_delegation -v and retain failure.
- [ ] Implement alternative basis paths, mandatory regime composition, typed normative positions, explicit priorities and the whole-case disposition rules.
- [ ] Implement delegation as bounded paths with established originating authority, issuer competence, explicit delegability and scope attenuation on every edge. Organizational reachability alone supplies no delegation.
- [ ] Reject normative dependency or priority cycles in the supported profile. Preserve legitimate organizational cycles. An over-depth delegation path stays unresolved while an independent valid route can still be assessed.
- [ ] Preserve post-action duties and distinguish legal competence from exercise of the power and physical capability.
- [ ] Run focused tests and all 288 direct oracle cells. Retain the first independent differences and repair only through documented candidate changes or reviewed expectation revisions.
- [ ] Commit the direct evaluator when required agreement is exact.

**Exit G1:** Direct bounded evaluation matches the independent oracle and all mandatory direct negative cases.

## 9 Task T05 Implement reverse queries and meaningful gaps

**Dependencies:** T04.  
**Creates:** queries.py, gaps.py, tests/test_queries.py and tests/test_gaps.py.

**Consumes:** assess_case, CandidateDomain, query types and question references.  
**Produces:** enumerate_actions, enumerate_actors and derive_authority_gaps.

- [ ] Write AQ25 through AQ33. Assert supported candidate sets agree with independent direct expectations; unknown candidates remain visible; a cutoff has complete false and a positive unassessed_count.
- [ ] Run python -B -m unittest tests.test_queries tests.test_gaps -v and retain failure.
- [ ] Implement deterministic finite enumeration over declared actor, capacity, operation and parameter bindings. Return counts and exclusions for every candidate class.
- [ ] Return a complete flat derivation closure for new cases, assessments and gaps. The AQ55 read-only subcase must resolve every fresh reference without a store write.
- [ ] Implement typed gap derivation with scope, dependencies and matching resolution route. Propose conditional branches only to assess materiality; do not close actual gaps.
- [ ] Require a witnessed outcome or basis change for those materiality labels. Use coverage_required or undetermined when that is what the evidence supports.
- [ ] Verify complete reverse selections against both direct evaluations and the independent oracle. Verify an always-unresolved implementation would fail expected positive cells.
- [ ] Commit the query and gap capabilities.

**Acceptance:** The platform can answer which considered actions or actors are supported and what information or authority could change the answer.

## 10 Task T06 Implement finite courses and shared limits

**Dependencies:** T05.  
**Creates:** courses.py, allocations.py, tests/test_courses.py and tests/test_allocations.py.

**Consumes:** Direct assessments, observation guards, CourseOfAction and AllocationRecord.  
**Produces:** assess_course, compare_courses and aggregate constraint findings.

- [ ] Write AQ34 through AQ36, AQ53 and AQ54. Use two alternative courses of two or three steps, a consent-dependent branch, an indivisible shared resource and a step that removes a later prerequisite.
- [ ] Run python -B -m unittest tests.test_courses tests.test_allocations -v and retain failure.
- [ ] Implement the finite course DAG with step bindings, guards, hypothesized effects, residual duties and cumulative constraints. No legal support for a step establishes its successful occurrence.
- [ ] Implement CourseSet comparison in display_only mode. Bind its policy and full domain digest, return each assessment and declared measures, and preserve evaluated and unassessed counts without ranking.
- [ ] Return all fresh step and branch assessments in the owning derivation closure and preserve their logical hashes when extracted. Cover the AQ55 read-only course subcase.
- [ ] Require a single fixed action across all branches for robustness; permit contingent selection only when the guard evidence is available to the deciding actor at that step's declared local frontier.
- [ ] Implement owner-issued allocation evidence and conservative unknown availability. Prevent duplicate use of one reservation across UoWs. Do not release on cancellation request or receipt.
- [ ] Verify all focused cases, limits and partial-search outputs. Commit course assessment.

**Acceptance:** Individually supported steps can still produce a blocked or unresolved combined course, with a specific witness.

## 11 Task T07 Implement the UoW bridge and causal history

**Dependencies:** T04 and T06.  
**Creates:** uow_bridge.py, causal.py lifecycle integration, tests/test_uow_bridge.py and tests/test_causal.py.

**Consumes:** AuthorityWorkProposal, independently supplied AdmissionContext, LegalAssessment and CausalSnapshot.  
**Produces:** assess_uow_entry, lifecycle use of the causal and legal-reference primitives, and explicit work-to-subject bindings.

- [ ] Write AQ06, AQ22, AQ37 and AQ39 through AQ48. Assert an admitted assessment UoW can report a prohibited subject act, while execute_assessed_action cannot pass its entry contract with that same finding.
- [ ] Bind the full WorkSubject for every work kind. Expand an admitted enumeration domain while retaining its first case, and add a course to an admitted CourseSet; both must require successor admission in v0.1.
- [ ] Run python -B -m unittest tests.test_uow_bridge tests.test_causal -v and retain failure.
- [ ] Implement the two work-kind paths. Analytical work admission covers its own access and audience. Action-entry validation requires an actual supported assessment and matching independent operational authority; it still exposes no executor.
- [ ] Use the frozen admission function only where its representation is faithful. Return unsupported_projection for a lossy request; never convert a legal result into an actual grant view.
- [ ] Bind stream-local ordering, actual causal parents, local receipt frontiers and declared reference-time mappings to the named UoW lifecycle records. Keep applying boundary identity separate from stream encoding.
- [ ] Integrate the T01 causal and legal-reference primitives without conflating their relation types. A legal-time attestation alone cannot make an observation available to a course decision.
- [ ] Preserve cancellation request, receipt, acceptance and application. Require exact application authority and separate allocation-release evidence.
- [ ] Verify focused cases, including unchanged historical admission after a later expiry and reconciliation before nonidempotent retry.
- [ ] Commit the bridge and local history support.

**Exit G2:** Analytical assessment and operational admission are independent, and the complete new workflow harness preserves the existing authority and time boundaries.

## 12 Task T08 Implement durable publication and reassessment

**Dependencies:** T07.  
**Creates:** store.py, reassessment.py, tests/test_store.py and tests/test_reassessment.py.

**Consumes:** Result records, AccessContext, dependency pins and the catalog extension.  
**Produces:** publish_assessment, find_reassessment, immutable replay and change notifications.

- [ ] Write AQ21, AQ30, AQ43 through AQ45 and AQ55. Inject an interrupted publication before commit; assert no partial result or link survives and a retry with the same identity is idempotent only for identical bytes.
- [ ] Run python -B -m unittest tests.test_store tests.test_reassessment -v and retain failure.
- [ ] Implement atomic SQLite transactions for an assessment and its required links. Enforce unique ID/revision and append-only published revisions.
- [ ] Validate the complete returned derivation closure and normalize away transport-only fields before hashing or storage. Use AQ55 to cover missing closure members, duplicate identity collisions and extraction from query or course outputs without changing logical-record hashes.
- [ ] Implement access-checked retrieval and explanation projection. Host permissions govern access; the legal actor being assessed confers no reader permission.
- [ ] Implement dependency and newly relevant source discovery. Require changed case, context, role, affected scope, review, source, coverage or frontier pins to prevent incompatible cache reuse.
- [ ] Verify restart replay, preserved prior findings, successor reasons and restricted-source explanation behavior.
- [ ] Commit durable analytical publication.

**Acceptance:** A stored result remains reproducible after amendments, and failed publication cannot leave a misleading partial record.

## 13 Task T09 Implement command line and host projection

**Dependencies:** T08 and G0b for the host portion.  
**Creates:** reporting.py, cli.py, projection.py, tests/test_cli.py, tests/test_projection.py and the inspected successor host adapter.

**Consumes:** Public interfaces, AccessContext and the frozen host mapping contract.  
**Produces:** Read-only assess, enumerate, gaps and compare commands with JSON and text outputs.

- [ ] Write CLI contract checks and projection cases using AQ05, AQ09, AQ20, AQ24, AQ30, AQ37, AQ41 and AQ56. Compare the host snapshot digest before and after every entry point.
- [ ] Run python -B -m unittest tests.test_cli tests.test_projection -v and retain failure.
- [ ] Implement explicit command arguments for case, context, budget, mode and output. No implicit latest pack selection or live source fetch occurs during deterministic evaluation.
- [ ] Implement field-level source provenance, semantic mapping status, namespaced event IDs and unsupported-projection results.
- [ ] Keep real lifecycle projections rejected. Do not expose source-to-grant promotion, arbitrary host writes or external execution.
- [ ] Run the actual host's existing integration suite under its inspected commands and candidate commit. Preserve host, reference, clock and new-authority counts separately.
- [ ] Commit the read-only integration and inspectable report outputs.

**Exit G3:** The actual host can project cases and consume explanations without mutating its source graph or actual workflow state.

## 14 Task T10 Qualify the release and conduct the reviewed pilot

**Dependencies:** G1, G2 and all applicable standalone mechanical checks. G3 is additionally required for an integrated release and the reviewed integrated pilot claim.  
**Creates:** tools/run_qualification.py, tools/publish_release.py, tests/test_qualification_runner.py, legal_pilot_charter.json, pilot review records and release_manifest.json.

**Consumes:** Frozen case catalog and independent oracle, candidate source hashes, current baseline results, actual host evidence and reviewed real-source scope pack.  
**Produces:** A bounded mechanical qualification report and a separately reviewed pilot record.

- [ ] Write test_runner_separates_counts and test_runner_refuses_false_pass. A missing case, unexpected unresolved result, absent host evidence or unsupported positive result prevents the relevant release gate.
- [ ] Implement GQ01 and GQ02 release governance checks for R24. Keep the fixed campaign's closure and successor-scope rules explicit; an unavailable host or pilot gate permits only the separately labeled standalone mechanical path.
- [ ] Run python -B -m unittest tests.test_qualification_runner -v and retain failure.
- [ ] Implement one runner with explicit stages reference, named_cases, direct_oracle, reverse_consistency, host and pilot. Report methods, named obligations, cells and checks in separate fields.
- [ ] Run every mandatory AQ obligation and all 288 direct cells against the frozen expectations. Preserve first independent failures and successive repair results.
- [ ] Have the qualified reviewer accept a real-source pack in one declared legal scope, including applicability, interpretations, exceptions, priorities, affected interests and exclusions.
- [ ] Freeze a 30-case read-only pilot before observing outputs: 12 direct, eight reverse and ten course or historical cases. Record independent human dispositions and material explanation criteria.
- [ ] Adjudicate each disagreement or preserve the relevant uncertainty in the result. Measure review effort and actual runtime without inferring a comparative benefit.
- [ ] Run the required final reference and host gates once after repairs, verify source digests and publish the bounded release statement.
- [ ] Commit the release manifest and close the declared campaign.

**Exit G4:** All mandatory mechanical checks pass with zero unresolved critical defects.  
**Exit G5:** Every pilot case is reviewed, every decisive finding is traceable, and remaining legal uncertainty is represented accurately.

## 15 Verification commands

Commands below are implementation targets unless explicitly marked existing. They become runnable only after their owning task creates the tool. Run package commands from experiments/authority_assessment/v0_1.

Existing reference commands, run from the extracted reference directory:

    python -B -m unittest discover -s tests -v
    python -B run_qualification.py --output authority_baseline_001.json
    python -B -m examples.integrated_trace

The existing qualification runner refuses an existing output filename. capture_baseline creates a fresh evidence run and invokes it with a new absolute output path.

Proposed package commands use POSIX shell line continuation below. In PowerShell, put each command and its arguments on one line.

    python -B -m unittest discover -s tests -v
    python -B -m tools.run_qualification \
        --stage mechanical --new-run \
        --evidence-root ../../../evidence/authority_assessment/v0_1
    python -B -m tools.run_qualification \
        --stage host --new-run \
        --evidence-root ../../../evidence/authority_assessment/v0_1
    python -B -m tools.run_qualification \
        --stage pilot --new-run \
        --evidence-root ../../../evidence/authority_assessment/v0_1
    python -B -m tools.publish_release \
        --release-version 0.1 \
        --evidence-root ../../../evidence/authority_assessment/v0_1 \
        --output-root ../../../artifacts/authority_assessment/v0_1

Each tool reports its generated run directory. It rejects overwriting a frozen record. publish_release requires an explicitly selected compatible chain of passing stage records in a release_selection.json file under the evidence root; it must not pick the newest wall-clock timestamp as implicit authority.

## 16 Release gates and stop conditions

| Gate | Evidence required | Scope of the claim |
| --- | --- | --- |
| G0a | Pinned reference, contracts and independent expectations | Stable engineering baseline |
| G0b | Inspected host source and clock mapping | Actual integration target is known |
| G1 | Direct mandatory cases and all 288 cells agree | Correct bounded direct semantics |
| G2 | UoW, scenario, time, course and shared-limit cases pass | Preserved local authority boundaries |
| G3 | Actual host projection and baseline compatibility pass | Read-only host integration |
| G4 | All 56 obligations and required subcases pass; no critical defect | Finite mechanical qualification |
| G5 | Accepted real-source scope and all 30 pilot cases reviewed | Bounded reviewed legal pilot |

A passing count never compensates for an unsupported positive finding, lost source or review binding, fabricated grant, invented temporal order, hidden incomplete search, scope leakage or historical rewrite.

If a gate fails, repair the identified defect and rerun its focused checks, then the required release gate. Expand testing only to cover a concrete uncovered risk. Keep the original failing evidence. Do not redefine an expected disagreement into success without a reviewed contract amendment.

Close v0.1 after G0a through G5 pass for the selected release scope. If the host or legal-pilot prerequisite is unavailable, a standalone mechanically qualified package may be published under that narrower label, with G3 or G5 explicitly unavailable. It must not be labeled an integrated reviewed legal platform.

## 17 First executable milestone

The first milestone is G0a plus T01 through T04: a standalone direct evaluator with complete source and review binding, four-state evidence, explicit applicability, separate legal dispositions and exact agreement on the 288-cell fictional oracle.

That milestone answers the essential question in a controlled setting: can the software assess one actor's specific act toward another without confusing legal support, uncertainty, subject evidence and UoW admission? Reverse queries, courses, durable history and host integration then build on the same qualified direct semantics.

The design, plan and catalogs form one engineering handoff. They define future implementation and acceptance work. No new platform implementation or authority test result is asserted by publication of this plan.

