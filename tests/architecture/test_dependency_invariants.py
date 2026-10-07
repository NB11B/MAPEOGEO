"""Architectural Dependency Invariant and Hygiene Tests.

Enforces:
1. Domain neutrality of the UoW kernel (kernel -/-> domains).
2. Domain neutrality of grammar and graph (grammar -/-> domains, graph -/-> domains).
3. Lexical and namespace hygiene (no historical generation tokens in canonical source).
4. Importability and presence of canonical subsystem packages.
5. Integrity and qualification schema of master provenance manifest and component records.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = REPO_ROOT / "src" / "mapeogeo"
KERNEL_ROOT = SRC_ROOT / "kernel"
GRAMMAR_ROOT = SRC_ROOT / "grammar"
GRAPH_ROOT = SRC_ROOT / "graph"
PSMSL_ROOT = SRC_ROOT / "psmsl"

# Forbidden physical claim tokens in shared PSMSL substrate
FORBIDDEN_PHYSICAL_TOKENS_IN_PSMSL = [
    "force",
    "energy",
    "mass",
    "sensor",
    "field",
    "physical_conservation",
]

# Forbidden historical tokens in canonical source imports, paths, and module names
FORBIDDEN_HISTORICAL_TOKENS = [
    "gen1",
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
    "wave_",
    "kernel_v",
    "experiment.",
    "portfolio_",
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


def _assert_no_domain_imports(subsystem_root: Path, subsystem_name: str) -> None:
    """Verify that no file under subsystem_root imports from mapeogeo.domains."""
    assert subsystem_root.is_dir(), f"{subsystem_name} directory missing at {subsystem_root}"

    violations: list[str] = []
    py_files = list(subsystem_root.rglob("*.py"))
    assert len(py_files) > 0, f"No python files found in {subsystem_name} directory"

    for py_file in py_files:
        imports = _get_imports_from_file(py_file)
        rel_path = py_file.relative_to(REPO_ROOT)
        for imp in imports:
            if "mapeogeo.domains" in imp or imp.startswith("domains"):
                violations.append(f"{rel_path}: imports forbidden domain module '{imp}'")

    assert not violations, f"Domain neutrality violation in {subsystem_name}:\n" + "\n".join(
        violations
    )


def test_kernel_domain_neutrality() -> None:
    """The UoW Kernel must NEVER import from any domain adapter."""
    _assert_no_domain_imports(KERNEL_ROOT, "UoW Kernel")


def test_grammar_domain_neutrality() -> None:
    """The Grammar layer must NEVER import from any domain adapter."""
    _assert_no_domain_imports(GRAMMAR_ROOT, "Grammar Layer")


def test_graph_domain_neutrality() -> None:
    """The Graph layer must NEVER import from any domain adapter."""
    _assert_no_domain_imports(GRAPH_ROOT, "Graph Layer")


def test_psmsl_domain_neutrality() -> None:
    """The PSMSL substrate must NEVER import from any domain adapter."""
    _assert_no_domain_imports(PSMSL_ROOT, "PSMSL Substrate")


def test_no_physical_claims_in_psmsl() -> None:
    """Physical claims (force, energy, mass, sensor, field) must not leak into PSMSL."""
    violations: list[str] = []
    py_files = list(PSMSL_ROOT.rglob("*.py"))
    assert len(py_files) > 0, "No python files found in PSMSL"

    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        rel_path = py_file.relative_to(REPO_ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id == "field":
                    continue  # standard library dataclasses.field
                id_lower = node.id.lower()
                for token in FORBIDDEN_PHYSICAL_TOKENS_IN_PSMSL:
                    if token in id_lower:
                        violations.append(
                            f"{rel_path}: identifier '{node.id}' contains token '{token}'"
                        )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name_lower = node.name.lower()
                for token in FORBIDDEN_PHYSICAL_TOKENS_IN_PSMSL:
                    if token in name_lower:
                        violations.append(
                            f"{rel_path}: definition '{node.name}' contains token '{token}'"
                        )

    assert not violations, "Physical domain leakage detected in PSMSL:\n" + "\n".join(violations)


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
        valid_statuses = ("PENDING_V2_QUALIFICATION", "QUALIFIED_CANONICAL_V2")
        assert comp["v2_qualification_status"] in valid_statuses, (
            f"Component '{cid}' must have valid qualification status: {comp['v2_qualification_status']}"
        )
        assert comp["source_repository"] == "NB11B/MAPEOGEO"
        assert len(comp["qualification_gate_requirements"]) >= 1

        # Check corresponding component file exists in docs/provenance/components/
        comp_file = components_dir / f"{cid}.json"
        assert comp_file.is_file(), f"Missing component record {comp_file}"

        comp_record = json.loads(comp_file.read_text(encoding="utf-8"))
        assert comp_record["component_id"] == cid
        assert comp_record["v2_qualification_status"] in valid_statuses
