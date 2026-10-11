# Pre-Soviet Ancestry Layer

This layer records mathematical/scientific ancestry that predates the Soviet period and materially shaped later Russian/Petersburg traditions.

It is **not** the Western-comparison namespace.

## Edge discipline

- `DOCUMENTED_ANCESTRY`: a source explicitly names or uses the earlier person/work/concept.
- `TRANSMITTED_THROUGH`: documentary evidence supports an institutional or pedagogical transmission path.
- `STRUCTURAL_ANCESTRY`: SOVCTX observes a behavioral/mathematical resemblance but direct transmission is not established.
- `CONTEXTUALLY_AVAILABLE_TO`: the earlier work was demonstrably available in the relevant intellectual environment, without claiming influence.

These edge types must never be silently promoted into one another.

## Initial backbone

```
Leibniz
  |
  | documented in Euler's geometria-situs paper
  v
Euler
  |
  | St. Petersburg Academy publication/institutional line
  v
Petersburg mathematical tradition
  |
  | later historical work to be ingested
  v
Chebyshev -> Markov / Lyapunov -> later Russian/Soviet schools
```

Current documented chain includes:

```
Markov ----\
            > Chebyshev -> Euler -> Leibniz
Lyapunov --/
```

- Euler -> Leibniz: Euler's own `geometria situs` paper explicitly attributes the concept to Leibniz.
- Chebyshev -> Euler: Kozlov's Russian Mathematical Surveys institutional history states that Chebyshev actively edited and published Euler's works.
- Markov/Lyapunov -> Chebyshev: the same source identifies them among Chebyshev's students.

These are ancestry/transmission facts. They do not mean every later theorem of Markov or Lyapunov is derived from Leibniz.

## Equation ancestry

The equation atlas begins with Leibniz's differential operator rules, preserving source notation separately from normalized notation.

Behavioral qualification asks what the rule does under substitution, symmetry, scaling, composition, limits, or other declared transformations. It does not impose a later mathematical foundation as a prerequisite for cataloguing the rule.
