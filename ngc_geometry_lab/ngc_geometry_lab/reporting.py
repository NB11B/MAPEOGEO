"""Human-readable report generated from the measured campaign results."""


def markdown_report(result):
    gates = result['gates']
    lines = ['# NGC / MAPEOGEO geometric reconstruction qualification', '',
             f"**Result: {'PASS' if result['qualified'] else 'FAIL'} — {sum(g['passed'] for g in gates)}/{len(gates)} computational gates passed.**",
             f"Master seed: `{result['seed']}`. All observations in this campaign are synthetic. Computation uses CPU arithmetic.", '',
             '| Gate | Result | Criterion |', '|---|---|---|']
    lines += [f"| {g['id']} | {'PASS' if g['passed'] else 'FAIL'} | {g['criterion']} |" for g in gates]
    if not result['qualified']:
        lines += ['', '## Failures are retained', '',
                  'Read `results.json`, stage checkpoints, and any exception files. A failed campaign is not replaced with a success summary.',
                  '', 'The complete source and input records remain available for investigation.']
        return '\n'.join(lines)+'\n'
    e = result['experiments']
    c,m,q,d,f,r,j,i = [e[k] for k in ('exact_closure','metric_and_center','single_qubit','dual_lane','finite_shot','readout','joint','identifiability')]
    b = e['connected_operators']['upstream_baseline']
    lines.append(f'''
## What this establishes

The connected operator implementation can support a concrete reconstruction-and-prediction chain. The experiment executes actual pinned MAPEOGEO operators and the actual NGC real dual-lane backend. A separate real geometric model and a separately implemented complex density-matrix reference agree within the fixed absolute tolerance. Counts can be used to calibrate a declared detector model, recover an unknown state, and predict measurements after new operation sequences.

This is a computational result about the stated representations and assumptions. It does not identify a unique physical cause, derive the measurement probability law, demonstrate a physical Bell violation, or establish a quantum computational speedup.

## 1. Connected MAPEOGEO operators and a fresh exact closure

The imported `fuse(A,B)` executes A followed by B and returns B times A. The qualification independently checks this order, projection rank and nullity, equality after an observation, and initial-state recovery through an operation sequence. MAPEOGEO's inverse API retains `source_identified=False` even when coordinates are uniquely recovered. The distinction is part of the executable source behavior.

The new exact closure uses three explicitly supplied integer matrices: a 90-degree rotation about x, a 90-degree rotation about z, and projection onto the xy plane. Composition executes MAPEOGEO's actual matrix multiplication. Breadth-first enumeration begins with identity. Independent integer NumPy products check every multiplication-table entry, and a separate enumeration of signed partial permutations checks the resulting family.

| Measured property | Result |
|---|---:|
| Elements | {c['size']} |
| Rank 0 / 1 / 2 / 3 | {c['rank_histogram']['0']} / {c['rank_histogram']['1']} / {c['rank_histogram']['2']} / {c['rank_histogram']['3']} |
| Invertible elements | {len(c['units'])} |
| Idempotents | {len(c['idempotents'])} |
| Nilpotents, including zero | {len(c['nilpotents'])} |
| Elements in center | {len(c['center'])} |
| Commuting ordered pairs, including self-pairs | {c['commuting_ordered_pairs']} |
| Distinct commuting pairs without order | {(c['commuting_ordered_pairs']-c['size'])//2} |
| Independent product comparisons | {c['validation']['product_comparisons']:,} |
| Associativity triples | {c['validation']['associativity_triples']:,} |
| Product / associativity mismatches | {c['validation']['product_mismatches']} / {c['validation']['associativity_mismatches']} |

This is newly computed evidence for these generators. It is not represented as recovery of the historical sealed 115-element artifact. Matrix indices and shortest words depend on generator choice and enumeration order. `exact_closure.json` contains every matrix, generator word, table entry, and classification needed to inspect or reproduce this result.

## 2. Recovering a metric and a common center

Metric reconstruction solves the declared isometry equations R-transpose G R = G and projection self-adjointness equations P-transpose G = G P. It does not demand that a projection preserve every length.

A deliberately distorted coordinate basis provides a known nonidentity metric. The operator constraints recover it uniquely up to scale. Trace normalization fixes the reporting convention; it does not recover an absolute physical length scale.

- Maximum metric-entry error: **{m['max_metric_error']:.3e}**.
- Maximum reconstructed common-center error: **{m['center_max_error']:.3e}**.
- Insufficient constraints: **{m['insufficient_metric_status']}**.
- Contradictory isometry constraints: **{m['contradictory_metric_status']}**.
- Numerically unresolved, highly distorted SPD example: **{m['ill_conditioned_spd_status']}**.
- Four affine tetrahedron face projections: **{m['tetrahedral_face_projections_common_center_status']}** as a common-fixed-point system.

That last control matters: a point used as a common input to four projections need not be fixed by all four. A reconstructed geometric center also does not identify a common historical cause. The code keeps those claims separate.

The metric procedure is deliberately incomplete for positive-definite feasibility when the symmetric solution space has multiple dimensions. It attempts a particular SPD witness and reports unresolved feasibility if that search fails. Near-zero eigenvalues also remain unresolved at the chosen tolerance. Failure to find a numerically stable witness is not used as proof that no metric exists.

## 3. Tetrahedral reconstruction and held-out transformations

The four directions are (+++), (+--), (-+-), (--+), divided by sqrt(3). The candidate uses p_i=(1+n_i dot r)/4 and reconstructs r=3 sum_i p_i n_i. This is an explicit correspondence to a standard tetrahedral qubit measurement. The user's broader projected-tetrahedron hypothesis is not presumed identical to this correspondence.

The independent reference computes probabilities from density-matrix traces against four POVM effects. Its rotations use complex 2-by-2 unitaries; the geometric model uses real Rodrigues rotations.

| Test | Measured result |
|---|---:|
| Pure / mixed states | {q['pure_states']} / {q['mixed_states']} |
| Maximum reconstructed coordinate error | {q['max_state_error']:.3e} |
| Maximum direct probability disagreement | {q['max_probability_error']:.3e} |
| Held-out rotation predictions | {q['rotation_predictions']:,} |
| Maximum held-out probability disagreement | {q['max_prediction_error']:.3e} |
| Mean error after mismatching outcome labels and operator frame | {q['wrong_label_control_mean_error']:.6f} |

The one-hot distribution (1,0,0,0) reconstructs to a Bloch vector of norm 3 and is rejected as a qubit state. The state-space restriction is a substantive model assumption. Four nonnegative numbers summing to one are not automatically a physical qubit tetrahedral distribution.

## 4. Observation and detector calibration

The detector is modeled as a fixed column-stochastic 4-by-4 response matrix acting on ideal tetrahedral probabilities. The fit uses only {f['calibration_preparations']} calibration preparations with known coordinates. The response is frozen before processing {f['heldout_preparations']} unknown preparations. Every preparation and verification record contains {f['counts_per_record']:,} counts, for {f['total_observed_counts']:,} sampled synthetic outcomes across 280 records in total.

Verification represents a fresh identically prepared ensemble after the specified operations. It is not a second measurement of the same system after a destructive initial measurement. The generator uses only the independent complex reference. Ground truth is written to a separate evaluator file and is forbidden by the analyzer's input schema.

| Held-out measure | Result |
|---|---:|
| Mean calibrated Bloch-vector error | {f['mean_state_error']:.6f} |
| Mean error without detector correction | {f['mean_uncorrected_state_error']:.6f} |
| Maximum calibrated state error | {f['max_state_error']:.6f} |
| 95th percentile calibrated state error | {f['p95_state_error']:.6f} |
| Mean prediction TV distance from known synthetic truth | {f['mean_prediction_total_variation_vs_truth']:.6f} |
| Mean prediction TV distance from verification counts | {f['mean_verification_total_variation']:.6f} |
| Maximum fitted detector-entry error | {f['detector_max_entry_error']:.6f} |
| Estimates explicitly projected to the physical unit ball | {f['projected_estimates']} |

TV distance is half the sum of absolute differences between the four outcome probabilities. Bloch error is Euclidean distance in dimensionless state coordinates. The error gate was fixed at mean Bloch error below 0.035 before this campaign ran; it is an engineering qualification threshold for synthetic data, not a universal confidence guarantee.

Linear inversion can produce a vector slightly outside the physical ball because of count noise. The analyzer preserves the raw vector, its norm, the linear probability estimate, and the correction distance. Its reported physical estimate uses explicit radial projection. This estimator can be biased near the boundary; the correction is not hidden.

Calibration assumes known preparation coordinates, known tetrahedral axes, a stationary linear detector, and complete counts. Unknown axes, setting-dependent loss, detector nonlinearity, drift, and preparation errors require an extended instrument model or separately calibrated controls.

## 5. What the actual NGC dual lanes reproduce

The imported NGC backend updates two real components using q'=Aq-Bp and p'=Bq+Ap for a complex operator A+iB. It is an exact real representation of the same finite complex state space, up to floating-point arithmetic.

- **{d['gate_applications']:,} gate applications** across {d['circuits']} random circuits and one through six qubits.
- Nonadjacent and reversed target ordering included.
- Maximum state-amplitude disagreement: **{d['max_state_error']:.3e}**.
- Maximum measurement-probability disagreement: **{d['max_probability_error']:.3e}**.
- Maximum normalization error: **{d['max_norm_error']:.3e}**.

The backend is actual repository code; the comparison uses a separate tensor-axis implementation. The campaign makes no timing comparison. It runs on CPU and does not launch the CUDA kernel or demonstrate execution on two physical cores.

The full real state retains 2 times 2-to-the-n float64 entries. At six qubits that is 128 real entries, or 1024 bytes: the same state-storage size as 64 complex128 amplitudes. This result validates representation and operation, while leaving general state-space scaling intact.

## 6. Readout hypotheses

Sequential projections give zero direct transmission between crossed axes. Inserting a diagonal projection gives final amplitude norm 1/2 and squared weight **{r['inserted_diagonal_weight']:.12f}**. The squared-norm identification is explicitly adopted.

The separate readout experiment compares normalized power rules with exponents 1, 2, and 4. Fifteen calibration angles select a rule; nineteen distinct held-out angles score the frozen selection. The selected exponent is **{r['selected_exponent_on_calibration']}**. Raw angle counts and all candidate scores are retained.

The generator deliberately uses the squared rule. Recovering exponent 2 demonstrates that the procedure distinguishes these alternatives on this data. It does not independently derive the Born rule from geometry, and classical polarization intensities can exhibit the same projection law.

## 7. Joint systems and correlations

Two-system reconstruction uses local vectors a,b and a 3-by-3 correlation matrix C. Sixteen product-tetrahedron probabilities recover all 15 independent real coordinates. Retaining only the two local three-vectors would discard the nine correlation coordinates.

The geometric probability formula is compared with direct traces of a complex 4-by-4 density matrix. The campaign includes {j['states']} pure/mixed joint states and {j['rotation_predictions']:,} local-rotation predictions.

| Joint-system test | Result |
|---|---:|
| Maximum density reconstruction error | {j['max_density_error']:.3e} |
| Maximum direct probability disagreement | {j['max_probability_error']:.3e} |
| Maximum transformed probability disagreement | {j['max_prediction_error']:.3e} |
| Computed singlet CHSH magnitude | {j['singlet_chsh']:.12f} |
| Maximum over all 16 local deterministic assignments | {j['local_deterministic_max_chsh']} |
| Singlet versus maximally mixed joint TV distance | {j['singlet_vs_mixed_joint_total_variation']:.6f} |

The singlet and maximally mixed state have identical local marginals but different joint distributions. The CHSH comparison is a calculation of those models. A centralized program computing joint probabilities is not a physical local hidden-variable realization. No spacelike-separated physical measurements were performed.

Another control produces valid product-tetrahedron probabilities from C=I, a=b=0, yet the corresponding density matrix is not positive semidefinite. This prevents a valid-looking four-by-four probability table from being accepted as sufficient proof of a quantum state.

## 8. Identifiability and common output

Repeating or mirroring one observation direction gives rank **{i['duplicate_and_mirror_rank']}**. A declared operation sequence gives rank **{i['dynamic_sequence_rank']}**. A pair of states has exactly the same initial selected output, then a permitted rotation creates an output separation of **{i['after_permitted_rotation_difference']:.6f}**.

Thus a common observation can define an equivalence class of candidate states. Changing operations can make that class smaller. Identical output alone does not identify one unique source or cause, even though the operator model can recover useful relationships.

## Source and test integrity

Verified **{e['source_integrity']['verified_files']} pinned source/evidence files** using SHA-256 and Git blob SHA-1. NGC_Real is pinned to commit 3d9e8ffed3811c9a9f043a6eed30a7a23e18bcab. MAPEOGEO operator algebra is pinned to ac63dde9da6dca2c000aa53ee6ffb9365e2388a1; its selected observability modules are pinned to 2e12009413488f34c8d7e411f3239d240ce19ade. Full URLs and per-file hashes are in the bundled source manifests.

The selected unchanged upstream baseline tests produced **{b['passed']} passes and {b['failed']} failure**. The failure is retained. Its expected answer is incorrect for the supplied observation: AB differs from BA, but the selected second rows PAB and PBA are both (0,2). Independent integer multiplication confirms that the operator's equivalence result is correct. There were **{b['unexpected_failures']} unexpected baseline failures**. These counts refer to selected bundled tests, not every test in each upstream repository.

The inspected historical release branch contains placeholder/mock transformation artifacts; those were not used as closure evidence. The original sealed 115-element artifact was not located. A separate suspected file-integrity mismatch was resolved exactly as LF-versus-CRLF line endings. The raw source, original test failure, correction calculation, and scoped source audit remain available. None of those historical files was silently repaired.

Independent review caught a metric-classification error at the positive-definite numerical boundary, a large-integer count-conversion error, and a nonfinite-output failure that could be hidden by a maximum-error reduction. It also found an omitted CUDA header in an early wheel. These defects were corrected with preserved regression evidence. The known upstream failure is recognized only at its exact pinned assertion site; other failures are unexpected. No pass threshold was relaxed.

The optional CUDA check has separate CPU boundary tests for phase-bin rounding, library failures, and corrupt output evidence. These tests do not execute a GPU. Native CUDA execution and physical measurements remain NOT_RUN in this campaign. `docs/CUDA_CHECK.md` supplies the build and execution instructions for the pinned source and header on a suitable host.

## Reproduce and use external measurements

From the extracted project directory:

```bash
python -m pip install -r requirements.txt
python -W error -m unittest discover -s tests -v
python -m ngc_geometry_lab run --seed {result['seed']} --out results/replay
python -m ngc_geometry_lab generate --out observations.json --truth-out truth.json
python -m ngc_geometry_lab analyze --input observations.json --out analysis.json
```

The generator labels its observations synthetic. For experimental records, follow `docs/EXPERIMENT_PROTOCOL.md`, preserve preparation and instrument metadata, and mark the provenance kind experimental. The same analyzer accepts the measured counts. Its output remains conditional on the declared instrument and state model.

The program refuses nonempty campaign output directories and existing output files. Use a new destination to preserve earlier evidence. `results.json` is deterministic for the seed/configuration and numerical environment; environment/time metadata lives separately in `manifest.json`. Floating-point last bits may differ across numerical-library/platform versions, so cross-platform comparisons should use the fixed tolerances as well as the recorded versions.

## Evidence files

- `results.json`: all gates, controls, measured summaries, upstream outcomes, and declared scope.
- `exact_closure.json`: the full fresh integer monoid, words, and multiplication table.
- `single_qubit.csv`, `dual_lane.csv`, `joint_systems.csv`: every transformation comparison.
- `finite_shot.csv`: every held-out reconstruction error and projection flag.
- `synthetic_observations.json`: analyzer input, containing no held-out truth.
- `synthetic_truth.json`: separate evaluator ground truth.
- `blind_analysis.json`: frozen calibration, raw estimates, corrections, and predictions.
- `readout_candidates.csv`: all candidate-rule scores; raw counts are also in `results.json`.
- `configuration.json`, stage checkpoints, and `manifest.json`: fixed settings and file integrity.

The result supports a precise constructive claim: these connected geometric representations can reconstruct and predict the tested finite systems. Further physical claims require independent measurements or distinctive predictions that separate competing physical models.
''')
    return '\n'.join(lines)+'\n'
