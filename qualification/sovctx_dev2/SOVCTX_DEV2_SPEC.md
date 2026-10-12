# SOVCTX-DEV2: Pedagogical Transition & Transfer Test Specification

## 1. Objective
Milestone **SOVCTX-DEV2** evaluates the developmental dynamics of Soviet mathematical pedagogy across three empirical dimensions:
1. **Agency Progression**: Empirical verification of the $\text{SUPPLIED} \to \text{HINTED} \to \text{INVENTED}$ trajectory across all active primitives.
2. **Transfer Demand Progression**: Verification of the $\text{SAME\_FORM} \to \text{NEAR\_TRANSFER} \to \text{FAR\_TRANSFER}$ progression and its strict coupling to scaffolding depth ($\text{DIRECT} \to \text{PARTIAL} \to \text{NONE}$).
3. **Noncommutative Grammar & Operation Ordering Concordance**: Testing whether the educational sequence systematically trains the structure-preserving, mathematically optimal order first, using the $16 \times 16$ Methodological Grammar Matrix $\Gamma$ discovered in **SOVCTX-M6.2**.

## 2. Regulatory Gates (20 Gates)
- `DEV2-GATE-01`: Corpus Scale Gate ($N=87$ episodes).
- `DEV2-GATE-02`: Active Primitives Gate ($\ge 12$ active primitives tracked).
- `DEV2-GATE-03`: Ordinary School Invention Exclusion Gate (Within Stages 1–3, invention rate is strictly 0.0%).
- `DEV2-GATE-04`: Olympiad Invention Surge Gate (Invention rate in Stage 4 is 100.0%).
- `DEV2-GATE-05`: Monotonic Scaffold Stripping Gate (100% of tracked primitives satisfy monotonic scaffold stripping).
- `DEV2-GATE-06`: $R_s$ Agency Trajectory Gate.
- `DEV2-GATE-07`: $A_x$ Agency Trajectory Gate.
- `DEV2-GATE-08`: $S_r$ Agency Trajectory Gate.
- `DEV2-GATE-09`: $I$ Agency Trajectory Gate.
- `DEV2-GATE-10`: $N$ Agency Trajectory Gate.
- `DEV2-GATE-11`: Transfer Demand Progression Gate.
- `DEV2-GATE-12`: Ordinary School Far Transfer Exclusion Gate (Far transfer is strictly 0.0% in Stages 1–3).
- `DEV2-GATE-13`: Scaffolding Partial Near Coupling Gate (`PARTIAL` scaffolding $\implies 100\%$ `NEAR_TRANSFER`).
- `DEV2-GATE-14`: Scaffolding None Far Coupling Gate (`NONE` scaffolding $\implies 100\%$ `FAR_TRANSFER`).
- `DEV2-GATE-15`: Directed Transitions Volume Gate ($\ge 160$ transitions).
- `DEV2-GATE-16`: M6.2 Grammar Concordance Rate Gate ($\ge 95\%$).
- `DEV2-GATE-17`: Structure-Preserving Order Gate ($\ge 95\%$).
- `DEV2-GATE-18`: High-Gamma Epistemic Gate ($\Gamma \ge 2$ concordance $= 100\%$).
- `DEV2-GATE-19`: Teacher Doctrine Order Contrast Gate (Pupil $S_r \to I$ vs Doctrine $I \to S_r$).
- `DEV2-GATE-20`: Hardware ARM Execution Budget Gate ($< 5.0\text{s}$ on Jetson Nano ARM Cortex-A57).
