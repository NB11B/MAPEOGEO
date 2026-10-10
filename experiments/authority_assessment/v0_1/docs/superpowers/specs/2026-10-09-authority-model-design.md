# MAPEOGEO Authority Model Design

**Author:** Nathanael J. Bocker  
**Date:** 9 October 2026  
**Design version:** 1.0  
**Target release:** Authority assessment v0.1  
**Copyright:** © 2026 Nathanael J. Bocker. All Rights Reserved.

## 1 Purpose and implementation decision

Build an intelligence analysis capability that evaluates a specific actor's proposed conduct toward another actor or affected interest under an explicit, reviewed legal framework. The platform must explain which legal positions apply, which conditions matter, what remains unresolved, and which additional work could change the answer. It must support both direct questions and bounded searches for possible actions, actors and courses of action.

The engineering decision is an additive deterministic authority package. MAPEOGEO supplies identities, relationships and source-linked context. Operational grammar supplies a versioned description of the action and its effects. The new package supplies applicability, legal-position assessment, gaps and comparison. UoW continues to govern the platform's own work, using a separate actual admission decision.

The initial release is a read-only analytical capability with a local workflow integration harness. It includes no external collection, communication, intervention or lifecycle executor. A reviewed legal pilot follows mechanical qualification. Its release claim will identify the actual legal scope, versions, supported operations and exclusions.

The design is intended for the engineer implementing the package, the host adapter owner, the legal knowledge engineer and the independent qualification owner. It preserves the current platform's evidence boundaries and makes the new authority semantics explicit enough to implement and test.

## 2 Baseline and migration boundaries

The inspected reference is intelligence_qualification_v0_3. Its report records 152 passing unittest methods, including the 24 frozen QF obligations. The original grammar baseline retains five disagreements, producing 19 of 24 matches; those disagreements are part of the preserved baseline. These are historical evidence statements, not a new software test run for this plan. [S1]

The current assess_admission function evaluates the exact actor, action, purpose, opaque scope, resources and recipients in a bound proposal against every supplied nonempty reviewed toy-policy view. It returns admitted, rejected, unresolved or context_or_model_error. The views stipulate grant effectiveness. The checker does not identify generally affected actors, select applicable law, authenticate instruments or resolve legal exceptions. A rejected resource or scope check is not itself a legal prohibition. [S2]

The frozen catalog checks record envelopes, revision pins and selected graph-layer relations. Its 42 record types do not have complete semantic implementations. The existing grammar adapter preserves explicit source conventions and alternative interpretations; it does not perform raw-language understanding. The analysis module supplies bounded evidence, gaps and scenario functions that can be reused only where their meanings match the new contract. [S1, S3]

The supplied host report identifies a read-only integration with 17 integration methods and 15 parity checks. The actual host adapter source was not available in this workspace. The clock-identity correction is a separate proposed codec and test package; its application to the host has not been confirmed. Gate G0 requires inspection of the actual host before any host compatibility claim. [S4, S5]

All v0.3 source bytes, frozen fixtures, expected results and historical reports remain unchanged. The successor package has its own namespace, schemas, qualification files and evidence directory. Compatibility is explicit and never achieved by weakening a frozen check or relabeling an old failure.

## 3 Alternatives considered

| Approach | Benefit | Limitation | Decision |
| --- | --- | --- | --- |
| Add a separate authority package | Keeps legal semantics inspectable and preserves the existing reference | Requires an explicit bridge and versioned contracts | Selected |
| Expand the existing admission function | Small initial integration surface | Mixes legal applicability with actual work admission and its universal view check | Retain only as a compatibility slice |
| Adopt a general legal reasoning service immediately | Potential future interoperability and wider language support | Adds semantic, dependency and legal-content commitments before the required profile is qualified | Defer behind a future adapter |

The selected package is one Python library, not a mandated fleet of services. Use the reference's Python 3.12 baseline and standard-library mechanisms for the deterministic kernel, local storage and qualification runner. An optional language model can propose candidate mappings or explanatory text later; it does not own rule activation, review status, grants, admission or actual-state mutation.

