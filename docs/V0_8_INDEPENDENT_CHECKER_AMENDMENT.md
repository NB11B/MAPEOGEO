# MAPEOGEO v0.8 — Independent Checker Tooling Amendment

## Status

This document amends **only the independent checker implementation** in the v0.8 verifier harness. It does not alter the frozen source bindings, Lean statements, formal scopes, EO/GEO graph relations, source hashes, acceptance thresholds, or the requirement that all four declarations compile without proof escape hatches.

The original preregistered specification named `nanoda` as the independent type-checking backstop.

## Why the implementation is amended

The preregistered Nanoda path was actually attempted on the pinned Lean/Mathlib `v4.33.1` environment.

The Lean kernel build succeeded for all four source-bound formal declarations. The environment export used by `nanoda` then produced approximately **6.07 GB** and **107.8 million lines**. The current Nanoda/debug checker failed while parsing that export with:

```text
Error: invalid digit found in string
```

This occurred after successful Lean compilation and before Nanoda could report a theorem/type-checking judgment. It is therefore recorded as **TOOLING_BLOCKED**, not PASS and not a mathematical/formalization failure.

A preceding Nanoda attempt also exposed a module-name detection incompatibility with the current Lake TOML layout; that harness issue was repaired before the 6.07 GB export attempt. Neither issue required changing a theorem statement or proof.

## Accepted independent checker substitution

For the accepted v0.8 run, the independent backstop is Lean's bundled `leanchecker`, invoked through pinned `leanprover/lean-action` v1.5.0.

The action documents `leanchecker` as an environment checker distinct from normal `lake build`; Lean `v4.33.1` is new enough to use the bundled checker. The accepted harness therefore requires both:

1. ordinary Lean/Mathlib build and kernel checking; and
2. `leanchecker` success.

The no-escape-hatch audit remains unchanged: no `sorry`, `admit`, custom `axiom` declaration, or `unsafe` declaration is allowed in the project formalization.

## Scientific-integrity rule

The original preregistration remains in repository history. This amendment is explicitly post-preregistration and is justified by an external checker/exporter compatibility failure observed only after the Lean proofs had already compiled.

No formal theorem, source hash, formal scope, graph promotion rule, or MAP scientific claim is changed by this substitution.

Nanoda remains useful for a future narrower-export or compatibility audit, but v0.8 will not block the MAP formal-verifier bridge on an external parser's inability to consume the current full Mathlib export.
