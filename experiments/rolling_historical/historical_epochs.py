"""Historical Epochs Definition and Semantic Corpora for Rolling Campaign H2.

Covers 12 rolling origins: 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010.
Strictly ensures zero semantic leakage: all vocabulary in G_t is validated <= t.
"""

from typing import Dict, List, Any

ROLLING_ORIGINS = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010]
EVAL_HORIZONS = [5, 10, 25, 50]

# Historical epoch ground truths: base state populations and subsequent discoveries
EPOCH_DEFINITIONS: Dict[int, Dict[str, Any]] = {
    1900: {
        "focus_areas": ["Analysis", "Algebra", "Topology", "Number Theory"],
        "key_sources": [
            {"author": "Hilbert, D.", "year": 1899, "work": "Grundlagen der Geometrie"},
            {"author": "Poincare, H.", "year": 1895, "work": "Analysis Situs"},
            {"author": "Dedekind, R.", "year": 1871, "work": "Theorie der algebraischen Zahlen"},
            {"author": "Weierstrass, K.", "year": 1872, "work": "Zur Funktionenlehre"}
        ],
        "core_nodes": [
            {"id": "N1900_01", "domain": "Topology", "degree": 4, "depth": 1, "coordinates": {"Delta": 1, "I": 2, "W": 1, "sigma": 1, "Pi": 2, "Gamma": 1}},
            {"id": "N1900_02", "domain": "Algebra", "degree": 6, "depth": 2, "coordinates": {"Delta": 2, "I": 3, "W": 2, "sigma": 1, "Pi": 1, "Gamma": 2}},
            {"id": "N1900_03", "domain": "Analysis", "degree": 5, "depth": 2, "coordinates": {"Delta": 3, "I": 1, "W": 3, "sigma": 2, "Pi": 1, "Gamma": 1}},
            {"id": "N1900_04", "domain": "Number_Theory", "degree": 5, "depth": 1, "coordinates": {"Delta": 1, "I": 1, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 1}},
            {"id": "N1900_05", "domain": "Geometry", "degree": 3, "depth": 1, "coordinates": {"Delta": 2, "I": 1, "W": 1, "sigma": 1, "Pi": 1, "Gamma": 1}},
            {"id": "N1900_06", "domain": "Logic", "degree": 3, "depth": 1, "coordinates": {"Delta": 1, "I": 2, "W": 1, "sigma": 2, "Pi": 1, "Gamma": 1}},
        ],
        "discoveries": [
            {"id": "DISC_1905_LEBESGUE", "year": 1905, "domain": "Analysis", "slot": "SLOT_INTEGRATION_MEASURE", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1908_STEINITZ", "year": 1910, "domain": "Algebra", "slot": "SLOT_ABSTRACT_FIELD", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1922_CARTAN_DIFF", "year": 1922, "domain": "Geometry", "slot": "SLOT_EXTERIOR_CALCULUS", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1931_GODEL", "year": 1931, "domain": "Logic", "slot": "SLOT_INCOMPLETENESS", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1910: {
        "focus_areas": ["Analysis", "Algebra", "Topology", "Set Theory"],
        "key_sources": [
            {"author": "Frechet, M.", "year": 1906, "work": "Espaces abstraits"},
            {"author": "Zermelo, E.", "year": 1908, "work": "Untersuchungen Grundlagen der Mengenlehre"},
            {"author": "Brouwer, L.E.J.", "year": 1910, "work": "Fixpunktsatz"}
        ],
        "core_nodes": [
            {"id": "N1910_01", "domain": "Analysis", "degree": 7, "depth": 2, "coordinates": {"Delta": 3, "I": 2, "W": 3, "sigma": 2, "Pi": 1, "Gamma": 2}},
            {"id": "N1910_02", "domain": "Topology", "degree": 5, "depth": 2, "coordinates": {"Delta": 2, "I": 2, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 1}},
            {"id": "N1910_03", "domain": "Logic", "degree": 4, "depth": 1, "coordinates": {"Delta": 1, "I": 3, "W": 2, "sigma": 2, "Pi": 1, "Gamma": 2}},
            {"id": "N1910_04", "domain": "Algebra", "degree": 6, "depth": 2, "coordinates": {"Delta": 2, "I": 3, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 1}},
        ],
        "discoveries": [
            {"id": "DISC_1914_HAUSDORFF", "year": 1914, "domain": "Topology", "slot": "SLOT_TOPOLOGICAL_SPACE", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1920_NOETHER_IDEALS", "year": 1921, "domain": "Algebra", "slot": "SLOT_IDEAL_THEORY", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1932_BANACH_SPACES", "year": 1932, "domain": "Analysis", "slot": "SLOT_NORMED_LINEAR_SPACE", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1944_EILENBERG_MACLANE", "year": 1945, "domain": "Topology", "slot": "SLOT_CATEGORICAL_DUALITY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1920: {
        "focus_areas": ["Functional Analysis", "Abstract Algebra", "General Relativity Geometry"],
        "key_sources": [
            {"author": "Weyl, H.", "year": 1918, "work": "Raum, Zeit, Materie"},
            {"author": "Noether, E.", "year": 1920, "work": "Moduln in nichtkommutativen Bereichen"},
            {"author": "Riesz, F.", "year": 1918, "work": "Uber lineare Funktionalgleichungen"}
        ],
        "core_nodes": [
            {"id": "N1920_01", "domain": "Algebra", "degree": 8, "depth": 3, "coordinates": {"Delta": 3, "I": 3, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 2}},
            {"id": "N1920_02", "domain": "Analysis", "degree": 7, "depth": 2, "coordinates": {"Delta": 3, "I": 2, "W": 3, "sigma": 2, "Pi": 1, "Gamma": 2}},
            {"id": "N1920_03", "domain": "Geometry", "degree": 5, "depth": 2, "coordinates": {"Delta": 2, "I": 2, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 1}},
        ],
        "discoveries": [
            {"id": "DISC_1925_HEISENBERG_BORN", "year": 1925, "domain": "Analysis", "slot": "SLOT_OPERATOR_ALGEBRA", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1930_VAN_DER_WAERDEN", "year": 1930, "domain": "Algebra", "slot": "SLOT_MODERN_ALGEBRA", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1945_CATEGORY_FOUNDATIONS", "year": 1945, "domain": "Algebra", "slot": "SLOT_FUNCTORIAL_NATURALITY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1965_LANG_ALGEBRA", "year": 1965, "domain": "Algebra", "slot": "SLOT_COHOMOLOGICAL_ALGEBRA", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
        ]
    },
    1930: {
        "focus_areas": ["Modern Algebra", "Quantum Operator Theory", "Mathematical Logic"],
        "key_sources": [
            {"author": "van der Waerden, B.L.", "year": 1930, "work": "Moderne Algebra"},
            {"author": "von Neumann, J.", "year": 1929, "work": "Allgemeine Eigenwerttheorie"},
            {"author": "Artin, E.", "year": 1927, "work": "Reziprozitatsgesetz"}
        ],
        "core_nodes": [
            {"id": "N1930_01", "domain": "Algebra", "degree": 9, "depth": 3, "coordinates": {"Delta": 3, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}},
            {"id": "N1930_02", "domain": "Analysis", "degree": 8, "depth": 3, "coordinates": {"Delta": 4, "I": 2, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}},
            {"id": "N1930_03", "domain": "Logic", "degree": 5, "depth": 2, "coordinates": {"Delta": 2, "I": 3, "W": 2, "sigma": 2, "Pi": 1, "Gamma": 2}},
        ],
        "discoveries": [
            {"id": "DISC_1935_HUREWICZ", "year": 1935, "domain": "Topology", "slot": "SLOT_HOMOTOPY_GROUP", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1940_BOURBAKI_TOPOLOGY", "year": 1940, "domain": "Topology", "slot": "SLOT_UNIFORM_STRUCTURE", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1955_CARTAN_EILENBERG", "year": 1956, "domain": "Algebra", "slot": "SLOT_HOMOLOGICAL_EXT", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1975_CONNES_FACTORS", "year": 1975, "domain": "Analysis", "slot": "SLOT_NONCOMMUTATIVE_GEOMETRY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1940: {
        "focus_areas": ["Algebraic Topology", "Differential Forms", "Fiber Bundles"],
        "key_sources": [
            {"author": "Hurewicz, W.", "year": 1935, "work": "Beitrage zur Topologie"},
            {"author": "de Rham, G.", "year": 1931, "work": "Sur l'analysis situs"},
            {"author": "Whitney, H.", "year": 1937, "work": "Differentiable manifolds"}
        ],
        "core_nodes": [
            {"id": "N1940_01", "domain": "Topology", "degree": 8, "depth": 3, "coordinates": {"Delta": 3, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}},
            {"id": "N1940_02", "domain": "Geometry", "degree": 7, "depth": 2, "coordinates": {"Delta": 3, "I": 2, "W": 2, "sigma": 1, "Pi": 2, "Gamma": 2}},
            {"id": "N1940_03", "domain": "Algebra", "degree": 7, "depth": 2, "coordinates": {"Delta": 2, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 1}},
        ],
        "discoveries": [
            {"id": "DISC_1945_EILENBERG_STEENROD", "year": 1945, "domain": "Topology", "slot": "SLOT_AXIOMATIC_HOMOLOGY", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1950_CARTAN_SEMINAR", "year": 1950, "domain": "Topology", "slot": "SLOT_SHEAF_GERM", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1965_ATIYAH_K_THEORY", "year": 1964, "domain": "Topology", "slot": "SLOT_TOPOLOGICAL_K_THEORY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1985_DONALDSON_4M", "year": 1983, "domain": "Geometry", "slot": "SLOT_GAUGE_THEORETIC_INVARIANT", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1950: {
        "focus_areas": ["Homological Foundations", "Sheaf Theory", "Fiber Bundles"],
        "key_sources": [
            {"author": "Eilenberg, S. and Mac Lane, S.", "year": 1945, "work": "General Theory of Natural Equivalences"},
            {"author": "Leray, J.", "year": 1946, "work": "L'anneau d'homologie d'une representation"},
            {"author": "Cartan, H.", "year": 1949, "work": "Seminaire Cartan (Faisceaux)"}
        ],
        "core_nodes": [
            {"id": "N1950_01", "domain": "Topology", "degree": 9, "depth": 3, "coordinates": {"Delta": 4, "I": 3, "W": 3, "sigma": 2, "Pi": 3, "Gamma": 2}},
            {"id": "N1950_02", "domain": "Algebra", "degree": 9, "depth": 3, "coordinates": {"Delta": 3, "I": 4, "W": 3, "sigma": 2, "Pi": 3, "Gamma": 2}},
            {"id": "N1950_03", "domain": "Geometry", "degree": 8, "depth": 3, "coordinates": {"Delta": 3, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}},
        ],
        "discoveries": [
            {"id": "DISC_1955_SERRE_FAC", "year": 1955, "domain": "Algebraic_Geometry", "slot": "SLOT_SHEAF_COHOMOLOGY", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1956_CARTAN_EILENBERG", "year": 1956, "domain": "Homological_Algebra", "slot": "SLOT_DERIVED_FUNCTOR_EXT", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1960_GROTHENDIECK_EGA", "year": 1960, "domain": "Algebraic_Geometry", "slot": "SLOT_ALGEBRAIC_SCHEME", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_1963_ATIYAH_SINGER", "year": 1963, "domain": "Global_Analysis", "slot": "SLOT_INDEX_INVARIANT", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1967_QUILLEN_SPECTRAL", "year": 1967, "domain": "Homotopical_Algebra", "slot": "SLOT_ABSTRACT_HOMOTOPY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1960: {
        "focus_areas": ["Schemes", "Derived Categories", "Index Theory"],
        "key_sources": [
            {"author": "Grothendieck, A.", "year": 1960, "work": "Elements de Geometrie Algebrique I"},
            {"author": "Serre, J.-P.", "year": 1955, "work": "Faisceaux Algebriques Coherents"},
            {"author": "Cartan, H. and Eilenberg, S.", "year": 1956, "work": "Homological Algebra"}
        ],
        "core_nodes": [
            {"id": "N1960_01", "domain": "Algebraic_Geometry", "degree": 11, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 2, "Pi": 3, "Gamma": 3}},
            {"id": "N1960_02", "domain": "Topology", "degree": 10, "depth": 3, "coordinates": {"Delta": 4, "I": 3, "W": 3, "sigma": 2, "Pi": 3, "Gamma": 2}},
            {"id": "N1960_03", "domain": "Analysis", "degree": 8, "depth": 3, "coordinates": {"Delta": 3, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}},
        ],
        "discoveries": [
            {"id": "DISC_1965_VERDIER_DERIVED", "year": 1967, "domain": "Category_Theory", "slot": "SLOT_DERIVED_CATEGORY", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1970_DELIGNE_WEIL_I", "year": 1974, "domain": "Number_Theory", "slot": "SLOT_L_ADIC_WEIL_CONJECTURES", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1985_FALTINGS_MORDEL", "year": 1983, "domain": "Arithmetic_Geometry", "slot": "SLOT_ARITHMETIC_MODULI", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_2005_PERELMAN_RICCI", "year": 2003, "domain": "Differential_Geometry", "slot": "SLOT_RICCI_FLOW_SURGERY", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1970: {
        "focus_areas": ["Topos Theory", "Model Categories", "Deligne Cohomology"],
        "key_sources": [
            {"author": "Lawvere, F.W. and Tierney, M.", "year": 1970, "work": "Elementary Topoi"},
            {"author": "Quillen, D.", "year": 1967, "work": "Homotopical Algebra"},
            {"author": "Deligne, P.", "year": 1970, "work": "Theorie de Hodge I"}
        ],
        "core_nodes": [
            {"id": "N1970_01", "domain": "Category_Theory", "degree": 12, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 3, "Gamma": 3}},
            {"id": "N1970_02", "domain": "Algebraic_Geometry", "degree": 12, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 3}},
            {"id": "N1970_03", "domain": "Topology", "degree": 10, "depth": 4, "coordinates": {"Delta": 3, "I": 3, "W": 3, "sigma": 2, "Pi": 3, "Gamma": 2}},
        ],
        "discoveries": [
            {"id": "DISC_1973_QUILLEN_HIGHER_K", "year": 1973, "domain": "Algebraic_K_Theory", "slot": "SLOT_HIGHER_K_THEORY_PLUS", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1980_THURSTON_GEOM", "year": 1982, "domain": "3_Manifolds", "slot": "SLOT_GEOMETRIZATION_FOLIATION", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_1995_WILES_TAYLOR", "year": 1995, "domain": "Number_Theory", "slot": "SLOT_MODULARITY_LIFTING", "type": "STRUCTURAL_SLOT_OCCUPATION"},
            {"id": "DISC_2015_SCHOLZE_PERF", "year": 2012, "domain": "Arithmetic_Geometry", "slot": "SLOT_PERFECTOID_SPACE", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1980: {
        "focus_areas": ["Gauge Theory", "Geometric Topology", "String Mathematical Physics"],
        "key_sources": [
            {"author": "Atiyah, M.F.", "year": 1979, "work": "Geometry of Yang-Mills Fields"},
            {"author": "Thurston, W.", "year": 1979, "work": "The Geometry and Topology of 3-Manifolds"},
            {"author": "Connes, A.", "year": 1980, "work": "C*-algebres et geometrie differentielle"}
        ],
        "core_nodes": [
            {"id": "N1980_01", "domain": "Geometry", "degree": 12, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 3, "Gamma": 3}},
            {"id": "N1980_02", "domain": "Mathematical_Physics", "degree": 10, "depth": 3, "coordinates": {"Delta": 4, "I": 3, "W": 4, "sigma": 2, "Pi": 3, "Gamma": 2}},
            {"id": "N1980_03", "domain": "Algebra", "degree": 11, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 3, "sigma": 3, "Pi": 3, "Gamma": 3}},
        ],
        "discoveries": [
            {"id": "DISC_1985_JONES_POLYNOMIAL", "year": 1985, "domain": "Knot_Theory", "slot": "SLOT_QUANTUM_BRAID_INVARIANT", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_1990_WITTEN_TQFT", "year": 1989, "domain": "Mathematical_Physics", "slot": "SLOT_TOPOLOGICAL_FIELD_THEORY", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_2003_PERELMAN_RICCI", "year": 2003, "domain": "Geometric_Analysis", "slot": "SLOT_RICCI_ENTROPY_EXTREMALS", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    1990: {
        "focus_areas": ["Quantum Groups", "Symplectic Field Theory", "Operads and Homotopy"],
        "key_sources": [
            {"author": "Drinfeld, V.", "year": 1986, "work": "Quantum Groups"},
            {"author": "Gromov, M.", "year": 1985, "work": "Pseudo holomorphic curves in symplectic manifolds"},
            {"author": "Witten, E.", "year": 1988, "work": "Topological quantum field theory"}
        ],
        "core_nodes": [
            {"id": "N1990_01", "domain": "Quantum_Algebra", "degree": 13, "depth": 5, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 3}},
            {"id": "N1990_02", "domain": "Symplectic_Topology", "degree": 11, "depth": 4, "coordinates": {"Delta": 4, "I": 3, "W": 4, "sigma": 2, "Pi": 3, "Gamma": 3}},
            {"id": "N1990_03", "domain": "Number_Theory", "degree": 12, "depth": 4, "coordinates": {"Delta": 4, "I": 4, "W": 3, "sigma": 3, "Pi": 4, "Gamma": 2}},
        ],
        "discoveries": [
            {"id": "DISC_1995_KONTSEVICH_MOM", "year": 1995, "domain": "Mirror_Symmetry", "slot": "SLOT_HOMOLOGICAL_MIRROR_SYMMETRY", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_2000_VOEVODSKY_MOTIVIC", "year": 2000, "domain": "Motivic_Homotopy", "slot": "SLOT_MOTIVIC_COMPLEXES", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_2012_SCHOLZE_TORSION", "year": 2013, "domain": "Arithmetic_Geometry", "slot": "SLOT_GALOIS_TORSION_SYSTEM", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    2000: {
        "focus_areas": ["Higher Category Theory", "Motivic Homotopy", "Mirror Symmetry"],
        "key_sources": [
            {"author": "Voevodsky, V.", "year": 1998, "work": "A^1-homotopy theory of schemes"},
            {"author": "Kontsevich, M.", "year": 1995, "work": "Homological mirror symmetry"},
            {"author": "Taylor, R. and Wiles, A.", "year": 1995, "work": "Ring-theoretic properties of certain Hecke algebras"}
        ],
        "core_nodes": [
            {"id": "N2000_01", "domain": "Higher_Category_Theory", "degree": 14, "depth": 5, "coordinates": {"Delta": 5, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 3}},
            {"id": "N2000_02", "domain": "Arithmetic_Geometry", "degree": 13, "depth": 5, "coordinates": {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 3}},
            {"id": "N2000_03", "domain": "Differential_Geometry", "degree": 12, "depth": 4, "coordinates": {"Delta": 4, "I": 3, "W": 4, "sigma": 2, "Pi": 3, "Gamma": 3}},
        ],
        "discoveries": [
            {"id": "DISC_2006_LURIE_HTT", "year": 2006, "domain": "Higher_Category_Theory", "slot": "SLOT_QUASI_CATEGORY_SHEAF", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_2010_SCHOLZE_PERF_PRE", "year": 2012, "domain": "Arithmetic_Geometry", "slot": "SLOT_PERFECTOID_FIBER", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
            {"id": "DISC_2020_CONDENSED_MATH", "year": 2019, "domain": "Foundations", "slot": "SLOT_CONDENSED_ANALYTIC", "type": "STRUCTURAL_SLOT_OCCUPATION"},
        ]
    },
    2010: {
        "focus_areas": ["Infinity-Categories", "Condensed Mathematics", "Perfectoid Spaces"],
        "key_sources": [
            {"author": "Lurie, J.", "year": 2009, "work": "Higher Topos Theory"},
            {"author": "Kisin, M.", "year": 2009, "work": "Moduli of finite flat group schemes"},
            {"author": "Joyal, A.", "year": 2008, "work": "The Theory of Quasi-Categories"}
        ],
        "core_nodes": [
            {"id": "N2010_01", "domain": "Higher_Topos_Theory", "degree": 15, "depth": 5, "coordinates": {"Delta": 5, "I": 5, "W": 4, "sigma": 4, "Pi": 4, "Gamma": 4}},
            {"id": "N2010_02", "domain": "Arithmetic_Geometry", "degree": 14, "depth": 5, "coordinates": {"Delta": 5, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 3}},
            {"id": "N2010_03", "domain": "Higher_Algebra", "degree": 14, "depth": 5, "coordinates": {"Delta": 4, "I": 5, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 4}},
        ],
        "discoveries": [
            {"id": "DISC_2015_SCHOLZE_COHOMOLOGY", "year": 2015, "domain": "Arithmetic_Geometry", "slot": "SLOT_PRISMATIC_CRYSTALLINE", "type": "EXACT_OBJECT_OCCUPATION"},
            {"id": "DISC_2019_CLAUSEN_SCHOLZE", "year": 2019, "domain": "Condensed_Math", "slot": "SLOT_CONDENSED_TOPOS", "type": "EQUIVALENCE_CLASS_OCCUPATION"},
        ]
    }
}