OASIS LegalRuleML supplies a useful representation reference for normative positions, exceptions, source links, roles, jurisdiction and time. W3C PROV-DM supplies provenance concepts. NIST's ABAC guidance informs the distinct operational access-control boundary. These references guide design; they do not establish implementation conformance or legal completeness. [W1, W2, W3]

## 4 Requirements and invariants

| ID | Required behavior |
| --- | --- |
| R01 | Bind a directed action case to actor, capacity, operation, affected scope, recipients, purpose, objects, jurisdiction context and legal reference context. |
| R02 | Accept any well-formed actor pair, including self-pairs and declared collective scopes; retain unsupported or unresolved identity and coverage. |
| R03 | Keep ClaimOfAuthority, LegalAssessment and AdmissionDecision as separate record meanings and graph layers. |
| R04 | Preserve permissions, powers, prohibitions, duties, claim-rights and immunities as distinct legal-position types. |
| R05 | Separate source provenance, source authenticity review, formalization review, applicability review, priority review and coverage review. |
| R06 | Evaluate applicability explicitly; record included, excluded, unknown and conflicting grounds. |
| R07 | Preserve supported, refuted, unknown and conflicting factual conditions with aligned evidence and lineage. |
| R08 | Distinguish alternative legal bases from independently applicable regimes, constraints and context alternatives. |
| R09 | Apply only reviewed exceptions and priority relations; do not infer priority from recency, rank, insertion order or a model score. |
| R10 | Produce traceable supported, conditions-unmet, prohibited and unresolved findings, with technical errors separate. |
| R11 | Return bounded action and actor searches with exact candidate counts, exclusions and an unassessed remainder. |
| R12 | Derive typed gaps and explain whether closing them could change an outcome, its basis or required coverage. |
| R13 | Assess every step and the combined effects, constraints and residual duties of a finite course of action. |
| R14 | Preserve the same fixed proposal across alternative contexts; allow contingent branches only on information available at the deciding step. |
| R15 | Prevent hypothetical facts, grants, reviews, effects and completion from establishing actual evidence or authority. |
| R16 | Preserve internal time for each UoW and explicit causal links; do not compare unrelated counters as a shared clock. |
| R17 | Bind any operational use to a separate exact UoW proposal, actual admission and applicable enforcement contract. |
| R18 | Preserve historical assessments and receipt knowledge; append successors and invalidate incompatible reuse. |
| R19 | Account for shared limits through an explicit owner or allocation protocol; uncertain cancellation does not release capacity. |
| R20 | Preserve source-to-result provenance and enforce the reader's existing access and audience restrictions. |
| R21 | Keep the reference immutable and host projection read-only until a separately qualified lifecycle contract exists. |
| R22 | Terminate every evaluation within declared structural budgets and report partial work honestly. |
| R23 | Qualify legal formalization and analyst usefulness separately from mechanical implementation behavior. |
| R24 | Close the release at the declared gates; expand scope through a successor contract rather than an open-ended test campaign. |

### Global constraints

Each UoW has internal time; no shared clocks.

No source assertion, model suggestion, scenario, analytical need or favorable effect creates an actual grant.

No result is promoted from CANDIDATE_REPRESENTS to REPRESENTS or SAME_SEMANTICS merely because a downstream assessment becomes convenient.

No absent field means false, no missing rule means permission, and no missing grant means prohibition.

No reviewed legal finding alone admits platform execution.

No UI, model training, autonomous source promotion, new external action adapter or universal legal catalog belongs to v0.1.

## 5 Records and graph placement

The machine-readable contract catalog accompanies this design. It specifies record fields, enums, interfaces and semantic obligations. It is a declarative engineering catalog, not a claim that runtime validation already exists.

The catalog includes value objects and interface envelopes as well as persisted domain records. Its entry count is not a count of new graph entities with complete semantics. References identify an exact ID and revision; a separate content-pin manifest binds the resolved record bytes. This permits ordinary reciprocal graph relationships without circular content hashes. Every material model reference must resolve or appear explicitly in the snapshot's unresolved-reference set. An undeclared dangling required reference is a technical error; a declared unresolved identity or source remains an analytical gap.

