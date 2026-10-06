from mapeogeo.erdos_campaign import classify


def test_graph_problem_routes_to_statement_inspection_not_solution_claim():
    d=classify("19","decidable",["graph theory","chromatic number"])
    assert d.outcome=="INSPECT_STATEMENT"
    assert "graph" in d.families


def test_number_theory_only_problem_fails_closed_to_capability_gap():
    d=classify("5","open",["number theory","primes"])
    assert d.outcome=="IMPLEMENT_OR_CERTIFY"


def test_resolved_problem_excluded():
    assert classify("4","proved",["number theory","primes"]).outcome=="EXCLUDE"


def test_geometry_overlap_is_candidate_only():
    d=classify("89","open",["geometry","distances"])
    assert d.outcome=="INSPECT_STATEMENT"
    assert d.reason.startswith("capability overlap")
