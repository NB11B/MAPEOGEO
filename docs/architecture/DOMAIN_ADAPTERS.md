# Domain Adapters Architecture

The Domain Adapters Layer (`mapeogeo.domains`) provides bidirectional translation between external domain semantics and the canonical Unit-of-Work kernel.

---

## 1. Governing Rule of Adaptation

$$\boxed{\text{Domains adapt to the kernel; the kernel does not adapt to domains.}}$$

The kernel remains completely agnostic to whether work represents mathematical deduction, physical parameter estimation, or software compilation. The adapter acts as a transducer, projecting domain problems into formal deficiency distributions $\Omega \to D$ and packaging domain results into $\mathcal M_6$ machinery units.

---

## 2. Canonical Adapter Contract

Every domain adapter implements a unified interface:

1. **Deficiency Projection**: Translates domain problem descriptions into formal `WorkRequirement` sets in $\Omega$.
2. **State Projection**: Maps certified machinery nodes $G_t$ to domain knowledge representations.
3. **Candidate Packaging**: Wraps domain-specific procedures and verification witnesses into `MachineryCandidate` structures.
4. **Independent Certification Boundary**: Enforces domain-specific truth criteria before emitting kernel candidates.

---

## 3. Strict Domain Isolation

Domain adapters are strictly isolated from one another:

$$\begin{aligned}
\texttt{domains.mathematics} &\;\not\leftrightarrow\; \texttt{domains.physics} \\
\texttt{domains.physics} &\;\not\leftrightarrow\; \texttt{domains.software} \\
\texttt{domains.software} &\;\not\leftrightarrow\; \texttt{domains.mathematics}
\end{aligned}$$

No domain adapter may import or depend upon another domain adapter. Shared representations exist solely in `kernel`, `grammar`, `graph`, `psmsl`, `routing`, or `proof`.