Read-only assessment, query and course outputs carry a flat derived_records closure for fresh cases, assessments, branch results, gaps and other generated dependencies. A caller resolves references against the immutable input snapshot plus that returned closure. No unpublished global lookup is required. The closure is transport-only metadata, excluded from logical record hashes and stripped from stored payloads. An extracted assessment can carry its owner's closure into publication without changing its ID, revision or content hash. Duplicate identities with different normalized payloads are rejected. Candidate and comparison envelopes are returned outputs; selected LegalAssessment and CourseAssessment records and their required closures can be published atomically.

### ActionCase

An ActionCase identifies the legal question. Required bindings are id, revision, actor_ref, capacity_ref, operation_ref, operation_revision, parameters, affected_scope, recipients, object_refs, purpose_ref, jurisdiction_context_ref, legal_reference_context_ref, mode and context_ref. The mode is observed_claim, proposed_actual or hypothetical.

Affected scope records actors or a defined collective class, their relationship to the action, affected interests, proposed effects, evidential status and coverage. A recipient is stored separately. An unresolved affected actor can be represented by a scoped unresolved binding; it must not be replaced with an invented person. A self-pair is valid when the operation contract permits it.

An action's occurrence is separately evidenced. A LegalAssessment of a reported or proposed operation does not establish that the operation took place. Predicted indirect effects remain model-dependent claims. A gap in affected-party coverage must not become an assertion that all tertiary effects have been identified.

### OperationDefinition

The registry pins an operation's identity, version, parameter types, units, actor capacities, object and affected-interest roles, precondition vocabulary and modeled effects. The initial synthetic campaign uses request_record, compel_record, retain_record and share_record. These are test operation definitions under fictional rules, not statements about any real actor's powers.

The seven existing functional lenses remain analytical tags. They are not legal operators or an exhaustive authority taxonomy. Offensive or defensive orientation and positive or negative intended effect remain perspective annotations. They never satisfy an authority predicate.

Unknown operation semantics produce an unresolved assessment with an operation_definition_gap. No arbitrary method name is executed. Novel operations require a successor reviewed registry definition before their legal effects can be assessed.

### SourceArtifact and ReviewRecord

SourceArtifact stores the source identity, exact version and digest, provision locator, issuing-body claim, provenance, source kind and legal-time claims. Source kinds include legislation, judicial_decision, regulation, contract, internal_policy, grant_instrument and attributed_claim. A kind is a classification, not proof of authenticity or applicability.

ReviewRecord binds an authenticated or explicitly stipulated reviewer identity to exact source, rule, interpretation and coverage revisions. Its review_kind is one of authenticity, formalization, applicability, priority, coverage or interpretation. It records accepted, contested or rejected status, scope, rationale, limitations, receipt event and deciding review boundary.

A single review can explicitly cover several review kinds through separate findings. A JSON flag named reviewed cannot stand in for the review chain. In synthetic mode, trusted_fixture receipts are accepted only inside the fixture profile. In reviewed-pilot mode, review imports require the configured host review boundary to verify the reviewer and acceptance event. A digest protects binding to bytes; it does not establish legal authority or source authenticity.

### RulePack and NormRule

A RulePack pins source and review references, jurisdiction profile, interpretation profile, coverage contract, rule list, basis policy, composition policy, registry version and supported semantic profile. Changes create a successor revision.

A NormRule has applicability conditions, factual antecedents, a typed normative conclusion, preconditions, linked duties, exceptions and explicit priority edges. Each rule refers to precise source provisions and accepted formalization review. A right names a holder, bearer and protected interest. A duty names its bearer, beneficiary where relevant, required conduct, trigger, phase, timing and evidence criteria. A power names the relationship or legal effect it can change.

The initial semantic profile permits finite, grounded rules and acyclic explicit rule dependencies. Recursive defaults, self-justifying authority and general natural-language interpretation are outside that profile. They return a named unsupported_profile diagnostic with an unresolved disposition rather than being approximated silently.

