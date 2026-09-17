from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import itertools
from typing import Any


def permutation_parity(p: list[int] | tuple[int, ...]) -> int:
    """Returns +1 for even permutations and -1 for odd permutations."""
    n = len(p)
    visited = [False] * n
    parity = 1
    for i in range(n):
        if not visited[i]:
            cycle_len = 0
            curr = i
            while not visited[curr]:
                visited[curr] = True
                curr = p[curr]
                cycle_len += 1
            if cycle_len % 2 == 0:
                parity = -parity
    return parity


@dataclass(frozen=True)
class Simplex:
    vertices: tuple[int, ...]

    @property
    def dimension(self) -> int:
        return len(self.vertices) - 1

    @property
    def canonical(self) -> Simplex:
        return Simplex(tuple(sorted(self.vertices)))

    def sign_relative_to(self, other: Simplex) -> int:
        if set(self.vertices) != set(other.vertices):
            raise ValueError("Simplices must have identical vertex sets to compare orientation")
        if len(self.vertices) <= 1:
            return 1
        sorted_verts = sorted(self.vertices)
        p1 = [sorted_verts.index(v) for v in self.vertices]
        p2 = [sorted_verts.index(v) for v in other.vertices]
        inv_p2 = [0] * len(p2)
        for idx, val in enumerate(p2):
            inv_p2[val] = idx
        perm = [inv_p2[v] for v in p1]
        return permutation_parity(perm)

    def boundary_facets(self) -> list[tuple[int, Simplex]]:
        r"""Returns list of (sign, facet_simplex) for \partial \sigma."""
        facets = []
        for i in range(len(self.vertices)):
            sign = (-1) ** i
            facet_verts = self.vertices[:i] + self.vertices[i + 1 :]
            facets.append((sign, Simplex(facet_verts)))
        return facets


class SimplicialComplex:
    def __init__(self, simplices: list[Simplex]):
        self.simplices_by_dim: dict[int, list[Simplex]] = {}
        for s in simplices:
            d = s.dimension
            if d not in self.simplices_by_dim:
                self.simplices_by_dim[d] = []
            if s.canonical not in [x.canonical for x in self.simplices_by_dim[d]]:
                self.simplices_by_dim[d].append(s.canonical)
        # Sort each dimension list canonically
        for d in self.simplices_by_dim:
            self.simplices_by_dim[d].sort(key=lambda s: s.vertices)

    @classmethod
    def standard_simplex(cls, dim: int) -> SimplicialComplex:
        r"""Constructs the full simplicial complex of standard \Delta^dim."""
        all_simplices = []
        verts = list(range(dim + 1))
        for k in range(1, dim + 2):
            for subset in itertools.combinations(verts, k):
                all_simplices.append(Simplex(subset))
        return cls(all_simplices)

    @property
    def max_dimension(self) -> int:
        return max(self.simplices_by_dim.keys()) if self.simplices_by_dim else 0


def boundary_matrix(K: SimplicialComplex, k: int) -> list[list[Fraction]]:
    r"""Matrix representing \partial_k : C_k -> C_{k-1} over Q."""
    if k <= 0 or k not in K.simplices_by_dim or (k - 1) not in K.simplices_by_dim:
        return []

    target_simplices = K.simplices_by_dim[k - 1]
    source_simplices = K.simplices_by_dim[k]

    target_idx = {s.canonical: i for i, s in enumerate(target_simplices)}
    rows = len(target_simplices)
    cols = len(source_simplices)

    mat = [[Fraction(0, 1) for _ in range(cols)] for _ in range(rows)]

    for col, sigma in enumerate(source_simplices):
        for sign, facet in sigma.boundary_facets():
            canon_facet = facet.canonical
            if canon_facet in target_idx:
                row = target_idx[canon_facet]
                facet_sign = facet.sign_relative_to(canon_facet)
                mat[row][col] += Fraction(sign * facet_sign, 1)

    return mat


