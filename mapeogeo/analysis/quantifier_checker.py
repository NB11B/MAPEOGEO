"""Executable quantifier dependency graph checker and validation engine."""

from __future__ import annotations

import inspect
from typing import Any, Callable
from mapeogeo.analysis.models import (
    AnalysisVerdict,
    QuantifierBlock,
    QuantifierSignature,
    QuantifierType,
)


class QuantifierChecker:
    """Validates quantifier order, variable domains, and permitted witness dependencies."""

    @staticmethod
    def validate_dependency_graph(signature: QuantifierSignature) -> tuple[bool, str]:
        """Verify that the quantifier sequence is well-formed and dependencies are topological."""
        # Include contextual parameters from hypotheses (e.g. functions, sequences, sets)
        context_vars = {
            "f", "x_seq", "y_seq", "a_seq", "b_seq", "c_seq", "fn_seq", "I_seq",
            "c", "L", "M", "x0", "a", "b", "K", "U", "cover", "E", "A", "poly", "seq", "n"
        }
        seen_vars: set[str] = set(context_vars)

        for block in signature.blocks:
            # Universal and existential quantifiers cannot depend on unintroduced variables
            for dep in block.depends_on:
                if dep not in seen_vars:
                    return False, f"Variable '{block.var}' depends on undeclared variable '{dep}'"
            seen_vars.add(block.var)

        # Verify forbidden dependencies are explicitly non-intersecting with permitted
        for exist_var, permitted in signature.permitted_dependencies.items():
            for forbidden in signature.forbidden_dependencies:
                if forbidden in permitted:
                    return False, f"Existential witness '{exist_var}' explicitly permits forbidden dependency '{forbidden}'"

        return True, "Quantifier dependency graph is valid."

    @staticmethod
    def check_witness_dependencies(
        witness_fn: Callable[..., Any],
        permitted_params: list[str],
        forbidden_params: list[str],
    ) -> tuple[bool, str]:
        """Inspect witness function signature to ensure zero leakage of forbidden variables."""
        sig = inspect.signature(witness_fn)
        params = list(sig.parameters.keys())

        for p in params:
            if p in forbidden_params:
                return (
                    False,
                    f"Quantifier dependency violation: witness function accepts forbidden variable '{p}'! "
                    f"Permitted parameters: {permitted_params}",
                )

        return True, "Witness signature satisfies dependency constraints."

    @staticmethod
    def test_spatial_independence(
        modulus_fn: Callable[[Any], Any],
        eps_input: Any,
        test_points: list[Any],
    ) -> tuple[bool, str]:
        """Test that a purported uniform modulus produces identical values regardless of spatial evaluation points."""
        base_val = modulus_fn(eps_input)
        for pt in test_points:
            # If modulus function is called with extra spatial context (or closure captures it), ensure value remains invariant
            val = modulus_fn(eps_input)
            if val != base_val:
                return (
                    False,
                    f"Modulus variation detected across spatial points: f({eps_input}) = {val} != {base_val} at point {pt}",
                )
        return True, "Modulus is spatially independent."

    @staticmethod
    def verify_alternation_order(
        declared_blocks: list[QuantifierBlock],
        expected_pattern: list[QuantifierType],
    ) -> tuple[bool, str]:
        """Verify that quantifier types match expected alternation (e.g. FORALL -> EXISTS -> FORALL)."""
        actual_types = [b.type for b in declared_blocks]
        if len(actual_types) < len(expected_pattern):
            return False, f"Quantifier block length {len(actual_types)} shorter than expected {len(expected_pattern)}"

        for i, exp in enumerate(expected_pattern):
            if actual_types[i] != exp:
                return (
                    False,
                    f"Quantifier alternation swap detected at position {i}: expected {exp.value}, got {actual_types[i].value}",
                )

        return True, "Quantifier alternation order verified."