CompositionPolicy explicitly lists mandatory regimes, alternative-basis groups, and reviewed displacement or choice relations. GrantRecord separately identifies issuer, grantee, capacity, scope, originating competence, parent grant, eligible delegation recipients, issuance event, effectiveness conditions and review. A source classified as grant_instrument does not substitute for the actual grant record. Each transfer must be supported by its parent and must narrow or preserve operations, purposes, affected interests, objects, recipients, jurisdiction, timing and quantitative limits. Transfer to a new grantee requires the parent's explicit delegation permission; it is not ordinary identity-set inclusion.

RulePack and BasisGroup policy declarations must agree with the accepted CompositionPolicy. A mismatch is a model error, not an opportunity for the evaluator to choose whichever policy produces a favorable result.

InterpretationBranch pins selected rules, interpretation and evidence context, any scenario assumptions, its mode and branch-domain coverage. ReferenceTimeMapping names the two reference domains, the relation or bounded interval, its evidential and review basis, applicability scope and uncertainty. These are outcome-determining inputs with validated payloads, not opaque policy labels.

### EvidenceFact and AssessmentContext

An EvidenceFact binds a subject, predicate, typed value, modality, legal reference context, origin lineage, review state, actual or hypothetical mode, and an actual receipt event where applicable. Supporting and opposing evidence references remain separate.

AssessmentContext pins the actor and operation registries, selected rule packs, interpretation branches, evidence snapshot, affected-interest coverage, jurisdiction context, legal reference context, observer frontier, review acceptance context and access context. Its digest identifies the complete supplied context, not global current truth.

The source, analytical derivation, scenario and actual UoW layers remain separate. ClaimOfAuthority belongs with attributed subject evidence. LegalAssessment belongs in analytical derivation, with a scenario reference when hypothetical. AdmissionDecision belongs in actual UoW. A new catalog extension declares these layers and relation types against the pinned base catalog.

### LegalAssessment

The result contains status, disposition, exact case and context digests, applicability findings, normative positions, basis paths, conditions, duties, conflicts, evidence references, review references, coverage, gaps, dependency pins, budget accounting and explanation trace.

Status is assessed, partial or context_or_model_error. Disposition is supported_within_scope, conditions_unmet, prohibited_under_reviewed_rule or unresolved. For context_or_model_error, disposition is null and diagnostics are mandatory. A malformed model must not be represented as a legal prohibition.

Partial evaluation returns disposition unresolved and retains any established local witnesses with their exact scope. A witness of a prohibition remains useful even when incomplete coverage prevents a final whole-case conclusion.

## 6 Evaluation semantics

### Four evidence states

Represent each factual proposition by support and refutation bits, plus the corresponding evidence references.

| Support | Refutation | Meaning |
| --- | --- | --- |
| 1 | 0 | Supported |
| 0 | 1 | Refuted |
| 0 | 0 | Unknown |
| 1 | 1 | Conflicting |

NOT exchanges the bits. AND supports only when every conjunct supports, and refutes when any conjunct refutes. OR supports when any disjunct supports, and refutes only when every disjunct refutes. No rule allows a contradiction to derive arbitrary unrelated facts.

Definite activation of a rule's material condition requires supported without unresolved contrary evidence. Conflicting and unknown material antecedents remain visible. Irrelevant uncertainty need not block an independent complete proof; the trace must show why that uncertainty cannot alter the result.

The condition language is closed: fact, all, any, not, eq, ge and le. A fact leaf identifies a scoped PropositionBinding, not a single report. The binding names the subject, predicate, expected value, modality and legal reference context; all aligned accepted supporting and opposing evidence contributes to its evidence pair.

Comparison operands are a literal TypedValue, a named parameter of the exact bound ActionCase, or a value obtained from a scoped PropositionBinding. The case is resolved through the supplied context snapshot. A parameter reference cannot name a different case revision. Numerical values use finite canonical decimal strings with declared units; binary floating-point, NaN, infinity and booleans used as numbers are rejected. Comparisons require compatible units and aligned contexts.