def exterior_derivative_matrix(K: SimplicialComplex, k: int) -> list[list[Fraction]]:
    """Matrix representing d_k : C^k -> C^{k+1} over Q (transpose of boundary operator)."""
    # d_k is from k-cochains to (k+1)-cochains, matrix size |C_{k+1}| x |C_k|
    b_mat = boundary_matrix(K, k + 1)
    if not b_mat:
        return []
    # Transpose of B_{k, k+1} is D_{k+1, k}
    rows = len(b_mat)      # |C_k|
    cols = len(b_mat[0])   # |C_{k+1}|
    # D will have |C_{k+1}| rows and |C_k| columns
    d_mat = [[b_mat[r][c] for r in range(rows)] for c in range(cols)]
    return d_mat


def boundary_operator(K: SimplicialComplex, k: int) -> list[list[Fraction]]:
    return boundary_matrix(K, k)


def discrete_exterior_derivative(K: SimplicialComplex, k: int) -> list[list[Fraction]]:
    return exterior_derivative_matrix(K, k)


def mat_mul(A: list[list[Fraction]], B: list[list[Fraction]]) -> list[list[Fraction]]:
    if not A or not B or not A[0] or not B[0]:
        return []
    rA, cA = len(A), len(A[0])
    rB, cB = len(B), len(B[0])
    if cA != rB:
        raise ValueError(f"Matrix dimension mismatch: {cA} != {rB}")
    C = [[Fraction(0, 1) for _ in range(cB)] for _ in range(rA)]
    for i in range(rA):
        for j in range(cB):
            for k in range(cA):
                C[i][j] += A[i][k] * B[k][j]
    return C


def is_zero_matrix(M: list[list[Fraction]]) -> bool:
    for row in M:
        for val in row:
            if val != 0:
                return False
    return True


def verify_nilpotency(K: SimplicialComplex, operator_type: str = "boundary") -> bool:
    max_d = K.max_dimension
    if operator_type == "boundary":
        for k in range(2, max_d + 1):
            B_k = boundary_matrix(K, k)
            B_k_minus_1 = boundary_matrix(K, k - 1)
            if B_k and B_k_minus_1:
                comp = mat_mul(B_k_minus_1, B_k)
                if not is_zero_matrix(comp):
                    return False
        return True
    elif operator_type == "coboundary":
        for k in range(0, max_d - 1):
            D_k = exterior_derivative_matrix(K, k)
            D_k_plus_1 = exterior_derivative_matrix(K, k + 1)
            if D_k and D_k_plus_1:
                comp = mat_mul(D_k_plus_1, D_k)
                if not is_zero_matrix(comp):
                    return False
        return True
    return False


def verify_incidence_transpose(K: SimplicialComplex) -> bool:
    max_d = K.max_dimension
    for k in range(0, max_d):
        B = boundary_matrix(K, k + 1)
        D = exterior_derivative_matrix(K, k)
        if not B or not D:
            continue
        # Check D == B^T
        rB, cB = len(B), len(B[0])
        rD, cD = len(D), len(D[0])
        if rD != cB or cD != rB:
            return False
        for i in range(rB):
            for j in range(cB):
                if B[i][j] != D[j][i]:
                    return False
    return True


def verify_stokes_duality(K: SimplicialComplex) -> bool:
    r"""Verifies discrete Stokes pairing <d alpha, sigma> = <alpha, \partial sigma> for all basis chains and cochains."""
    max_d = K.max_dimension
    for k in range(0, max_d):
        B = boundary_matrix(K, k + 1)
        D = exterior_derivative_matrix(K, k)
        if not B or not D:
            continue
        # For each basis cochain alpha_i (unit vector in C^k) and basis chain sigma_j (unit vector in C_{k+1}):
        # <d alpha_i, sigma_j> is the (j, i) entry of D, which is D[j][i]
        # <alpha_i, \partial sigma_j> is the (i, j) entry of B, which is B[i][j]
        for i in range(len(B)):          # C_k basis
            for j in range(len(B[0])):     # C_{k+1} basis
                pairing_lhs = D[j][i]
                pairing_rhs = B[i][j]
                if pairing_lhs != pairing_rhs:
                    return False
    return True
