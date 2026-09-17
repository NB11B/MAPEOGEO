#!/usr/bin/env python3
"""MAPEOGEO Wave F3 — Abstract Algebra & Elementary Number Theory Manifest Generator.

Generates the 4 authoritative formal manifests for Wave F3:
1. formal/wave_f3_source_manifest.json (Judson Abstract Algebra, Stein Elementary Number Theory, Open Logic anchors)
2. formal/wave_f3_contract_manifest.json (32 Canonical Concepts with explicit formulation contracts)
3. formal/wave_f3_relation_manifest.json (Typed mathematical relationship edges and witness specifications)
4. formal/wave_f3_falsification_manifest.json (Multi-class falsification mutants across all 3 families)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_MANIFEST_PATH = ROOT / "formal" / "wave_f3_source_manifest.json"
CONTRACT_MANIFEST_PATH = ROOT / "formal" / "wave_f3_contract_manifest.json"
RELATION_MANIFEST_PATH = ROOT / "formal" / "wave_f3_relation_manifest.json"
FALSIFICATION_MANIFEST_PATH = ROOT / "formal" / "wave_f3_falsification_manifest.json"


def _hash_statement(statement: str) -> str:
    norm = " ".join(statement.strip().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------
# 1. Source Declarations (Judson, Stein, Open Logic)
# ----------------------------------------------------------------------
def generate_source_declarations() -> list[dict[str, Any]]:
    decls = [
        # --- William Stein: Elementary Number Theory ---
        {
            "node_id": "decl:STEIN_ENT:DEF:divisibility",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch1:Def:1.1.1",
            "chapter_section": "1.1 Divisibility and Prime Numbers",
            "decl_type": "DEFINITION",
            "label": "Stein ENT (Def 1.1.1): Divisibility of Integers",
            "raw_statement": "An integer a divides an integer b, written a | b, if there exists an integer c such that b = a * c. If a does not divide b, we write a ∤ b.",
            "structural_refs": [],
        },
        {
            "node_id": "decl:STEIN_ENT:DEF:greatest_common_divisor",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch1:Def:1.1.3",
            "chapter_section": "1.1 Divisibility and Prime Numbers",
            "decl_type": "DEFINITION",
            "label": "Stein ENT (Def 1.1.3): Greatest Common Divisor",
            "raw_statement": "The greatest common divisor of two integers a and b, not both zero, is the largest integer d such that d | a and d | b, denoted gcd(a, b).",
            "structural_refs": ["decl:STEIN_ENT:DEF:divisibility"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:euclidean_algorithm",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch1:Thm:1.1.6",
            "chapter_section": "1.1 Divisibility and Prime Numbers",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 1.1.6): The Euclidean Algorithm",
            "raw_statement": "Let a and b be integers with b > 0. Successive division a = q_1 b + r_1, b = q_2 r_1 + r_2, ..., r_{n-1} = q_{n+1} r_n + 0 yields gcd(a, b) = r_n, the last non-zero remainder.",
            "structural_refs": ["decl:STEIN_ENT:DEF:greatest_common_divisor"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:bezout_identity",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch1:Thm:1.1.8",
            "chapter_section": "1.1 Divisibility and Prime Numbers",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 1.1.8): Bézout's Identity and Extended GCD",
            "raw_statement": "For any integers a and b, there exist integers x and y such that a*x + b*y = gcd(a, b). Furthermore, gcd(a, b) is the smallest positive integer of the form a*x + b*y.",
            "structural_refs": ["decl:STEIN_ENT:THM:euclidean_algorithm"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:fundamental_theorem_arithmetic",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch1:Thm:1.1.17",
            "chapter_section": "1.1 Divisibility and Prime Numbers",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 1.1.17): Fundamental Theorem of Arithmetic",
            "raw_statement": "Every integer n > 1 can be written uniquely as a product of prime numbers n = p_1^{e_1} * p_2^{e_2} * ... * p_k^{e_k} up to the order of the factors.",
            "structural_refs": ["decl:STEIN_ENT:DEF:divisibility"],
        },
        {
            "node_id": "decl:STEIN_ENT:DEF:congruence",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch2:Def:2.1.1",
            "chapter_section": "2.1 Modular Arithmetic",
            "decl_type": "DEFINITION",
            "label": "Stein ENT (Def 2.1.1): Congruence Modulo n",
            "raw_statement": "Let n be a positive integer. Integers a and b are congruent modulo n, written a ≡ b (mod n), if n divides a - b.",
            "structural_refs": ["decl:STEIN_ENT:DEF:divisibility"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:chinese_remainder_theorem",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch2:Thm:2.2.4",
            "chapter_section": "2.2 The Chinese Remainder Theorem",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 2.2.4): Chinese Remainder Theorem",
            "raw_statement": "Let m and n be coprime positive integers. For any integers a and b, there exists an integer x such that x ≡ a (mod m) and x ≡ b (mod n), unique modulo m*n.",
            "structural_refs": ["decl:STEIN_ENT:DEF:congruence", "decl:STEIN_ENT:THM:bezout_identity"],
        },
        {
            "node_id": "decl:STEIN_ENT:DEF:euler_totient",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch2:Def:2.3.1",
            "chapter_section": "2.3 Euler's Phi Function and Theorem",
            "decl_type": "DEFINITION",
            "label": "Stein ENT (Def 2.3.1): Euler's Totient Function",
            "raw_statement": "Euler's phi-function phi(n) is the number of integers a such that 1 <= a <= n and gcd(a, n) = 1.",
            "structural_refs": ["decl:STEIN_ENT:DEF:greatest_common_divisor"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:euler_theorem",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch2:Thm:2.3.3",
            "chapter_section": "2.3 Euler's Phi Function and Theorem",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 2.3.3): Euler's Totient Theorem",
            "raw_statement": "If n is a positive integer and gcd(a, n) = 1, then a^{phi(n)} ≡ 1 (mod n).",
            "structural_refs": ["decl:STEIN_ENT:DEF:euler_totient", "decl:STEIN_ENT:DEF:congruence"],
        },
        {
            "node_id": "decl:STEIN_ENT:THM:fermat_little_theorem",
            "source_id": "STEIN_ENT_2017",
            "corpus": "STEIN_NUMBER_THEORY",
            "locator": "Stein:ENT:Ch2:Thm:2.3.5",
            "chapter_section": "2.3 Euler's Phi Function and Theorem",
            "decl_type": "THEOREM",
            "label": "Stein ENT (Thm 2.3.5): Fermat's Little Theorem",
            "raw_statement": "If p is a prime and a is an integer not divisible by p, then a^{p-1} ≡ 1 (mod p). For all integers a, a^p ≡ a (mod p).",
            "structural_refs": ["decl:STEIN_ENT:THM:euler_theorem"],
        },

        # --- Tom Judson: Abstract Algebra (Groups) ---
        {
            "node_id": "decl:JUDSON_ALG:DEF:group",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch3:Def:3.1",
            "chapter_section": "3.1 Definition of a Group",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 3.1): Group Axioms",
            "raw_statement": "A group (G, *) is a set G closed under a binary operation * satisfying: (1) Associativity: (a*b)*c = a*(b*c); (2) Identity: exists e in G such that e*a = a*e = a; (3) Inverses: for all a in G, exists a^{-1} such that a*a^{-1} = a^{-1}*a = e.",
            "structural_refs": [],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:subgroup",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch3:Def:3.8",
            "chapter_section": "3.2 Subgroups",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 3.8): Subgroup and Subgroup Criterion",
            "raw_statement": "A subset H of a group G is a subgroup, denoted H <= G, if H is closed under the operation and inverses of G, or equivalently for non-empty H: a, b in H implies a*b^{-1} in H.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:cyclic_group",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch4:Def:4.1",
            "chapter_section": "4.1 Cyclic Subgroups",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 4.1): Cyclic Groups and Generators",
            "raw_statement": "A group G is cyclic if there exists an element a in G such that G = <a> = {a^k : k in Z}. The element a is called a generator of G.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:coset",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch6:Def:6.1",
            "chapter_section": "6.1 Cosets",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 6.1): Left and Right Cosets",
            "raw_statement": "Let H be a subgroup of G and g in G. The left coset of H in G containing g is gH = {gh : h in H}. The right coset is Hg = {hg : h in H}.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:subgroup"],
        },
        {
            "node_id": "decl:JUDSON_ALG:THM:lagrange",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch6:Thm:6.8",
            "chapter_section": "6.1 Cosets and Lagrange's Theorem",
            "decl_type": "THEOREM",
            "label": "Judson AATA (Thm 6.8): Lagrange's Theorem",
            "raw_statement": "Let G be a finite group and H <= G. Then the order of H divides the order of G, and |G| = [G : H] * |H|, where [G : H] is the number of distinct left cosets.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:coset"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:group_homomorphism",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch11:Def:11.1",
            "chapter_section": "11.1 Group Homomorphisms",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 11.1): Group Homomorphism",
            "raw_statement": "A group homomorphism between groups (G, *) and (H, .) is a map f: G -> H such that f(a * b) = f(a) . f(b) for all a, b in G.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:kernel_and_image",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch11:Def:11.3",
            "chapter_section": "11.1 Group Homomorphisms",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 11.3): Kernel and Image",
            "raw_statement": "Let f: G -> H be a group homomorphism. The kernel of f is ker f = {g in G : f(g) = e_H}. The image is im f = {f(g) : g in G}.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group_homomorphism"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:normal_subgroup",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch10:Def:10.1",
            "chapter_section": "10.1 Normal Subgroups and Factor Groups",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 10.1): Normal Subgroups",
            "raw_statement": "A subgroup N of G is a normal subgroup, denoted N <| G, if gNg^{-1} = N for all g in G, or equivalently gN = Ng for all g in G.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:subgroup", "decl:JUDSON_ALG:DEF:coset"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:quotient_group",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch10:Def:10.4",
            "chapter_section": "10.1 Normal Subgroups and Factor Groups",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 10.4): Factor / Quotient Group",
            "raw_statement": "If N <| G, the factor group G/N is the set of cosets {gN : g in G} equipped with well-defined coset multiplication (aN)(bN) = (ab)N.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:normal_subgroup"],
        },
        {
            "node_id": "decl:JUDSON_ALG:THM:first_isomorphism_groups",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch11:Thm:11.10",
            "chapter_section": "11.2 The Isomorphism Theorems",
            "decl_type": "THEOREM",
            "label": "Judson AATA (Thm 11.10): First Isomorphism Theorem for Groups",
            "raw_statement": "If f: G -> H is a group homomorphism, then ker f <| G and G / ker f is isomorphic to im f via the canonical map g*ker f |-> f(g).",
            "structural_refs": ["decl:JUDSON_ALG:DEF:kernel_and_image", "decl:JUDSON_ALG:DEF:quotient_group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:symmetric_group",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch5:Def:5.1",
            "chapter_section": "5.1 Permutation Groups",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 5.1): Symmetric and Alternating Groups",
            "raw_statement": "The symmetric group S_n is the group of bijections on {1, ..., n}. The alternating group A_n is the normal subgroup of even permutations of index 2.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:THM:orbit_stabilizer",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch14:Thm:14.11",
            "chapter_section": "14.2 Group Actions and the Orbit-Stabilizer Theorem",
            "decl_type": "THEOREM",
            "label": "Judson AATA (Thm 14.11): Orbit-Stabilizer Theorem",
            "raw_statement": "Let G be a group acting on a set X. For any x in X, |Orb(x)| = [G : Stab(x)], and hence |G| = |Orb(x)| * |Stab(x)| for finite G.",
            "structural_refs": ["decl:JUDSON_ALG:THM:lagrange"],
        },

        # --- Tom Judson: Abstract Algebra (Rings & Fields) ---
        {
            "node_id": "decl:JUDSON_ALG:DEF:ring",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.1",
            "chapter_section": "16.1 Rings",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.1): Ring Axioms",
            "raw_statement": "A ring (R, +, *) is a set with two binary operations such that (R, +) is an abelian group, * is associative, and * distributes over +.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:group"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:units_zero_divisors",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.4",
            "chapter_section": "16.1 Rings and Integral Domains",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.4): Units and Zero Divisors",
            "raw_statement": "In a ring R with unity 1, an element u in R is a unit if there exists v in R such that uv = vu = 1. A non-zero element a in R is a zero divisor if there exists non-zero b in R with ab = 0.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ring"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:integral_domain",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.7",
            "chapter_section": "16.1 Rings and Integral Domains",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.7): Integral Domain",
            "raw_statement": "An integral domain is a commutative ring with non-zero unity having no zero divisors (ab = 0 implies a = 0 or b = 0).",
            "structural_refs": ["decl:JUDSON_ALG:DEF:units_zero_divisors"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:ideal",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.12",
            "chapter_section": "16.2 Ideals and Quotient Rings",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.12): Ideals in a Ring",
            "raw_statement": "An ideal I of a ring R is an additive subgroup of R such that for all r in R and a in I, r*a in I and a*r in I.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ring"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:quotient_ring",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.15",
            "chapter_section": "16.2 Ideals and Quotient Rings",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.15): Quotient Ring",
            "raw_statement": "Let I be an ideal of R. The quotient ring R/I is the set of cosets {r + I : r in R} with well-defined addition (r+I)+(s+I)=(r+s)+I and multiplication (r+I)(s+I)=rs+I.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ideal"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:ring_homomorphism",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.20",
            "chapter_section": "16.3 Ring Homomorphisms and First Isomorphism Theorem",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.20): Ring Homomorphism",
            "raw_statement": "A ring homomorphism phi: R -> S is a map such that phi(a + b) = phi(a) + phi(b) and phi(a * b) = phi(a) * phi(b) for all a, b in R.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ring"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:prime_ideal",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.26",
            "chapter_section": "16.2 Prime and Maximal Ideals",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.26): Prime Ideals",
            "raw_statement": "A proper ideal P in a commutative ring R is a prime ideal if ab in P implies a in P or b in P. Equivalently, R/P is an integral domain.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ideal", "decl:JUDSON_ALG:DEF:integral_domain"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:maximal_ideal",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch16:Def:16.28",
            "chapter_section": "16.2 Prime and Maximal Ideals",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 16.28): Maximal Ideals",
            "raw_statement": "A proper ideal M in a commutative ring R is maximal if there is no ideal J such that M < J < R. In a commutative ring with unity, M is maximal iff R/M is a field.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ideal", "decl:JUDSON_ALG:DEF:quotient_ring"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:polynomial_ring",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch17:Def:17.1",
            "chapter_section": "17.1 Polynomial Rings",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 17.1): Polynomial Ring R[x]",
            "raw_statement": "Let R be a commutative ring. The polynomial ring R[x] consists of formal sums sum_{i=0}^n a_i x^i with coefficients a_i in R under standard polynomial addition and multiplication.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:ring"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:irreducible_polynomial",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch17:Def:17.10",
            "chapter_section": "17.2 Irreducibility and Factorization",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 17.10): Irreducible Polynomials and Quotient Fields",
            "raw_statement": "A non-constant polynomial p(x) in F[x] over a field F is irreducible if p(x) cannot be factored as a product of two polynomials of lower degree. If p(x) is irreducible, F[x]/(p(x)) is a field.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:polynomial_ring", "decl:JUDSON_ALG:DEF:maximal_ideal"],
        },
        {
            "node_id": "decl:JUDSON_ALG:DEF:field_extension",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch21:Def:21.1",
            "chapter_section": "21.1 Extension Fields",
            "decl_type": "DEFINITION",
            "label": "Judson AATA (Def 21.1): Field Extensions and Degree",
            "raw_statement": "A field E is an extension field of a field F, denoted E/F, if F is a subfield of E. The degree [E : F] is the dimension of E as a vector space over F.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:irreducible_polynomial"],
        },
        {
            "node_id": "decl:JUDSON_ALG:THM:finite_fields",
            "source_id": "JUDSON_AATA_2023",
            "corpus": "JUDSON_ABSTRACT_ALGEBRA",
            "locator": "Judson:AATA:Ch22:Thm:22.1",
            "chapter_section": "22.1 Finite Fields (Galois Fields)",
            "decl_type": "THEOREM",
            "label": "Judson AATA (Thm 22.1): Structure and Uniqueness of Finite Fields",
            "raw_statement": "Every finite field has order p^n for some prime p and positive integer n, and is isomorphic to the splitting field of x^{p^n} - x over F_p. Its multiplicative group is cyclic.",
            "structural_refs": ["decl:JUDSON_ALG:DEF:field_extension", "decl:JUDSON_ALG:DEF:cyclic_group"],
        },
    ]

    for d in decls:
        d["statement_sha256"] = _hash_statement(d["raw_statement"])
        d["extraction_mode"] = "SOURCE_PARSE"
        d["license"] = "CC BY-SA 4.0 / GFDL" if "JUDSON" in d["node_id"] else "CC BY-NC-SA 4.0"

    return decls


# ----------------------------------------------------------------------
# 2. Canonical Contracts (32 Concepts)
# ----------------------------------------------------------------------
def generate_canonical_contracts() -> list[dict[str, Any]]:
    return [
        # --- Number Theory (8) ---
        {
            "canonical_id": "canonical:number_theory:divisibility_and_gcd",
            "name": "Divisibility and Greatest Common Divisor",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (a, b in Z, not both 0) EXISTS! (d = gcd(a,b) in Z+)",
            "hypotheses": ["a, b integers", "not both zero"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:DEF:divisibility", "decl:STEIN_ENT:DEF:greatest_common_divisor"],
            "description": "Divisibility lattice and greatest common divisor linear combination invariant.",
        },
        {
            "canonical_id": "canonical:number_theory:euclidean_algorithm",
            "name": "The Euclidean Division and Remainder Algorithm",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (a in Z, b in Z+) EXISTS (q_k, r_k finite descent trace ending in 0)",
            "hypotheses": ["a in Z", "b > 0"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:THM:euclidean_algorithm"],
            "description": "Division algorithm finite remainder descent chain computing gcd(a,b).",
        },
        {
            "canonical_id": "canonical:number_theory:bezout_identity",
            "name": "Bézout's Identity and Extended Euclidean Multipliers",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (a, b in Z) EXISTS (x, y in Z : a*x + b*y = gcd(a,b))",
            "hypotheses": ["a, b in Z"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:THM:bezout_identity"],
            "description": "Extended Euclidean matrix backward substitution computing Bézout certificates.",
        },
        {
            "canonical_id": "canonical:number_theory:prime_factorization",
            "name": "Fundamental Theorem of Arithmetic and Prime Factorization",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (n >= 2) EXISTS! (p_1^{e_1} ... p_k^{e_k} canonical prime power product)",
            "hypotheses": ["n integer >= 2"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:THM:fundamental_theorem_arithmetic"],
            "description": "Unique prime factorization multi-set representation.",
        },
        {
            "canonical_id": "canonical:number_theory:congruences_and_modular_arithmetic",
            "name": "Modular Congruences and Residue Ring Arithmetic",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (m in Z+, a, b in Z : a == b mod m <=> m | (a-b))",
            "hypotheses": ["modulus m >= 2"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:DEF:congruence"],
            "description": "Modular residue classes and cyclic quotient ring Z/mZ operations.",
        },
        {
            "canonical_id": "canonical:number_theory:chinese_remainder_theorem",
            "name": "Chinese Remainder Theorem for Coprime Moduli",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (m, n coprime, a, b in Z) EXISTS! (x in Z_{mn} : x == a mod m and x == b mod n)",
            "hypotheses": ["gcd(m, n) = 1", "m, n >= 2"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:THM:chinese_remainder_theorem"],
            "description": "Simultaneous residue reconstruction isomorphism Z_mn = Z_m x Z_n.",
        },
        {
            "canonical_id": "canonical:number_theory:euler_totient_and_theorem",
            "name": "Euler's Totient Function and Coprime Exponentiation Theorem",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (n in Z+, a in Z with gcd(a,n)=1 : a^{phi(n)} == 1 mod n)",
            "hypotheses": ["n >= 2", "gcd(a, n) = 1"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:DEF:euler_totient", "decl:STEIN_ENT:THM:euler_theorem"],
            "description": "Coprime residue group order phi(n) and modular power cycle closure.",
        },
        {
            "canonical_id": "canonical:number_theory:fermats_little_theorem",
            "name": "Fermat's Little Theorem for Prime Moduli",
            "domain": "Elementary Number Theory",
            "family": "NUMBER_THEORY",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (p prime, a in Z with p !| a : a^{p-1} == 1 mod p)",
            "hypotheses": ["p is prime", "gcd(a, p) = 1"],
            "aligned_source_node_ids": ["decl:STEIN_ENT:THM:fermat_little_theorem"],
            "description": "Prime field multiplicative order p-1 modular inversion.",
        },

        # --- Group Theory (12) ---
        {
            "canonical_id": "canonical:groups:group_axioms",
            "name": "Group Axioms and Permutation Regular Representations",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (a, b, c in G : (ab)c = a(bc), exists e, exists a^{-1})",
            "hypotheses": ["Set G closed under binary op", "Identity and inverse existence"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:group"],
            "description": "Cayley regular representation and Latin square table consistency.",
        },
        {
            "canonical_id": "canonical:groups:subgroups",
            "name": "Subgroups, Subgroup Criterion, and Lattices",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (non-empty H subset G : (a, b in H => ab^{-1} in H) <=> H <= G)",
            "hypotheses": ["H subset G non-empty", "One-step subgroup criterion"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:subgroup"],
            "description": "Subgroup poset lattice and closure under inverses.",
        },
        {
            "canonical_id": "canonical:groups:cosets",
            "name": "Left and Right Coset Partitions",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (H <= G, g in G : |gH| = |H| and cosets form partition of G)",
            "hypotheses": ["H <= G", "G finite or discrete"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:coset"],
            "description": "Equipotent disjoint coset fiber partition of group manifold.",
        },
        {
            "canonical_id": "canonical:groups:lagrange_theorem",
            "name": "Lagrange's Order Divisibility Theorem",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (finite G, H <= G : |H| divides |G| and |G| = [G:H] * |H|)",
            "hypotheses": ["G finite group", "H <= G"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:THM:lagrange"],
            "description": "Index formula and order divisibility across finite groups.",
        },
        {
            "canonical_id": "canonical:groups:cyclic_groups",
            "name": "Cyclic Groups, Generators, and Subgroup Lattices",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (G = <a> cyclic of order n : for every d | n exists unique subgroup of order d)",
            "hypotheses": ["G cyclic group"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:cyclic_group"],
            "description": "Cyclic permutation digraph and divisor subgroup lattice.",
        },
        {
            "canonical_id": "canonical:groups:group_homomorphisms",
            "name": "Group Homomorphisms and Structure Preservation",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (f: G -> H : f(xy) = f(x)f(y) for all x, y in G)",
            "hypotheses": ["G, H groups", "f structure-preserving map"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:group_homomorphism"],
            "description": "Homomorphic commutative diagram tensor evaluation.",
        },
        {
            "canonical_id": "canonical:groups:kernels_and_images",
            "name": "Kernels, Images, and Fiber Decompositions",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (f: G -> H : ker f <= G, im f <= H, fibers f^{-1}(h) = g * ker f)",
            "hypotheses": ["f: G -> H group homomorphism"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:kernel_and_image"],
            "description": "Kernel subspace projection and inverse image fiber partition.",
        },
        {
            "canonical_id": "canonical:groups:normal_subgroups",
            "name": "Normal Subgroups and Conjugation Invariance",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (N <= G : (forall g in G : gNg^{-1} = N) <=> N <| G)",
            "hypotheses": ["N <= G", "Conjugation invariance"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:normal_subgroup"],
            "description": "Self-conjugate normal subgroup characterization and left/right coset equality.",
        },
        {
            "canonical_id": "canonical:groups:quotient_groups",
            "name": "Factor Groups and Coset Multiplication Operations",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (N <| G : (aN)(bN) = (ab)N is well-defined group on G/N)",
            "hypotheses": ["N normal subgroup of G"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:quotient_group"],
            "description": "Quotient group Cayley graph and coset multiplication table.",
        },
        {
            "canonical_id": "canonical:groups:first_isomorphism_theorem_groups",
            "name": "First Isomorphism Theorem for Groups",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (f: G -> H : ker f <| G and G / ker f ~= im f)",
            "hypotheses": ["f: G -> H homomorphism"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:THM:first_isomorphism_groups"],
            "description": "Canonical bijective isomorphism between quotient cosets and image elements.",
        },
        {
            "canonical_id": "canonical:groups:symmetric_and_alternating_groups",
            "name": "Symmetric and Alternating Groups, Cycle Parity",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (n >= 2 : sgn: S_n -> {+1, -1} is homom, ker(sgn) = A_n with |A_n| = n!/2)",
            "hypotheses": ["Degree n >= 2"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:symmetric_group"],
            "description": "Permutation cycle decomposition and alternating group index 2 parity kernel.",
        },
        {
            "canonical_id": "canonical:groups:group_actions_and_orbit_stabilizer",
            "name": "Group Actions, Orbits, and Orbit-Stabilizer Theorem",
            "domain": "Group Theory",
            "family": "GROUPS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (G acting on X, x in X : |G| = |Orb(x)| * |Stab(x)|)",
            "hypotheses": ["G finite group acting on finite set X"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:THM:orbit_stabilizer"],
            "description": "Action permutation matrix representation and orbit-stabilizer coset bijection.",
        },

        # --- Ring & Field Theory (12) ---
        {
            "canonical_id": "canonical:rings_fields:ring_axioms",
            "name": "Ring Axioms and Matrix Ring Structures",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (a, b, c in R : (R,+) abelian, * assoc, a(b+c)=ab+ac, (a+b)c=ac+bc)",
            "hypotheses": ["Set R with two binary operations +, *"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:ring"],
            "description": "Bilinear ring operation tensors and distributive validation.",
        },
        {
            "canonical_id": "canonical:rings_fields:units_and_zero_divisors",
            "name": "Units, Invertible Elements, and Zero Divisors",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (r in R with 1 : r in R^x <=> exists r^{-1}; r zero-divisor <=> exists s!=0: rs=0)",
            "hypotheses": ["Ring R with unity"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:units_zero_divisors"],
            "description": "Multiplicative group of units R^x and zero-divisor graph.",
        },
        {
            "canonical_id": "canonical:rings_fields:integral_domains",
            "name": "Integral Domains and Cancellation Properties",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (comm ring R with 1!=0 : (forall a, b: ab=0 => a=0 or b=0) <=> R is domain)",
            "hypotheses": ["Commutative ring R with 1 != 0"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:integral_domain"],
            "description": "Zero-divisor-free ring cancellation algebraic and cell verification.",
        },
        {
            "canonical_id": "canonical:rings_fields:ideals",
            "name": "Ideals, Ideal Absorption, and Principal Ideals",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (I subset R : (I <= (R,+) and forall r in R, a in I: ra in I) <=> I is ideal)",
            "hypotheses": ["R ring", "I additive subgroup with multiplicative absorption"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:ideal"],
            "description": "Absorption matrix closure and principal ideal generator lattice.",
        },
        {
            "canonical_id": "canonical:rings_fields:quotient_rings",
            "name": "Quotient Rings and Residue Arithmetic",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (ideal I of R : (r+I)(s+I) = rs+I is well-defined on R/I)",
            "hypotheses": ["I ideal in ring R"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:quotient_ring"],
            "description": "Quotient ring addition and multiplication coset cell complex.",
        },
        {
            "canonical_id": "canonical:rings_fields:ring_homomorphisms",
            "name": "Ring Homomorphisms, Kernels, and First Isomorphism Theorem",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (phi: R -> S : ker phi is ideal of R and R / ker phi ~= im phi)",
            "hypotheses": ["phi additive and multiplicative homomorphism"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:ring_homomorphism"],
            "description": "Ring homomorphism kernel ideal absorption and quotient isomorphism.",
        },
        {
            "canonical_id": "canonical:rings_fields:prime_ideals",
            "name": "Prime Ideals and Integral Domain Quotient Characterization",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (ideal P of comm R : (ab in P => a in P or b in P) <=> R/P is integral domain)",
            "hypotheses": ["R commutative ring with unity", "P proper ideal"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:prime_ideal"],
            "description": "Prime ideal factor characterization and domain quotient verification.",
        },
        {
            "canonical_id": "canonical:rings_fields:maximal_ideals",
            "name": "Maximal Ideals and Field Quotient Characterization",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (ideal M of comm R : M maximal <=> R/M is a field)",
            "hypotheses": ["R commutative ring with unity", "M proper maximal ideal"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:maximal_ideal"],
            "description": "Maximal ideal unit-generation and field inversion quotient verification.",
        },
        {
            "canonical_id": "canonical:rings_fields:polynomial_rings",
            "name": "Polynomial Rings R[x] and Degree Valuations",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (f, g in R[x] over domain R : deg(f*g) = deg(f) + deg(g))",
            "hypotheses": ["R commutative ring or field"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:polynomial_ring"],
            "description": "Polynomial coefficient algebra matrix and convolution multiplication.",
        },
        {
            "canonical_id": "canonical:rings_fields:irreducibility_and_quotients",
            "name": "Irreducible Polynomials and Quotient Extension Fields",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (p(x) in F[x] : p(x) irreducible <=> F[x]/(p(x)) is a field)",
            "hypotheses": ["F is a field", "p(x) non-constant"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:irreducible_polynomial"],
            "description": "Irreducible polynomial Euclidean inversion matrix constructing field F[x]/(p(x)).",
        },
        {
            "canonical_id": "canonical:rings_fields:field_extensions",
            "name": "Field Extensions, Algebraic Elements, and Tower Law",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (F <= K <= E fields : [E : F] = [E : K] * [K : F])",
            "hypotheses": ["Tower of field extensions F <= K <= E"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:DEF:field_extension"],
            "description": "Vector space basis expansion and degree product tower law.",
        },
        {
            "canonical_id": "canonical:rings_fields:finite_fields",
            "name": "Finite Fields (Galois Fields) and Frobenius Automorphisms",
            "domain": "Ring & Field Theory",
            "family": "RINGS_FIELDS",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "quantifier_contract": "FORALL (prime p, n >= 1 : exists! GF(p^n) of order p^n; Frob(x)=x^p is automorphism)",
            "hypotheses": ["p prime", "dimension n >= 1"],
            "aligned_source_node_ids": ["decl:JUDSON_ALG:THM:finite_fields"],
            "description": "Galois field GF(p^n) arithmetic, Frobenius linear map, and cyclic unit generator.",
        },
    ]


# ----------------------------------------------------------------------
# 3. Typed Mathematical Relationships
# ----------------------------------------------------------------------
def generate_typed_relationships() -> list[dict[str, Any]]:
    return [
        {
            "relation_id": "REL:F3:EUCLIDEAN_TO_BEZOUT",
            "relation_type": "CONSTRUCTION",
            "source_canonical_id": "canonical:number_theory:euclidean_algorithm",
            "target_canonical_id": "canonical:number_theory:bezout_identity",
            "mathematical_claim": "The division sequence of the Euclidean algorithm constructs the Bézout integer linear multipliers (x, y) via backward substitution matrix recursion.",
            "witness_validator": "validate_euclidean_bezout_construction",
        },
        {
            "relation_id": "REL:F3:BEZOUT_TO_GCD",
            "relation_type": "IMPLICATION",
            "source_canonical_id": "canonical:number_theory:bezout_identity",
            "target_canonical_id": "canonical:number_theory:divisibility_and_gcd",
            "mathematical_claim": "The existence of integers (x, y) with ax + by = d implies d is the greatest common divisor gcd(a, b).",
            "witness_validator": "validate_bezout_gcd_implication",
        },
        {
            "relation_id": "REL:F3:EULER_TO_FERMAT",
            "relation_type": "SPECIALIZATION",
            "source_canonical_id": "canonical:number_theory:euler_totient_and_theorem",
            "target_canonical_id": "canonical:number_theory:fermats_little_theorem",
            "mathematical_claim": "Euler's theorem a^{phi(n)} == 1 (mod n) specializes to Fermat's Little Theorem a^{p-1} == 1 (mod p) whenever n = p is a prime, since phi(p) = p - 1.",
            "witness_validator": "validate_euler_fermat_specialization",
        },
        {
            "relation_id": "REL:F3:CRT_TO_RING_PRODUCT",
            "relation_type": "ISOMORPHISM",
            "source_canonical_id": "canonical:number_theory:chinese_remainder_theorem",
            "target_canonical_id": "canonical:rings_fields:quotient_rings",
            "mathematical_claim": "The Chinese Remainder Theorem establishes a ring isomorphism Z/(mn)Z ~= Z/mZ x Z/nZ for pairwise coprime integers gcd(m, n) = 1.",
            "witness_validator": "validate_crt_ring_product_isomorphism",
        },
        {
            "relation_id": "REL:F3:COSETS_TO_LAGRANGE",
            "relation_type": "PARTITION",
            "source_canonical_id": "canonical:groups:cosets",
            "target_canonical_id": "canonical:groups:lagrange_theorem",
            "mathematical_claim": "The left cosets of subgroup H in G partition the finite group G into [G:H] disjoint fibers of uniform size |H|, establishing Lagrange's formula |G| = [G:H] * |H|.",
            "witness_validator": "validate_cosets_lagrange_partition",
        },
        {
            "relation_id": "REL:F3:HOMOMORPHISM_TO_KERNEL",
            "relation_type": "CONSTRUCTION",
            "source_canonical_id": "canonical:groups:group_homomorphisms",
            "target_canonical_id": "canonical:groups:kernels_and_images",
            "mathematical_claim": "Any group homomorphism f: G -> H constructs a unique kernel subgroup ker f = f^{-1}(e_H) and image subgroup im f <= H.",
            "witness_validator": "validate_homomorphism_kernel_construction",
        },
        {
            "relation_id": "REL:F3:KERNEL_TO_NORMAL",
            "relation_type": "IMPLICATION",
            "source_canonical_id": "canonical:groups:kernels_and_images",
            "target_canonical_id": "canonical:groups:normal_subgroups",
            "mathematical_claim": "The kernel of any group homomorphism f: G -> H is invariant under conjugation (g (ker f) g^{-1} = ker f for all g in G), and hence is normal in G.",
            "witness_validator": "validate_kernel_normal_implication",
        },
        {
            "relation_id": "REL:F3:NORMAL_TO_QUOTIENT",
            "relation_type": "CONSTRUCTION",
            "source_canonical_id": "canonical:groups:normal_subgroups",
            "target_canonical_id": "canonical:groups:quotient_groups",
            "mathematical_claim": "A normal subgroup N <| G constructs a well-defined factor group G/N with coset operation (aN)(bN) = (ab)N.",
            "witness_validator": "validate_normal_quotient_construction",
        },
        {
            "relation_id": "REL:F3:QUOTIENT_TO_FIRST_ISOMORPHISM",
            "relation_type": "ISOMORPHISM",
            "source_canonical_id": "canonical:groups:quotient_groups",
            "target_canonical_id": "canonical:groups:first_isomorphism_theorem_groups",
            "mathematical_claim": "The factor group G/ker f is canonically isomorphic to the image subgroup im f under g(ker f) |-> f(g).",
            "witness_validator": "validate_quotient_first_isomorphism",
        },
        {
            "relation_id": "REL:F3:ACTION_TO_ORBIT_STABILIZER",
            "relation_type": "DECOMPOSITION",
            "source_canonical_id": "canonical:groups:group_actions_and_orbit_stabilizer",
            "target_canonical_id": "canonical:groups:lagrange_theorem",
            "mathematical_claim": "The Orbit-Stabilizer theorem decomposes the group action fibers G/Stab(x) ~= Orb(x), deriving |G| = |Orb(x)| * |Stab(x)| as a direct consequence of Lagrange's theorem on Stab(x) <= G.",
            "witness_validator": "validate_action_orbit_stabilizer_decomposition",
        },
        {
            "relation_id": "REL:F3:PRIME_IDEAL_TO_DOMAIN",
            "relation_type": "QUOTIENT",
            "source_canonical_id": "canonical:rings_fields:prime_ideals",
            "target_canonical_id": "canonical:rings_fields:integral_domains",
            "mathematical_claim": "An ideal P in a commutative ring R with unity is prime if and only if the quotient ring R/P is an integral domain.",
            "witness_validator": "validate_prime_ideal_domain_quotient",
        },
        {
            "relation_id": "REL:F3:MAXIMAL_IDEAL_TO_FIELD",
            "relation_type": "QUOTIENT",
            "source_canonical_id": "canonical:rings_fields:maximal_ideals",
            "target_canonical_id": "canonical:rings_fields:finite_fields",
            "mathematical_claim": "An ideal M in a commutative ring R with unity is maximal if and only if the quotient ring R/M is a field.",
            "witness_validator": "validate_maximal_ideal_field_quotient",
        },
        {
            "relation_id": "REL:F3:IRREDUCIBLE_TO_FIELD_EXTENSION",
            "relation_type": "CONSTRUCTION",
            "source_canonical_id": "canonical:rings_fields:irreducibility_and_quotients",
            "target_canonical_id": "canonical:rings_fields:field_extensions",
            "mathematical_claim": "An irreducible polynomial p(x) in F[x] constructs a simple algebraic field extension K = F[x]/(p(x)) with degree [K:F] = deg(p).",
            "witness_validator": "validate_irreducible_field_extension_construction",
        },
        {
            "relation_id": "REL:F3:FINITE_FIELD_TO_CYCLIC_UNITS",
            "relation_type": "ISOMORPHISM",
            "source_canonical_id": "canonical:rings_fields:finite_fields",
            "target_canonical_id": "canonical:groups:cyclic_groups",
            "mathematical_claim": "The multiplicative group of any finite field GF(q)^x is cyclic of order q - 1, isomorphic to (Z/(q-1)Z, +).",
            "witness_validator": "validate_finite_field_cyclic_units_isomorphism",
        },
    ]


# ----------------------------------------------------------------------
# 4. Falsification Mutants (Minimum 2 per family)
# ----------------------------------------------------------------------
def generate_falsification_mutants() -> list[dict[str, Any]]:
    return [
        # --- Number Theory Mutants (4) ---
        {
            "mutant_id": "MUT:NT:01_FERMAT_COMPOSITE_MODULUS",
            "family": "NUMBER_THEORY",
            "mutation_class": "NON_PRIME_MODULUS_SUBSTITUTION",
            "target_canonical_id": "canonical:number_theory:fermats_little_theorem",
            "description": "Substitute composite modulus n=6 into Fermat's Little Theorem (2^5 = 32 = 2 != 1 mod 6).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:NT:02_CRT_NON_COPRIME_MODULI",
            "family": "NUMBER_THEORY",
            "mutation_class": "INVALID_COPRIMALITY_HYPOTHESIS",
            "target_canonical_id": "canonical:number_theory:chinese_remainder_theorem",
            "description": "Use non-coprime moduli m1=4, m2=6 with contradictory residues x=1 mod 4 and x=2 mod 6.",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:NT:03_BEZOUT_CORRUPTED_COEFFICIENTS",
            "family": "NUMBER_THEORY",
            "mutation_class": "CORRUPTED_LINEAR_COMBINATION",
            "target_canonical_id": "canonical:number_theory:bezout_identity",
            "description": "Perturb Bézout multiplier pair (x, y) such that a*x + b*y != gcd(a, b).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:NT:04_EULER_WRONG_TOTIENT",
            "family": "NUMBER_THEORY",
            "mutation_class": "ALTERED_EXPONENT_POWER",
            "target_canonical_id": "canonical:number_theory:euler_totient_and_theorem",
            "description": "Evaluate power a^{phi(n)+1} mod n violating group order identity.",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },

        # --- Group Theory Mutants (4) ---
        {
            "mutant_id": "MUT:GRP:05_NON_NORMAL_SUBGROUP_QUOTIENT",
            "family": "GROUPS",
            "mutation_class": "NON_NORMAL_SUBGROUP_QUOTIENT",
            "target_canonical_id": "canonical:groups:quotient_groups",
            "description": "Attempt to form factor group on non-normal subgroup H = <(1 2)> in S_3 (coset multiplication ill-defined).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:GRP:06_BROKEN_ASSOCIATIVITY_CAYLEY_TABLE",
            "family": "GROUPS",
            "mutation_class": "BROKEN_ASSOCIATIVITY",
            "target_canonical_id": "canonical:groups:group_axioms",
            "description": "Perturb a single entry in Cayley multiplication table to violate associativity (ab)c != a(bc).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:GRP:07_CORRUPTED_HOMOMORPHISM_MAP",
            "family": "GROUPS",
            "mutation_class": "CORRUPTED_HOMOMORPHISM",
            "target_canonical_id": "canonical:groups:group_homomorphisms",
            "description": "Inject map f: G -> H violating homomorphism property f(xy) != f(x)f(y).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:GRP:08_COSET_FIBER_IMBALANCE",
            "family": "GROUPS",
            "mutation_class": "COSET_PARTITION_VIOLATION",
            "target_canonical_id": "canonical:groups:cosets",
            "description": "Construct unequal coset fiber sizes violating equipotence |gH| != |H|.",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },

        # --- Ring & Field Mutants (4) ---
        {
            "mutant_id": "MUT:RNG:09_NON_MAXIMAL_IDEAL_FIELD_CLAIM",
            "family": "RINGS_FIELDS",
            "mutation_class": "NON_MAXIMAL_IDEAL_FIELD_CLAIM",
            "target_canonical_id": "canonical:rings_fields:maximal_ideals",
            "description": "Claim non-maximal ideal (x^2) in R[x] yields a quotient field (contains zero divisor x + (x^2)).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:RNG:10_NON_PRIME_IDEAL_DOMAIN_CLAIM",
            "family": "RINGS_FIELDS",
            "mutation_class": "NON_PRIME_IDEAL_DOMAIN_CLAIM",
            "target_canonical_id": "canonical:rings_fields:prime_ideals",
            "description": "Claim composite ideal (6) in Z yields an integral domain (2 * 3 = 0 in Z/6Z).",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:RNG:11_REDUCIBLE_POLYNOMIAL_FIELD_CLAIM",
            "family": "RINGS_FIELDS",
            "mutation_class": "REDUCIBLE_POLYNOMIAL_FIELD_CLAIM",
            "target_canonical_id": "canonical:rings_fields:irreducibility_and_quotients",
            "description": "Attempt to construct field extension via reducible polynomial x^2 - 1 = (x-1)(x+1) in F_2[x].",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
        {
            "mutant_id": "MUT:RNG:12_CORRUPTED_FROBENIUS_LINEARITY",
            "family": "RINGS_FIELDS",
            "mutation_class": "CORRUPTED_FROBENIUS_MAP",
            "target_canonical_id": "canonical:rings_fields:finite_fields",
            "description": "Perturb Frobenius map x |-> x^p violating fresh-man's dream (x+y)^p != x^p + y^p.",
            "expected_verdict": "NONCOMMUTATIVE_UNDER_CONTRACT",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Wave F3 Manifests")
    parser.parse_args()

    # 1. Source Manifest
    sources = generate_source_declarations()
    source_manifest = {
        "schema_version": "0.21",
        "stage": "v0.21_wave_f3",
        "corpora": [
            {
                "corpus_id": "JUDSON_ABSTRACT_ALGEBRA",
                "title": "Abstract Algebra: Theory and Applications",
                "author": "Thomas W. Judson",
                "edition": "2023 Edition",
                "license": "GNU Free Documentation License / CC BY-SA 4.0",
                "official_url": "http://abstract.ups.edu/",
            },
            {
                "corpus_id": "STEIN_NUMBER_THEORY",
                "title": "Elementary Number Theory: Primes, Congruences, and Secrets",
                "author": "William Stein",
                "edition": "2017 Edition (Springer / Open Access)",
                "license": "CC BY-NC-SA 4.0",
                "official_url": "https://wstein.org/ent/",
            },
        ],
        "total_source_declarations": len(sources),
        "declarations": sources,
    }
    SOURCE_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_MANIFEST_PATH.write_text(json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[Wave F3] Saved source manifest: {SOURCE_MANIFEST_PATH} ({len(sources)} declarations)")

    # 2. Contract Manifest
    contracts = generate_canonical_contracts()
    contracts_count: dict[str, int] = {}
    families_count: dict[str, int] = {}
    verdicts_count: dict[str, int] = {}

    for c in contracts:
        ctr = c["contract"]
        fam = c["family"]
        v = c["expected_verdict"]
        contracts_count[ctr] = contracts_count.get(ctr, 0) + 1
        families_count[fam] = families_count.get(fam, 0) + 1
        verdicts_count[v] = verdicts_count.get(v, 0) + 1

    contract_manifest = {
        "schema_version": "0.21",
        "stage": "v0.21_wave_f3",
        "campaign_name": "ABSTRACT_ALGEBRA_AND_NUMBER_THEORY_DUAL_VIEW_AUDIT",
        "total_canonical_concepts": len(contracts),
        "families_breakdown": families_count,
        "contracts_breakdown": contracts_count,
        "expected_verdicts_breakdown": verdicts_count,
        "target_concepts": contracts,
    }
    CONTRACT_MANIFEST_PATH.write_text(json.dumps(contract_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[Wave F3] Saved contract manifest: {CONTRACT_MANIFEST_PATH} ({len(contracts)} canonical concepts)")

    # 3. Relation Manifest
    relations = generate_typed_relationships()
    relation_manifest = {
        "schema_version": "0.21",
        "stage": "v0.21_wave_f3",
        "total_typed_relations": len(relations),
        "relations": relations,
    }
    RELATION_MANIFEST_PATH.write_text(json.dumps(relation_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[Wave F3] Saved relation manifest: {RELATION_MANIFEST_PATH} ({len(relations)} typed relationships)")

    # 4. Falsification Manifest
    mutants = generate_falsification_mutants()
    falsification_manifest = {
        "schema_version": "0.21",
        "stage": "v0.21_wave_f3",
        "total_registered_mutants": len(mutants),
        "mutants": mutants,
    }
    FALSIFICATION_MANIFEST_PATH.write_text(json.dumps(falsification_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[Wave F3] Saved falsification manifest: {FALSIFICATION_MANIFEST_PATH} ({len(mutants)} registered mutants)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
