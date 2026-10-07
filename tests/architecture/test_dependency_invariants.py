"""Architectural Dependency Invariant and Hygiene Tests.

Enforces:
1. Domain neutrality of the UoW kernel (kernel -/-> domains).
2. Lexical and namespace hygiene (no historical generation tokens in canonical source).
3. Importability and presence of canonical subsystem packages.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = REPO_ROOT / "src" / "mapeogeo"
KERNEL_ROOT = SRC_ROOT / "kernel"

# Forbidden historical tokens in canonical source imports and module names
FORBIDDEN_HISTORICAL_TOKENS = [
    "gen2",
    "gen3",
    "gen4",
    "gen5",
    "gen6",
    "gen7",
    "gen8",
    "gen9",
    "gen10",
    "gen11",
    "gen12",
    "kernel_v3",
    "wave_f3",
    "wave_f4",
    "wave_f5",
    "experiment.",
]


def _get_imports_from_file(file_path: Path) -> list[str]:
    """Parse a Python file with AST and return all imported module paths."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)
            elif node.level > 0:
                # Relative import without explicit module name
                imported_modules.append(f".{'.' * (node.level - 1)}")

    return imported_modules


def test_kernel_domain_neutrality() -> None:
    """The UoW Kernel must NEVER import from any domain adapter.

    Invariance constraint:
        mapeogeo.kernel -/-> mapeogeo.domains
    """
    assert KERNEL_ROOT.is_dir(), f"Kernel directory missing at {KERNEL_ROOT}"

    violations: list[str] = []
    py_files = list(KERNEL_ROOT.rglob("*.py"))

    assert len(py_files) > 0, "No python files found in kernel directory"

    for py_file in py_files:
        imports = _get_imports_from_file(py_file)
        rel_path = py_file.relative_to(REPO_ROOT)
        for imp in imports:
            if "mapeogeo.domains" in imp or imp.startswith("domains"):
                violations.append(f"{rel_path}: imports forbidden domain module '{imp}'")

    assert not violations, "Domain neutrality violation detected in UoW Kernel:\n" + "\n".join(
        violations
    )


def test_no_historical_generation_tokens_in_canonical_source() -> None:
    """Canonical source in src/mapeogeo must NOT import historical artifacts
    or generation branches.
    """
    violations: list[str] = []
    py_files = list(SRC_ROOT.rglob("*.py"))

    assert len(py_files) > 0, "No python files found in src/mapeogeo"

    for py_file in py_files:
        rel_path = py_file.relative_to(REPO_ROOT)
        # Check filename itself
        for token in FORBIDDEN_HISTORICAL_TOKENS:
            if token.lower() in py_file.name.lower():
                violations.append(f"{rel_path}: filename contains forbidden token '{token}'")

        # Check imported modules
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            imp_lower = imp.lower()
            for token in FORBIDDEN_HISTORICAL_TOKENS:
                if token.lower() in imp_lower:
                    violations.append(
                        f"{rel_path}: imported module '{imp}' contains forbidden token '{token}'"
                    )

    assert not violations, (
        "Forbidden historical tokens detected in canonical source:\n" + "\n".join(violations)
    )


def test_canonical_subsystems_importable() -> None:
    """All canonical packages must be importable without syntax or initialization errors."""
    import mapeogeo
    import mapeogeo.domains
    import mapeogeo.domains.mathematics
    import mapeogeo.domains.physics
    import mapeogeo.domains.software
    import mapeogeo.grammar
    import mapeogeo.graph
    import mapeogeo.kernel
    import mapeogeo.proof
    import mapeogeo.psmsl
    import mapeogeo.routing

    assert hasattr(mapeogeo, "__version__")
    assert mapeogeo.__version__ == "2.0.0.dev1"


def test_canonical_package_structure() -> None:
    """Every canonical module directory must contain an __init__.py file."""
    expected_packages = [
        SRC_ROOT,
        SRC_ROOT / "kernel",
        SRC_ROOT / "grammar",
        SRC_ROOT / "graph",
        SRC_ROOT / "routing",
        SRC_ROOT / "proof",
        SRC_ROOT / "psmsl",
        SRC_ROOT / "domains",
        SRC_ROOT / "domains" / "mathematics",
        SRC_ROOT / "domains" / "physics",
        SRC_ROOT / "domains" / "software",
    ]
    for pkg in expected_packages:
        init_file = pkg / "__init__.py"
        assert init_file.is_file(), f"Missing __init__.py in {pkg}"


def test_provenance_manifest_and_component_records() -> None:
    """Verify master provenance manifest and component records adhere to v2 qualification rules."""
    import json

    manifest_file = REPO_ROOT / "artifacts" / "releases" / "V2_PROVENANCE_MANIFEST.json"
    assert manifest_file.is_file(), f"Missing master manifest at {manifest_file}"

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data.get("manifest_version") == "2.0.0"
    assert manifest_data.get("upstream_frozen_commit") == "74e51bd"
    assert manifest_data.get("canonical_base_commit") == "d664f8c"

    components = manifest_data.get("components", [])
    assert len(components) >= 8, f"Expected at least 8 registered components, got {len(components)}"

    components_dir = REPO_ROOT / "docs" / "provenance" / "components"
    assert components_dir.is_dir()

    for comp in components:
        cid = comp["component_id"]
        # Rule: Status must be PENDING_V2_QUALIFICATION for all unported/bootstrap components
        assert comp["v2_qualification_status"] == "PENDING_V2_QUALIFICATION", (
            f"Component '{cid}' must have status PENDING_V2_QUALIFICATION during Wave 2"
        )
        assert comp["source_repository"] == "NB11B/MAPEOGEO"
        assert len(comp["qualification_gate_requirements"]) >= 1

        # Check corresponding component file exists in docs/provenance/components/
        comp_file = components_dir / f"{cid}.json"
        assert comp_file.is_file(), f"Missing component record {comp_file}"

        comp_record = json.loads(comp_file.read_text(encoding="utf-8"))
        assert comp_record["component_id"] == cid
        assert comp_record["v2_qualification_status"] == "PENDING_V2_QUALIFICATION"
