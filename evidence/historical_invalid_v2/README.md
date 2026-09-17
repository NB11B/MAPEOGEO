# Historical V2 artifact — quarantined

This directory preserves the exact GitHub Actions artifact archive emitted by
the historical V2 run. It is retained for provenance inspection only.

- frozen commit: `f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5`
- Actions run: `35059952763`
- artifact ID: `10431654598`
- archive SHA-256: `baf020fa8007e3f721b44264c168249c4abf6689787f23db76f0ba4adee60235`
- original GitHub expiry: `2026-12-15T05:32:57Z`
- current validation status: `NOT_VALID_UNDER_CURRENT_STANDARD`

The archive's `SUPPORTED` label records what the frozen implementation emitted;
it is not a current capability claim. Hardened review found non-candidate bridge
lineage in G8/G9, insufficient frozen terminal checks for G4/G10/G11, and
incomplete runtime macro authority. The current runtime therefore refuses to
rescore or regenerate V2. Dependency ranges in the frozen revision also mean
that the commit alone does not identify an exactly reproducible environment.