A quantity operand is established only when the aligned accepted evidence identifies one value without material contrary evidence. Missing values produce an unknown comparison. Multiple or contradicted values produce an unknown comparison with a quantity_conflict diagnostic and all source references. Refuting one exact value does not establish another value or an inequality. This conservative quantity rule is distinct from explicit support and refutation of a Boolean proposition. There is no eval, executable source text, arbitrary function or network lookup.

### Applicability before combination

The engine selects candidate rules from the supplied finite RulePack set and records whether each is included, excluded, unresolved or conflicting for the bound question. It retains the connecting facts and reviewed criteria. A geographic coordinate may contribute a fact; it does not by itself establish a legal jurisdiction.

Jurisdiction context can include territory, subject matter, personal connection, forum and the capacity in which the actor acts. The applicable taxonomy is pinned in the pack. Coverage states which dimensions and candidate regimes were considered. Missing mandatory scope dimensions prevent a positive whole-case finding.

### Basis paths and independent constraints

Alternative valid bases inside a reviewed regime are OR paths. Failure of one possible grant does not refute every other legal basis.

The reviewed composition policy declares which regimes independently constrain the action and which choice-of-law or displacement relations apply. All indispensable constraints from the selected applicable regimes must be satisfied. A favorable result in one regime cannot erase another regime's surviving prohibition.

Alternative factual worlds or interpretations are separate branches. A robust_supported annotation requires one identical bound ActionCase to be supported in every member of a nonempty, adequately covered branch set. Finding a different favorable action in each branch establishes no single robust action.

Private liberty can be modeled through an explicit reviewed default-basis rule. It does not require pretending that every lawful private action is a delegated governmental power. Public competence, contractual permission, consent and delegated authority retain different bases and conditions. Consent has a holder, affected interest, scope and validity conditions; it is not a universal override.

### Exceptions and conflict

A known applicable exception is evaluated through its reviewed defeat relation. An unknown material exception remains a possible defeater and prevents an unconditional positive result unless a scoped proof establishes its irrelevance. The engine never assumes an exception is absent merely because no fact was supplied.

Normative conflict concerns incompatible conclusions under aligned actors, capacities, operations, effects and temporal contexts whose relationship the reviewed profile cannot resolve. Permission and duty are not inherently conflicting. A duty and evidence of its nonperformance may establish a modeled violation, not an inconsistency in the legal rules.

Priority edges require accepted priority review and precise rule references. Priority cycles are invalid in the affected profile. Organizational relationship cycles are permitted and must not be mistaken for legal or causal cycles. A delegation cycle supplies no originating authority.

### Whole-case disposition

A supported_within_scope result requires valid input, completed relevant evaluation, adequate declared coverage, an established basis appropriate to each applicable regime, satisfied indispensable entry conditions, and no unresolved material defeater or surviving prohibition.

A prohibited_under_reviewed_rule result requires an established applicable prohibition and resolved material exception or priority questions for that conclusion. Its explanation names the rule and scope.

A conditions_unmet result requires established failure of a prerequisite indispensable to every relevant legal-basis path, or established failure of every relevant alternative after adequate coverage and complete evaluation. An unresolved alternative that could establish a sufficient basis prevents this disposition. No surviving applicable prohibition may remain; that has its own disposition. The result does not assert that the missing prerequisite can necessarily be obtained.

Unknown material facts, unresolved applicability, conflicting interpretations, uncovered interests, unsupported semantics and incomplete evaluation produce unresolved. Across a nonempty adequately covered branch set, the aggregate disposition can be supported, prohibited or conditions_unmet only when every branch supports that same disposition with its required proof. Mixed dispositions or any material unresolved branch produce aggregate unresolved. Branch findings remain available independently. An empty branch domain is not a vacuous positive proof.

Post-action duties remain attached to supported actions. Their discharge requires matching evidence when due. A proposed fulfillment step may support plan feasibility under assumptions; it does not mark the actual duty as discharged.

## 7 Authority queries and meaningful gaps

Provide three query entry points: assess_case, enumerate_actions and enumerate_actors. Enumeration takes an explicit finite CandidateDomain of actors, capacities, operations and parameter bindings. Each candidate uses the same direct evaluator. Return candidates by disposition, the domain digest, evaluated and unassessed counts, exclusions, stopping reason and completeness flag.

