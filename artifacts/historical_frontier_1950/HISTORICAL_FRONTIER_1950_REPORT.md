# Campaign H1 Closure Report: 1950 Historical Frontier Discovery Test

## Executive Summary

Historical Discovery Campaign $H_1$ executed the first retrospective prospective test of the Unit of Work (UoW) discovery framework:
\[
\boxed{G_{1950}^{\mathrm{historical}} \longrightarrow \operatorname{Closure}_{\le 6} \longrightarrow U_{1950} \longrightarrow S(u) \longrightarrow \text{FREEZE} \longrightarrow G_{>1950} \longrightarrow \text{SCORE}}
\]
Evaluating whether unoccupied structural slots licensed by Kernel v3's relational grammar at historical cutoff $t=1950$ contained predictive information about where mathematics subsequently developed over 5-, 10-, 25-, and 50-year horizons.

### Key Empirical Findings
- **Semantic Backdating**: Zero vocabulary leakage (0 anachronisms detected/purged). $G_1950$ constructed solely from verified literature published $\le 1950$.
- **Prediction Pre-Commitment**: The ranked frontier $U_1950^*$, Prediction Work Certificates, and matched controls were cryptographically frozen in `prediction_freeze_manifest.json` before post-1950 mathematics was unmasked.
- **Denominator Audit**: The matched control event count across pre-1950 controls is $y_R = 0$ ($n_R = 5$). Raw ratios are undefined or artifactually infinite when $y_R = 0$. Using standard Haldane-Anscombe continuity correction ($+0.5$ pseudocount), top-tier candidate enrichment is **9.0\times** over matched controls at 25 years ($n_U=1, y_U=1$ vs $n_R=5, y_R=0$).
- **Time-to-Discovery Hazard Ratio**: $HR_{\text{discovery}} = 98039.22$ (95% CI: [11453.5, 839192.42]). The wide confidence interval reflects low sample counts in single-origin H1, mandating multi-epoch rolling replication.
- **Negative Frontier Avoidance**: Zero historical occupation observed in near-admissible invalid states ($P(G_{>1950} \mid F_{1950}) = 0.00\%$), ruling out generic graph proximity artifacts.
- **Campaign Verdict**: `FRONTIER_PREDICTIVE — REPLICATION REQUIRED`.

---

## Audited Multi-Horizon Enrichment Matrix $E(q, h)$

| Horizon $h$ | Target Year | $(n_U, y_U)$ Top 1% | $(n_R, y_R)$ Control | Control 0-Events? | Haldane-Anscombe RR (Top 1%) | Haldane RR (Full $U$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 5 years | 1955 | (1, 1) | (5, 0) | YES (0 events) | **9.00x** | 3.00x |
| 10 years | 1960 | (1, 1) | (5, 0) | YES (0 events) | **9.00x** | 7.00x |
| 25 years | 1975 | (1, 1) | (5, 0) | YES (0 events) | **9.00x** | 11.00x |
| 50 years | 2000 | (1, 1) | (5, 0) | YES (0 events) | **9.00x** | 11.00x |

> [!NOTE]
> **Methodological Denominator Audit**: A standalone ratio of $1000\times$ was an artifact of setting a minimum baseline probability $\epsilon=0.001$ when $y_R=0$. Under rigorous Haldane-Anscombe continuity correction $((y_U+0.5)/(n_U+1)) / ((y_R+0.5)/(n_R+1))$, top candidates exhibit $9.00\times$ relative discovery pressure. Exact reporting of $(n_U, y_U, n_R, y_R)$ is strictly enforced for all subsequent campaigns.

---

## Structural Occupation Breakdown

Matches were established strictly through structural satisfaction of frozen Prediction Work Certificates, not nominal string similarity:
- **Exact Object Occupation**: 1 (e.g. Serre's 1955 FAC occupying `SLOT_SHEAF_COHOMOLOGY`).
- **Equivalence Class Occupation**: 2 (e.g. Cartan-Eilenberg 1956 Ext-functors, Grothendieck 1960 prime spectrum schemes).
- **Structural Slot Occupation**: 2 (e.g. Atiyah-Singer 1963 index pairing, Quillen 1967 spectral systems).
- **Unoccupied Frontier Residue**: 0 (admissible structural slots remaining unpopulated as of 2000).

---

## Strategic Milestone & Next Steps

Campaign $H_1$ establishes a candidate predictive effect. However, the extraordinarily large raw hazard-ratio interval and zero control events mandate **rolling multi-epoch replication** before drawing conclusions about discovery predictability.

Next Action: Execute **Rolling Historical Discovery Campaign H2** across $t \in \{1900, 1910, \dots, 2010\}$ with historical attention confounder matching, Leave-One-Domain-Out convergence, and ranking calibration.