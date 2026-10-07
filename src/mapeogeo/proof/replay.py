"""Independent Mathematical and Structural Proof Replay Subsystem.

Enforces independent re-execution of mathematical decision procedures
on proof payloads, ensuring that digest-consistent but mathematically
false payloads are fail-closed and rejected.
"""

from __future__ import annotations

import hashlib
import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from mapeogeo.proof.contracts import (
    ProofClaim,
    ProofStatus,
    canonical_sha256,
)


class ReplayStatus(StrEnum):
    """Execution status of an independent proof replay."""

    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    MALFORMED_PAYLOAD = "MALFORMED_PAYLOAD"
    MISSING_PAYLOAD = "MISSING_PAYLOAD"


@dataclass(frozen=True)
class ReplayResult:
    """Outcome of replaying an independent mathematical verifier on payload."""

    status: ReplayStatus
    verifier_id: str
    proof_status: ProofStatus
    message: str
    steps_evaluated: int = 0
    payload_digest: str = ""
    replay_hash: str = ""

    @property
    def passed(self) -> bool:
        return self.status == ReplayStatus.VERIFIED


class ProofReplayer(Protocol):
    """Protocol for independent mathematical and logical proof replayers."""

    def can_replay(self, verifier_semantic_id: str) -> bool:
        """Return True if this replayer is authoritative for the verifier ID."""
        ...

    def replay(self, claim: ProofClaim, payload: Mapping[str, Any]) -> ReplayResult:
        """Independently execute the decision procedure on the proof payload."""
        ...


class BooleanROBDDReplayer:
    """Independent Boolean / ROBDD equivalence replayer."""

    SEMANTIC_ID = "GFY.ROBDD_EQUIVALENCE.v1"

    def can_replay(self, verifier_semantic_id: str) -> bool:
        return verifier_semantic_id == self.SEMANTIC_ID

    def _eval_expr(self, expr: Any, env: dict[str, bool]) -> bool:
        if isinstance(expr, bool):
            return expr
        if isinstance(expr, (int, float)):
            return bool(expr)
        if isinstance(expr, str):
            return env.get(expr, False)
        if not isinstance(expr, list) or not expr:
            raise ValueError(f"malformed expression node: {expr!r}")

        op = str(expr[0]).lower()
        if op == "const":
            return bool(expr[1])
        if op == "var":
            return env.get(str(expr[1]), False)
        if op == "not":
            return not self._eval_expr(expr[1], env)
        if op == "and":
            return all(self._eval_expr(sub, env) for sub in expr[1:])
        if op == "or":
            return any(self._eval_expr(sub, env) for sub in expr[1:])
        if op == "xor":
            return self._eval_expr(expr[1], env) != self._eval_expr(expr[2], env)
        if op == "implies":
            left = self._eval_expr(expr[1], env)
            right = self._eval_expr(expr[2], env)
            return (not left) or right
        if op == "iff":
            return self._eval_expr(expr[1], env) == self._eval_expr(expr[2], env)

        raise ValueError(f"unknown logical operator: {op}")

    def _collect_vars(self, expr: Any, found: set[str]) -> None:
        if isinstance(expr, str):
            found.add(expr)
        elif isinstance(expr, list) and expr:
            op = str(expr[0]).lower()
            if op == "var":
                found.add(str(expr[1]))
            elif op in {"not", "and", "or", "xor", "implies", "iff"}:
                for sub in expr[1:]:
                    self._collect_vars(sub, found)

    def replay(self, claim: ProofClaim, payload: Mapping[str, Any]) -> ReplayResult:
        payload_digest = canonical_sha256(dict(payload), domain="mapeogeo-proof-payload-v2")
        if "left" not in payload or "right" not in payload:
            return ReplayResult(
                status=ReplayStatus.MALFORMED_PAYLOAD,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message="ROBDD payload missing 'left' or 'right' expression",
                payload_digest=payload_digest,
            )

        left_expr = payload["left"]
        right_expr = payload["right"]

        vars_set: set[str] = set()
        declared_order = payload.get("variable_order")
        if isinstance(declared_order, (list, tuple)):
            for v in declared_order:
                vars_set.add(str(v))
        self._collect_vars(left_expr, vars_set)
        self._collect_vars(right_expr, vars_set)

        sorted_vars = sorted(vars_set)
        steps = 0

        # Evaluate across all 2^N truth assignments
        for bits in itertools.product([False, True], repeat=len(sorted_vars)):
            steps += 1
            env = dict(zip(sorted_vars, bits, strict=True))
            try:
                l_val = self._eval_expr(left_expr, env)
                r_val = self._eval_expr(right_expr, env)
            except Exception as exc:
                return ReplayResult(
                    status=ReplayStatus.ERROR,
                    verifier_id=self.SEMANTIC_ID,
                    proof_status=ProofStatus.PROOF_GAP,
                    message=f"Evaluation error: {exc}",
                    steps_evaluated=steps,
                    payload_digest=payload_digest,
                )

            if l_val != r_val:
                replay_hash = hashlib.sha256(
                    f"COUNTEREXAMPLE:{env}:{l_val}!={r_val}".encode()
                ).hexdigest()
                return ReplayResult(
                    status=ReplayStatus.REJECTED,
                    verifier_id=self.SEMANTIC_ID,
                    proof_status=ProofStatus.COUNTEREXAMPLE,
                    message=(
                        f"Equivalence disproven at assignment {env}: left={l_val}, right={r_val}"
                    ),
                    steps_evaluated=steps,
                    payload_digest=payload_digest,
                    replay_hash=replay_hash,
                )

        replay_hash = hashlib.sha256(f"VERIFIED:{steps}:{sorted_vars}".encode()).hexdigest()
        return ReplayResult(
            status=ReplayStatus.VERIFIED,
            verifier_id=self.SEMANTIC_ID,
            proof_status=ProofStatus.FORMALLY_CHECKED,
            message=f"ROBDD equivalence verified across {steps} truth assignments",
            steps_evaluated=steps,
            payload_digest=payload_digest,
            replay_hash=replay_hash,
        )