A complete empty supported set means no supported candidate in that declared domain. It does not mean no lawful option exists anywhere. A budget cutoff never converts an unassessed candidate into a negative finding. Direct and reverse parity is a consistency check and must also be compared with an independent oracle.

AuthorityGap has a typed unresolved proposition, scope, source assessment, dependencies, possible resolution routes and materiality finding. Gap kinds are fact_gap, authority_evidence_missing, grant_required, source_applicability_gap, interpretation_gap, coverage_gap, operation_definition_gap, resource_commitment_required, completion_reconciliation_required and admission_required.

Materiality findings are outcome_change_witnessed, basis_change_witnessed, coverage_required or undetermined. A counterfactual branch used to assess materiality remains hypothetical. It cannot close the actual gap. No numerical priority or probability is inferred from a count of possible branches.

Resolution routes are proposals for work. Reviewing a source can address an interpretation gap. Finding evidence of a valid grant can address authority_evidence_missing. A grant_required gap requires an actual competent grant event and subsequent matching assessment. More factual evidence cannot create that grant.

## 8 Courses of action and constraints across work

CourseOfAction is a finite directed acyclic graph of proposed steps. Each step has an ActionCase revision, dependencies, observation guards, required inputs, proposed effects, resources, duties and affected-interest scope. The plan states its objective, candidate-domain coverage and comparison policy.

Assess every step, every relevant branch and the combined course. Check whether predecessor effects are actually available at a successor or merely assumed in a scenario. A permission to perform a step is not evidence that the step succeeded. A proposed authorization or consent step stays hypothetical until an actual competent event supports it.

Composition checks cumulative data scope, limits, legal effects, incompatible consents, shared resources and residual duties. Several individually supported steps may form an unsupported course. Splitting a course across actors or UoWs does not remove aggregate constraints.

A contingent branch may use only an observation available to its deciding actor at that step's local frontier. A strategy cannot select its branch using a hidden future condition. The initial search compares supplied candidate courses; it does not implement unrestricted automatic planning.

compare_courses consumes a CourseSet, AssessmentContext, CourseComparisonPolicy and EvaluationBudget. v0.1 uses a display_only comparison policy: it returns each course's legal assessment, conditions, declared costs or effort when supplied, ties or unassessed comparability, coverage and exact evaluated and unassessed counts. It does not compute a preferred, optimal or dominant course. A future ranking policy requires its own reviewed objective, comparable measures and qualification. Adding a course or changing a step or comparison policy changes the course-set digest.

Where a resource or legal allowance is shared, an explicit owner or allocation protocol provides reservation and consumption evidence. A participant's incomplete local record does not prove global availability. Cancellation request or receipt does not release a reservation. Release requires its own authorized application evidence and retention of residual duties.

The model can compare unconventional arrangements under the same reviewed rules. Novelty is metadata. Feasibility, expected effectiveness, tertiary effects and legality remain distinct findings with their own evidence.

## 9 UoW and time integration

### Separate assessment work from the assessed act

An analysis UoW can validly produce a report that the subject action is prohibited or unresolved. For work_kind assess_case, enumerate_actions, enumerate_actors, assess_course or compare_courses, admission governs the analyst's access, analysis, retention and dissemination. It does not require a favorable legal finding about the subject.

AuthorityWorkProposal binds a discriminated WorkSubject: the complete ActionCase for assess_case and execute_assessed_action, the query and full CandidateDomain for enumeration, one CourseOfAction for assess_course, or the entire CourseSet and comparison policy for compare_courses. The subject and context digests enter the operational proposal scope and digest. A representative first case cannot bind a larger domain. Domain expansion, an added course, a changed step or a changed comparison policy requires successor admission in v0.1.

For work_kind execute_assessed_action, future operational use would require a supported actual LegalAssessment, exact case and proposal binding, separate actual admission, resource commitments, duties and an enforcement contract. This release can validate that entry contract in an isolated local harness, but has no external executor.

