"""Planner-owned artifact identity and derivation lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .canonical import canonical_sha256
from .model import Artifact, ArtifactType, DerivationStep, RootOrigin, VerificationResult


@dataclass(frozen=True)
class DerivedOrigin:
    operator_id: str
    parents: tuple[tuple[str, str], ...]
    step_id: str


@dataclass(frozen=True)
class TrackedArtifact:
    instance_id: str
    artifact: Artifact
    origin: RootOrigin | DerivedOrigin
    root_input_keys: frozenset[str]
    derivation_step_ids: tuple[str, ...]
    ancestor_types: tuple[ArtifactType, ...]
    producer_objectives: tuple[str, ...] = ()


def _artifact_payload(artifact: Artifact) -> dict[str, object]:
    return {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "value": artifact.value,
        "metadata": artifact.metadata,
    }


def artifact_content_digest(artifact: Artifact) -> str:
    return canonical_sha256(_artifact_payload(artifact), domain="pct-artifact-content-v1")


def track_roots(inputs: Mapping[str, Artifact]) -> tuple[tuple[str, TrackedArtifact], ...]:
    rows: list[tuple[str, TrackedArtifact]] = []
    for key, artifact in sorted(inputs.items()):
        instance_id = "root:" + canonical_sha256(
            {"input_key": key, "artifact": _artifact_payload(artifact)},
            domain="pct-root-instance-v1",
        )
        origin = RootOrigin(key, instance_id, artifact.artifact_id, artifact_content_digest(artifact))
        rows.append(
            (
                key,
                TrackedArtifact(
                    instance_id=instance_id,
                    artifact=artifact,
                    origin=origin,
                    root_input_keys=frozenset((key,)),
                    derivation_step_ids=(),
                    ancestor_types=(),
                ),
            )
        )
    return tuple(rows)


def derive_artifact(
    *,
    operator_id: str,
    output: Artifact,
    bound_inputs: Mapping[str, TrackedArtifact],
    verifier: VerificationResult,
    objectives: Sequence[str] = (),
) -> tuple[TrackedArtifact, DerivationStep]:
    parents = tuple(sorted((port_id, tracked.instance_id) for port_id, tracked in bound_inputs.items()))
    instance_id = "derived:" + canonical_sha256(
        {
            "operator_id": operator_id,
            "parents": parents,
            "artifact": _artifact_payload(output),
        },
        domain="pct-derived-instance-v1",
    )
    step_id = "step:" + canonical_sha256(
        {
            "operator_id": operator_id,
            "parents": parents,
            "output_instance_id": instance_id,
            "verifier": verifier,
        },
        domain="pct-derivation-step-v1",
    )
    roots = frozenset().union(*(tracked.root_input_keys for tracked in bound_inputs.values()))
    prior_steps: list[str] = []
    ancestor_types: list[ArtifactType] = []
    for port_id in sorted(bound_inputs):
        tracked = bound_inputs[port_id]
        for prior in tracked.derivation_step_ids:
            if prior not in prior_steps:
                prior_steps.append(prior)
        ancestor_types.extend(tracked.ancestor_types)
        ancestor_types.append(tracked.artifact.artifact_type)
    tracked_output = TrackedArtifact(
        instance_id=instance_id,
        artifact=output,
        origin=DerivedOrigin(operator_id, parents, step_id),
        root_input_keys=roots,
        derivation_step_ids=tuple(prior_steps) + (step_id,),
        ancestor_types=tuple(ancestor_types),
        producer_objectives=tuple(objectives),
    )
    step = DerivationStep(
        step_id=step_id,
        operator_id=operator_id,
        input_bindings=parents,
        output_instance_id=instance_id,
        output_artifact_id=output.artifact_id,
        output_type=output.artifact_type,
        verifier=verifier,
        root_input_keys=roots,
    )
    return tracked_output, step