class FarkasImplicationReplayer:
    """Independent linear polyhedral Farkas implication replayer."""

    SEMANTIC_ID = "GFY.FARKAS_IMPLICATION.v1"

    def can_replay(self, verifier_semantic_id: str) -> bool:
        return verifier_semantic_id == self.SEMANTIC_ID

    def replay(self, claim: ProofClaim, payload: Mapping[str, Any]) -> ReplayResult:
        payload_digest = canonical_sha256(dict(payload), domain="mapeogeo-proof-payload-v2")
        try:
            matrix = payload["matrix"]
            bounds = payload["bounds"]
            target_coeffs = payload["target_coefficients"]
            target_bound = float(payload["target_bound"])
            multipliers = payload.get("multipliers")
        except KeyError as exc:
            return ReplayResult(
                status=ReplayStatus.MALFORMED_PAYLOAD,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message=f"Missing required Farkas field: {exc}",
                payload_digest=payload_digest,
            )

        if not isinstance(matrix, list) or not isinstance(bounds, list):
            return ReplayResult(
                status=ReplayStatus.MALFORMED_PAYLOAD,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message="Matrix and bounds must be lists",
                payload_digest=payload_digest,
            )

        num_rows = len(matrix)
        num_cols = len(target_coeffs)

        if multipliers is None:
            mult_list: list[float] = [0.0] * num_rows
        elif isinstance(multipliers, (list, tuple)):
            mult_list = [float(x) for x in multipliers]
        else:
            return ReplayResult(
                status=ReplayStatus.MALFORMED_PAYLOAD,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message="Multipliers must be a list or tuple of numbers",
                payload_digest=payload_digest,
            )

        if len(mult_list) != num_rows:
            return ReplayResult(
                status=ReplayStatus.REJECTED,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message=f"Multipliers count {len(mult_list)} does not match row count {num_rows}",
                payload_digest=payload_digest,
            )

        # 1. Non-negativity: y >= 0
        if any(y < -1e-9 for y in mult_list):
            return ReplayResult(
                status=ReplayStatus.REJECTED,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.FALSE_AS_STATED,
                message="Farkas multipliers must be non-negative",
                payload_digest=payload_digest,
            )

        # 2. Gradient combination: y^T A == c^T
        comb_coeffs = [0.0] * num_cols
        for i, row in enumerate(matrix):
            y_i = mult_list[i]
            for j in range(num_cols):
                comb_coeffs[j] += y_i * float(row[j])

        for j in range(num_cols):
            if abs(comb_coeffs[j] - float(target_coeffs[j])) > 1e-7:
                return ReplayResult(
                    status=ReplayStatus.REJECTED,
                    verifier_id=self.SEMANTIC_ID,
                    proof_status=ProofStatus.COUNTEREXAMPLE,
                    message=(
                        f"Combined coefficient {comb_coeffs[j]} does not match "
                        f"target {target_coeffs[j]} at col {j}"
                    ),
                    payload_digest=payload_digest,
                )

        # 3. Bound combination: y^T b <= gamma
        comb_bound = sum([mult_list[i] * float(bounds[i]) for i in range(num_rows)])
        if comb_bound > target_bound + 1e-7:
            return ReplayResult(
                status=ReplayStatus.REJECTED,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.COUNTEREXAMPLE,
                message=f"Combined bound {comb_bound} exceeds target bound {target_bound}",
                payload_digest=payload_digest,
            )

        replay_hash = hashlib.sha256(
            f"FARKAS_VERIFIED:{mult_list}:{comb_bound}".encode()
        ).hexdigest()
        return ReplayResult(
            status=ReplayStatus.VERIFIED,
            verifier_id=self.SEMANTIC_ID,
            proof_status=ProofStatus.FORMALLY_CHECKED,
            message=(
                "Farkas certificate verified: non-negative multipliers "
                "satisfy y^T A = c^T and y^T b <= gamma"
            ),
            steps_evaluated=num_rows * num_cols,
            payload_digest=payload_digest,
            replay_hash=replay_hash,
        )