The UoW bridge never manufactures a grant view from a LegalAssessment. It consumes independently established operational authority. The legacy checker can be used only for its faithful exact-proposal compatibility slice. Unsupported projection is explicit.

### Clock identity and knowledge

Authority actor identity, UoW identity and clock-stream identity are distinct. A stream is a declared tuple of history domain, epoch and local stream owner. The history domain names the UoW or an explicitly declared local history. Counters from different streams establish no order.

Reuse or adapt the proposed canonical clock codec only after inspecting the actual host validation. The known delimiter-overlap pair must remain distinct. Namespace event identities and parent endpoints separately. Do not substitute a clock-encoded actor for a legal actor in every record. [S5]

relate_events reports causal order only: one stream's local sequence or actual causal parent links. Invalid causal cycles and unresolved referenced parent records in a required complete snapshot are diagnosed before publication. A well-formed pair without a justified relation returns unknown, not proof of independence. compare_legal_reference separately evaluates a ReferenceTimeMapping for legal interval applicability. Chronological or legal-reference precedence never creates causal receipt, information availability, a message edge or a shared counter.

Legal source dates, legal effect intervals, occurrence evidence and local receipt frontiers remain separate. Relating a legal interval to an occurrence requires an explicit reviewed reference-time mapping or attestation. An unrelated local counter cannot establish expiry. The deciding boundary records its freshness protocol and knowledge limit; it never claims globally simultaneous revocation awareness.

Late evidence may support a new assessment of an earlier occurrence. It must not backdate receipt, extend a grant, rewrite an earlier admission or erase prior uncertainty.

## 10 Storage and host integration

Use a versioned Catalog extension against the pinned v0.3 catalog, with explicit semantic validators for the new records. Use a local SQLite store for successor analytical records, source and review references, dependency indexes and audit events. Published revisions are immutable; corrections append successors.

Write one result and all its required links atomically. A failed validation or interrupted transaction leaves no partially published assessment. Enforce unique record ID and revision, proposal and context digest bindings, and source-layer restrictions. Local transactional serialization does not create a shared clock among UoWs.

Publication validates and writes the root plus its required fresh derived records in one transaction. The stored logical records omit transport closures. Missing material derivations and normalized-payload collisions are rejected before publication. This allows the same read-only result to be inspected, serialized or explicitly published without changing its logical content.

AccessContext is supplied through the host's existing admission and audience controls. The package does not infer reader entitlement from the actor being analyzed. Explanation access follows its evidence and audience constraints; a public summary can reference restricted support without disclosing protected source details.

GraphProjection maps an explicitly permitted host snapshot to ActionCase and AssessmentContext records. Each projected field retains its source attribute, host record revision, mapping rule and semantic status. Unknown identities, unsupported relationships and ambiguous operation mappings remain explicit. No host graph node or actual lifecycle record is changed by projection.

Gate G0 captures the actual host import interface in host_mapping_contract.json before creating the successor adapter. The planned successor file is experiments/intelligence_integration/v0_2/authority_adapter.py. It wraps a named inspected host interface; it must not invent the v0.1 adapter's API from a report.

Reassessment pins case, context, registry, rule pack, source, review, coverage, evidence and frontier dependencies. New potentially applicable sources or newly affected interests can trigger reassessment even when absent from the old dependency graph. A pinned replay reproduces the old context; current reuse requires the successor context. Cache keys include the complete relevant context digest.

## 11 Finite limits

The initial qualification profile fixes the following configurable limits. They are design limits, not measured throughput claims. Changing them requires a profile revision and boundary checks.

| Dimension | v0.1 limit | On exhaustion |
| --- | --- | --- |
| Direct candidate bindings per enumeration | 4096 | Return partial candidates and remainder |
| Rules supplied in one assessment context | 1024 | Reject unsupported profile size before evaluation |
| Condition expression depth | 32 | context_or_model_error |
| Rule evaluations across one query UoW | 65536 | partial and unresolved remainder |
| Explicit context branches | 64 | Reject an undeclared truncated branch set |
| Nodes in one course | 8 | Unsupported course profile |
| Supplied candidate courses | 64 | Partial comparison with remainder |
| Delegation edges in one path | 16 | Unresolved path with depth diagnostic |
| Explanation nodes | 16384 | No positive result without its full decisive trace |

