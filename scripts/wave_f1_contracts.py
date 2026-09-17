#!/usr/bin/env python3
"""MAPEOGEO Wave F1 — Statement-Bound Executable Contracts and Falsification Engine.

Provides exact, finite, decidable mathematical verification bound directly to
Wave F1 source declaration statement hashes:
  1. `logic.truth_table_exhaustive`: Exhaustive valuation tables for propositional logic.
  2. `combinatorics.inclusion_exclusion_exact`: Exact rational/integer PIE verification.
  3. `graph.eulerian_degree_parity`: Exact degree-parity and connectivity graph algorithms.
  4. `sets.finite_csb_bijection`: Exact Cantor-Schröder-Bernstein bijection constructor.

Zero-prose and closed-contract policy:
  - All contracts fail-closed.
  - Evidence binds exact subject IDs and statement SHA-256 hashes.
  - Mutation tests verify active falsification capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class WaveF1ContractEvidence:
    """Executable evidence for named, hash-bound Wave F1 declaration subjects."""

    contract_id: str
    contract_version: str
    subject_ids: tuple[str, ...]
    subject_hashes: tuple[tuple[str, str], ...]
    verifier_id: str
    certificate_class: str
    scope: str
    witnesses: tuple[dict[str, Any], ...]
    status: str
    evidence_digest: str

    @classmethod
    def create(
        cls,
        *,
        contract_id: str,
        contract_version: str,
        subject_ids: tuple[str, ...],
        subject_hashes: tuple[tuple[str, str], ...],
        verifier_id: str,
        certificate_class: str,
        scope: str,
        witnesses: tuple[dict[str, Any], ...],
        status: str,
    ) -> "WaveF1ContractEvidence":
        core = {
            "contract_id": contract_id,
            "contract_version": contract_version,
            "subject_ids": list(subject_ids),
            "subject_hashes": [list(item) for item in subject_hashes],
            "verifier_id": verifier_id,
            "certificate_class": certificate_class,
            "scope": scope,
            "witnesses": list(witnesses),
            "status": status,
        }
        return cls(
            evidence_digest=_canonical_digest(core),
            contract_id=contract_id,
            contract_version=contract_version,
            subject_ids=subject_ids,
            subject_hashes=subject_hashes,
            verifier_id=verifier_id,
            certificate_class=certificate_class,
            scope=scope,
            witnesses=witnesses,
            status=status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "subject_ids": list(self.subject_ids),
            "subject_hashes": [list(item) for item in self.subject_hashes],
            "verifier_id": self.verifier_id,
            "certificate_class": self.certificate_class,
            "scope": self.scope,
            "witnesses": list(self.witnesses),
            "status": self.status,
            "evidence_digest": self.evidence_digest,
        }


# =========================================================================
# Contract 1: Propositional Logic Exhaustive Truth Tables
# =========================================================================

def verify_propositional_tautology(
    var_names: list[str],
    eval_fn: Callable[[dict[str, bool]], bool],
) -> dict[str, Any]:
    """Exhaustively verify that eval_fn evaluates to True under all 2^n assignments."""
    n = len(var_names)
    if n > 16:
        raise ValueError(f"Truth table verification restricted to <= 16 variables (got {n})")
    total_assignments = 1 << n
    rows = []
    for bits in itertools.product([False, True], repeat=n):
        env = dict(zip(var_names, bits))
        val = bool(eval_fn(env))
        if not val:
            return {
                "is_tautology": False,
                "failing_assignment": {k: int(v) for k, v in env.items()},
                "evaluated_rows": len(rows) + 1,
                "total_rows": total_assignments,
            }
        rows.append(env)
    return {
        "is_tautology": True,
        "failing_assignment": None,
        "evaluated_rows": len(rows),
        "total_rows": total_assignments,
    }


def run_logic_truth_table_contract(
    subject_hashes: dict[str, str],
) -> WaveF1ContractEvidence:
    """Run exhaustive propositional tautology verifier."""
    target_ids = (
        "decl:OPEN_LOGIC:DEF:prop_valuation",
        "decl:OPEN_LOGIC:DEF:prop_tautology",
    )
    for tid in target_ids:
        if tid not in subject_hashes:
            raise ValueError(f"Missing subject hash for {tid}")

    witnesses = []

    # Witness 1: Law of Excluded Middle: A or (not A)
    lem_res = verify_propositional_tautology(
        ["A"],
        lambda env: env["A"] or (not env["A"]),
    )
    assert lem_res["is_tautology"]
    witnesses.append({"name": "law_of_excluded_middle", "vars": ["A"], "result": lem_res})

    # Witness 2: De Morgan's Law: not (A and B) <-> (not A or not B)
    demorgan_res = verify_propositional_tautology(
        ["A", "B"],
        lambda env: (not (env["A"] and env["B"])) == ((not env["A"]) or (not env["B"])),
    )
    assert demorgan_res["is_tautology"]
    witnesses.append({"name": "de_morgan_conjunction", "vars": ["A", "B"], "result": demorgan_res})

    # Witness 3: Modus Ponens Tautology: (A and (A -> B)) -> B
    mp_res = verify_propositional_tautology(
        ["A", "B"],
        lambda env: (not (env["A"] and ((not env["A"]) or env["B"]))) or env["B"],
    )
    assert mp_res["is_tautology"]
    witnesses.append({"name": "modus_ponens_tautology", "vars": ["A", "B"], "result": mp_res})

    # Witness 4: Contrapositive: (A -> B) <-> (not B -> not A)
    contra_res = verify_propositional_tautology(
        ["A", "B"],
        lambda env: (((not env["A"]) or env["B"]) == (((not (not env["B"])) or (not env["A"]))))
    )
    assert contra_res["is_tautology"]
    witnesses.append({"name": "contraposition", "vars": ["A", "B"], "result": contra_res})

    return WaveF1ContractEvidence.create(
        contract_id="contract:f1:logic_truth_table_exhaustive",
        contract_version="1.0.0",
        subject_ids=target_ids,
        subject_hashes=tuple((tid, subject_hashes[tid]) for tid in target_ids),
        verifier_id="scripts.wave_f1_contracts.run_logic_truth_table_contract",
        certificate_class="EXHAUSTIVE_FINITE_MODEL",
        scope="EXHAUSTIVE_BOOLEAN_TRUTH_TABLE",
        witnesses=tuple(witnesses),
        status="PASS",
    )


# =========================================================================
# Contract 2: Inclusion-Exclusion Exact Integer Verification
# =========================================================================

def compute_pie_union_cardinality(sets: list[set[Any]]) -> int:
    """Compute cardinality of union using the exact inclusion-exclusion alternating sum formula."""
    n = len(sets)
    if n == 0:
        return 0
    total = 0
    for k in range(1, n + 1):
        sign = 1 if (k % 2 == 1) else -1
        k_sum = 0
        for combo in itertools.combinations(range(n), k):
            inter = set.intersection(*(sets[i] for i in combo))
            k_sum += len(inter)
        total += sign * k_sum
    return total


def run_inclusion_exclusion_contract(
    subject_hashes: dict[str, str],
) -> WaveF1ContractEvidence:
    """Run exact arithmetic verification of Principle of Inclusion-Exclusion."""
    target_id = "decl:LEVIN_DISCRETE:THM:inclusion_exclusion"
    if target_id not in subject_hashes:
        raise ValueError(f"Missing subject hash for {target_id}")

    witnesses = []

    # Case 1: 3 sets with overlaps
    s1 = {1, 2, 3, 4, 5}
    s2 = {3, 4, 5, 6, 7, 8}
    s3 = {5, 6, 7, 9, 10}
    sets_3 = [s1, s2, s3]
    actual_union_3 = len(s1 | s2 | s3)
    pie_calc_3 = compute_pie_union_cardinality(sets_3)
    assert actual_union_3 == pie_calc_3 == 10
    witnesses.append({"case": "3_sets_overlapping", "actual": actual_union_3, "pie": pie_calc_3})

    # Case 2: 4 sets with pairwise and 3-way overlaps
    s_a = set(range(1, 21))
    s_b = set(range(10, 31))
    s_c = set(range(20, 41))
    s_d = set(range(5, 25))
    sets_4 = [s_a, s_b, s_c, s_d]
    actual_union_4 = len(s_a | s_b | s_c | s_d)
    pie_calc_4 = compute_pie_union_cardinality(sets_4)
    assert actual_union_4 == pie_calc_4 == 40
    witnesses.append({"case": "4_sets_dense_overlap", "actual": actual_union_4, "pie": pie_calc_4})

    # Case 3: 5 pairwise disjoint sets
    sets_disjoint = [{i} for i in range(5)]
    actual_disjoint = 5
    pie_disjoint = compute_pie_union_cardinality(sets_disjoint)
    assert actual_disjoint == pie_disjoint == 5
    witnesses.append({"case": "5_sets_disjoint", "actual": actual_disjoint, "pie": pie_disjoint})

    return WaveF1ContractEvidence.create(
        contract_id="contract:f1:inclusion_exclusion_exact",
        contract_version="1.0.0",
        subject_ids=(target_id,),
        subject_hashes=((target_id, subject_hashes[target_id]),),
        verifier_id="scripts.wave_f1_contracts.run_inclusion_exclusion_contract",
        certificate_class="EXACT_ARITHMETIC_VERIFICATION",
        scope="EXACT_FINITE_PIE_SUM",
        witnesses=tuple(witnesses),
        status="PASS",
    )


# =========================================================================
# Contract 3: Graph Eulerian Degree Parity & Connectivity Verifier
# =========================================================================

def check_eulerian_status(
    vertices: list[int],
    edges: list[tuple[int, int]],
) -> dict[str, Any]:
    """Check degree sum, connectivity, and Euler circuit/path characterization."""
    adj: dict[int, list[int]] = {v: [] for v in vertices}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    # Handshaking sum check
    degrees = {v: len(adj[v]) for v in vertices}
    degree_sum = sum(degrees.values())
    if degree_sum != 2 * len(edges):
        return {"valid": False, "reason": "Handshaking lemma violated"}

    # Connectedness (ignoring isolated vertices)
    active_vertices = [v for v in vertices if degrees[v] > 0]
    if not active_vertices:
        return {"valid": True, "has_euler_circuit": True, "has_euler_path": True, "odd_degrees": []}

    visited = set()
    queue = [active_vertices[0]]
    visited.add(active_vertices[0])
    while queue:
        curr = queue.pop(0)
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    is_connected = (len(visited) == len(active_vertices))
    odd_vertices = [v for v in vertices if degrees[v] % 2 == 1]

    has_circuit = is_connected and (len(odd_vertices) == 0)
    has_path = is_connected and (len(odd_vertices) in {0, 2})

    return {
        "valid": True,
        "is_connected": is_connected,
        "degree_sum": degree_sum,
        "edge_count": len(edges),
        "odd_vertex_count": len(odd_vertices),
        "odd_vertices": odd_vertices,
        "has_euler_circuit": has_circuit,
        "has_euler_path": has_path,
    }


def run_eulerian_graph_contract(
    subject_hashes: dict[str, str],
) -> WaveF1ContractEvidence:
    """Run graph degree parity and Eulerian traversal verification."""
    target_ids = (
        "decl:LEVIN_DISCRETE:THM:handshaking_lemma",
        "decl:LEVIN_DISCRETE:THM:euler_path_circuit",
    )
    for tid in target_ids:
        if tid not in subject_hashes:
            raise ValueError(f"Missing subject hash for {tid}")

    witnesses = []

    # Graph 1: K_5 (all vertices degree 4, even -> Euler circuit)
    k5_vertices = list(range(5))
    k5_edges = list(itertools.combinations(k5_vertices, 2))
    k5_status = check_eulerian_status(k5_vertices, k5_edges)
    assert k5_status["has_euler_circuit"] is True
    witnesses.append({"graph": "K_5_complete", "status": k5_status})

    # Graph 2: Bridges of Königsberg (vertices: 4, degrees: 3, 3, 3, 5 -> 4 odd vertices -> neither)
    konigsberg_vertices = [0, 1, 2, 3]
    konigsberg_edges = [
        (0, 1), (0, 1), # 2 bridges between 0 and 1
        (0, 2), (0, 2), # 2 bridges between 0 and 2
        (0, 3),         # 1 bridge between 0 and 3
        (1, 3),         # 1 bridge between 1 and 3
        (2, 3),         # 1 bridge between 2 and 3
    ]
    konigsberg_status = check_eulerian_status(konigsberg_vertices, konigsberg_edges)
    assert konigsberg_status["has_euler_circuit"] is False
    assert konigsberg_status["has_euler_path"] is False
    assert konigsberg_status["odd_vertex_count"] == 4
    witnesses.append({"graph": "konigsberg_multigraph", "status": konigsberg_status})

    # Graph 3: Open Euler path graph (2 odd vertices, e.g. path P_4)
    p4_vertices = [0, 1, 2, 3]
    p4_edges = [(0, 1), (1, 2), (2, 3)]
    p4_status = check_eulerian_status(p4_vertices, p4_edges)
    assert p4_status["has_euler_circuit"] is False
    assert p4_status["has_euler_path"] is True
    assert p4_status["odd_vertex_count"] == 2
    witnesses.append({"graph": "path_graph_P4", "status": p4_status})

    return WaveF1ContractEvidence.create(
        contract_id="contract:f1:eulerian_degree_parity",
        contract_version="1.0.0",
        subject_ids=target_ids,
        subject_hashes=tuple((tid, subject_hashes[tid]) for tid in target_ids),
        verifier_id="scripts.wave_f1_contracts.run_eulerian_graph_contract",
        certificate_class="DECISION_PROCEDURE_PROOF",
        scope="EULERIAN_DEGREE_PARITY_AND_CONNECTIVITY",
        witnesses=tuple(witnesses),
        status="PASS",
    )


# =========================================================================
# Contract 4: Finite Cantor-Schröder-Bernstein Bijection Constructor
# =========================================================================

def construct_finite_csb_bijection(
    set_a: set[Any],
    set_b: set[Any],
    f: dict[Any, Any], # injection A -> B
    g: dict[Any, Any], # injection B -> A
) -> dict[str, Any]:
    """Explicitly construct and verify the CSB bijection h: A -> B."""
    # Check injection preconditions
    if len(set(f.values())) != len(set_a) or set(f.keys()) != set_a:
        raise ValueError("f is not an injection from A to B")
    if len(set(g.values())) != len(set_b) or set(g.keys()) != set_b:
        raise ValueError("g is not an injection from B to A")

    # Invert g: g_inv maps g(b) -> b
    g_inv = {v: k for k, v in g.items()}
    g_b = set(g.values())

    # C_0 = A \ g(B)
    c_curr = set_a - g_b
    c_all = set(c_curr)

    # Compute C = Union_{n >= 0} (g o f)^n (A \ g(B))
    while c_curr:
        c_next = {g[f[x]] for x in c_curr}
        new_elements = c_next - c_all
        c_all.update(new_elements)
        c_curr = new_elements

    # Define h: A -> B: h(x) = f(x) if x in C else g_inv(x)
    h: dict[Any, Any] = {}
    for x in set_a:
        if x in c_all:
            h[x] = f[x]
        else:
            h[x] = g_inv[x]

    # Verify that h is a bijection A -> B
    is_injective = len(set(h.values())) == len(set_a)
    is_surjective = set(h.values()) == set_b
    is_bijection = is_injective and is_surjective

    return {
        "is_bijection": is_bijection,
        "c_chain_size": len(c_all),
        "domain_size": len(set_a),
        "codomain_size": len(set_b),
        "bijection_map": {str(k): str(v) for k, v in h.items()},
    }


def run_finite_csb_contract(
    subject_hashes: dict[str, str],
) -> WaveF1ContractEvidence:
    """Run exact verification of the CSB bijection constructor."""
    target_id = "decl:OPEN_SET_THEORY:THM:cantor_schroder_bernstein"
    if target_id not in subject_hashes:
        raise ValueError(f"Missing subject hash for {target_id}")

    witnesses = []

    # Witness 1: Finite sets of size 6 with non-trivial shifted injections
    set_a = {1, 2, 3, 4, 5, 6}
    set_b = {"a", "b", "c", "d", "e", "f"}
    # f: A -> B
    f = {1: "a", 2: "b", 3: "c", 4: "d", 5: "e", 6: "f"}
    # g: B -> A shifted
    g = {"a": 2, "b": 3, "c": 4, "d": 5, "e": 6, "f": 1}
    res1 = construct_finite_csb_bijection(set_a, set_b, f, g)
    assert res1["is_bijection"] is True
    witnesses.append({"case": "shifted_cyclic_6", "result": res1})

    # Witness 2: Identity injections
    set_a2 = {10, 20, 30}
    set_b2 = {100, 200, 300}
    f2 = {10: 100, 20: 200, 30: 300}
    g2 = {100: 10, 200: 20, 300: 30}
    res2 = construct_finite_csb_bijection(set_a2, set_b2, f2, g2)
    assert res2["is_bijection"] is True
    witnesses.append({"case": "identity_3", "result": res2})

    return WaveF1ContractEvidence.create(
        contract_id="contract:f1:finite_csb_bijection",
        contract_version="1.0.0",
        subject_ids=(target_id,),
        subject_hashes=((target_id, subject_hashes[target_id]),),
        verifier_id="scripts.wave_f1_contracts.run_finite_csb_contract",
        certificate_class="ALGORITHMIC_CONSTRUCTIVE_BIJECTION",
        scope="FINITE_CSB_BIJECTION_CONSTRUCTION",
        witnesses=tuple(witnesses),
        status="PASS",
    )


def execute_all_wave_f1_contracts(
    manifest_paths: list[Path] | None = None,
) -> dict[str, WaveF1ContractEvidence]:
    """Execute all 4 Wave F1 contracts against manifest statement hashes."""
    if manifest_paths is None:
        manifest_paths = [
            ROOT / "formal" / "open_logic_manifest_v0_21.json",
            ROOT / "formal" / "open_set_theory_manifest_v0_21.json",
            ROOT / "formal" / "levin_discrete_manifest_v0_21.json",
        ]

    subject_hashes: dict[str, str] = {}
    for p in manifest_paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        for d in data.get("declarations", []):
            subject_hashes[d["node_id"]] = d["statement_sha256"]

    c1 = run_logic_truth_table_contract(subject_hashes)
    c2 = run_inclusion_exclusion_contract(subject_hashes)
    c3 = run_eulerian_graph_contract(subject_hashes)
    c4 = run_finite_csb_contract(subject_hashes)

    return {
        c1.contract_id: c1,
        c2.contract_id: c2,
        c3.contract_id: c3,
        c4.contract_id: c4,
    }


def main() -> int:
    evidence_map = execute_all_wave_f1_contracts()
    print(f"Successfully executed {len(evidence_map)} Wave F1 statement-bound contracts:")
    for cid, ev in evidence_map.items():
        print(f"  - {cid}: {ev.status} ({len(ev.witnesses)} witnesses, digest={ev.evidence_digest[:12]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
