# GEO-EULER-002 — Successor-derived prime generators
Prime labels are not supplied. A finite successor table defines addition by repeated successor and multiplication by repeated addition. Multiplicatively irreducible integers are those with no nontrivial factor-pair witness. A recursive graph traversal finds canonical factor multisets. Trial division is confined to an independent reference test.

**Local run:** 10/10 tests passed, domain 1..120, 30 recovered prime generators, 7381 recorded addition relations, 602 multiplication relations; all 120 integers reconstructed and unique canonical factor multisets.

**Boundaries:** successor labels, addition iteration, multiplication iteration and irreducibility definitions are engineered. Arithmetic integer bounds are enforced in generation. This is a finite computation, not a formal proof of unique factorization or Euler's infinite product, and not yet MAPEOGEO-native grammar synthesis. The generator-based infinite product and direct finite integer sum have different truncations.

Run `cd experiments/geo_euler_002 && python -m unittest discover -v && python experiment.py`.