All counts refer to one declared query or course assessment. Budget consumption is deterministic and returned in the result. Check the last allowed item and the first disallowed item in qualification. No wall-clock timeout creates a substantive legal conclusion.

## 12 Qualification and release scope

The proposed campaign contains 56 named obligations and a separate 288-cell direct oracle: six actors by six affected actors by four operations by two fictional scope packs at one pinned snapshot. The 56 obligations include parameterized checks and eight additions covering evidence logic, uncertain exceptions, private liberty, hostile source instructions, shared allocations, branch quantifiers, transactional publication and input/profile boundaries.

The independent qualification owner freezes sources, rule formalizations, expected direct outcomes, reverse domains, case expectations and hashes before inspecting candidate implementation. The first failures are retained. Oracle changes require a reviewed specification or fixture amendment and never overwrite a disagreement.

Require exact agreement on every declared direct cell and mandatory obligation. Reverse queries must have no unsupported inclusion or unexplained omission within complete declared domains. A permanently unresolved implementation cannot pass because expected supported, prohibited and conditions-unmet cells must also match.

After mechanical gates, conduct a 30-case read-only pilot in one selected reviewed legal scope: 12 direct questions, eight reverse queries and ten course or historical traces. The pilot charter selects the applicable operation subset, source universe, reviewers and audience before cases are frozen. All real-source cases receive independent legal disposition. This sample is a workflow budget, not an accuracy estimate.

Legal review judges source selection, applicability, formalization, exception and priority handling, affected interests and coverage. Mechanical tests judge whether software implements those declared meanings. Pilot review judges intelligibility, traceability and useful next-work identification. Record review effort and observed runtime; do not claim a speed or analyst-performance improvement without a separately designed comparison.

Release requires zero unresolved critical implementation defects, all required mechanical gates, complete traceability for decisive findings, inspected host compatibility, and adjudication or explicit unresolved treatment of every pilot disagreement. Do not require a low unresolved rate. Close v0.1 when these conditions are met.

Additional jurisdictions, action meanings, normative recursion, distributed execution, automated collection, external grant issuance, field-effect claims and performance claims require successor scope and qualification.

## 13 Sources and design references

[S1] Intelligence qualification v0.3 README and qualification_report_v0_3.txt. Source manifest records exact hashes. These describe the finite reference, test counts and exclusions.

[S2] Intelligence qualification v0.3 docs/API_CONTRACT.txt and intel_uow/workflow.py. Relevant sections: assess_admission, blocker_resolution, event_relation and Workflow.

[S3] Intelligence qualification v0.3 intel_uow/catalog.py, grammar.py, analysis.py and the frozen architecture contract catalog. Relevant concepts: graph layers, immutable revisions, explicit interpretation and bounded analysis.

[S4] User-supplied Intelligence Integration v0.1 local report, Pasted text(20261009-232329).txt. Host integration claims are reported evidence until verified against the actual host.

[S5] Clock identity correction proposal v0.1.1 README, clock_identity.py and PACKAGE_MANIFEST.json. The correction is standalone; its actual host application remains to be checked.

[W1] OASIS. LegalRuleML Core Specification Version 1.0. OASIS Standard, 30 August 2021. https://docs.oasis-open.org/legalruleml/legalruleml-core-spec/v1.0/os/legalruleml-core-spec-v1.0-os.html

[W2] W3C. PROV-DM The PROV Data Model. Recommendation, 30 April 2013. https://www.w3.org/TR/prov-dm/

[W3] NIST. SP 800-162 Guide to Attribute Based Access Control Definition and Considerations. Updated publication page. https://csrc.nist.gov/pubs/sp/800/162/upd2/final

[W4] Office of the Director of National Intelligence. Intelligence Community Directive 203 Analytic Standards. https://www.dni.gov/files/documents/ICD/ICD-203.pdf
Design use: source quality, uncertainty, alternatives and explicit analytical reasoning. This plan makes no blanket compliance claim.