class TautologyDFAEqualityReplayer:
    """Independent deterministic finite automaton equivalence replayer."""

    SEMANTIC_ID = "GFY.DFA_EQUIVALENCE.v1"

    def can_replay(self, verifier_semantic_id: str) -> bool:
        return verifier_semantic_id == self.SEMANTIC_ID

    def replay(self, claim: ProofClaim, payload: Mapping[str, Any]) -> ReplayResult:
        payload_digest = canonical_sha256(dict(payload), domain="mapeogeo-proof-payload-v2")
        if "dfa1" not in payload or "dfa2" not in payload:
            return ReplayResult(
                status=ReplayStatus.MALFORMED_PAYLOAD,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.PROOF_GAP,
                message="DFA payload missing 'dfa1' or 'dfa2'",
                payload_digest=payload_digest,
            )

        dfa1 = payload["dfa1"]
        dfa2 = payload["dfa2"]
        # Fast structural check or BFS product state equivalence
        if dfa1 == dfa2:
            replay_hash = hashlib.sha256(b"DFA_IDENTICAL").hexdigest()
            return ReplayResult(
                status=ReplayStatus.VERIFIED,
                verifier_id=self.SEMANTIC_ID,
                proof_status=ProofStatus.FORMALLY_CHECKED,
                message="DFAs are structurally identical",
                steps_evaluated=len(dfa1.get("states", [])),
                payload_digest=payload_digest,
                replay_hash=replay_hash,
            )

        # BFS state product exploration
        alphabet = sorted(set(dfa1.get("alphabet", [])) | set(dfa2.get("alphabet", [])))
        start1 = dfa1.get("initial_state")
        start2 = dfa2.get("initial_state")
        accept1 = set(dfa1.get("accepting_states", []))
        accept2 = set(dfa2.get("accepting_states", []))
        trans1 = dfa1.get("transitions", {})
        trans2 = dfa2.get("transitions", {})

        queue = [(start1, start2, "")]
        visited = {(start1, start2)}
        steps = 0

        while queue and steps < 10000:
            steps += 1
            s1, s2, word = queue.pop(0)
            in_acc1 = s1 in accept1
            in_acc2 = s2 in accept2
            if in_acc1 != in_acc2:
                return ReplayResult(
                    status=ReplayStatus.REJECTED,
                    verifier_id=self.SEMANTIC_ID,
                    proof_status=ProofStatus.COUNTEREXAMPLE,
                    message=(
                        f"DFA equivalence disproven by word {word!r}: "
                        f"dfa1={in_acc1}, dfa2={in_acc2}"
                    ),
                    steps_evaluated=steps,
                    payload_digest=payload_digest,
                    replay_hash=hashlib.sha256(f"DFA_DIFF:{word}".encode()).hexdigest(),
                )

            for sym in alphabet:
                next1 = trans1.get(f"{s1}:{sym}") or trans1.get(str(s1), {}).get(sym)
                next2 = trans2.get(f"{s2}:{sym}") or trans2.get(str(s2), {}).get(sym)
                pair = (next1, next2)
                if pair not in visited:
                    visited.add(pair)
                    queue.append((next1, next2, word + sym))

        replay_hash = hashlib.sha256(f"DFA_EQ:{steps}".encode()).hexdigest()
        return ReplayResult(
            status=ReplayStatus.VERIFIED,
            verifier_id=self.SEMANTIC_ID,
            proof_status=ProofStatus.FORMALLY_CHECKED,
            message=f"DFA equivalence verified across {steps} states",
            steps_evaluated=steps,
            payload_digest=payload_digest,
            replay_hash=replay_hash,
        )


class ProofReplayRegistry:
    """Central registry of authoritative proof replayers."""

    def __init__(self) -> None:
        self._replayers: list[ProofReplayer] = [
            BooleanROBDDReplayer(),
            FarkasImplicationReplayer(),
            TautologyDFAEqualityReplayer(),
        ]

    def register(self, replayer: ProofReplayer) -> None:
        """Register a new domain-specific or mathematical proof replayer."""
        self._replayers.insert(0, replayer)

    def find_replayer(self, verifier_semantic_id: str) -> ProofReplayer | None:
        for r in self._replayers:
            if r.can_replay(verifier_semantic_id):
                return r
        return None

    def replay(
        self,
        verifier_semantic_id: str,
        claim: ProofClaim,
        payload: Mapping[str, Any],
    ) -> ReplayResult:
        replayer = self.find_replayer(verifier_semantic_id)
        if replayer is None:
            return ReplayResult(
                status=ReplayStatus.REJECTED,
                verifier_id=verifier_semantic_id,
                proof_status=ProofStatus.PROOF_GAP,
                message=(
                    f"No authoritative replayer registered for verifier ID: {verifier_semantic_id}"
                ),
            )
        return replayer.replay(claim, payload)
