# Latent Generator Qualification Campaign

## Question
Can MAPEOGEO recover the work-producing mathematical generator from an observed effect without requiring identification of the physical or semantic actor that caused it?

## Generic model
Observation: y(t)=P q(t).
Generator family: q(t;alpha).

The inverse stage returns (q_hat,N,u), where N is the observational null/equivalence space and u is uncertainty.

Certification performs y_hat=P q_hat and requires ||y_hat-y|| <= tau_W.

## Primary qualification cases
1. Variable-amplitude/phase sinusoid: recover identifiable scale/phase state and differential scale/rotation components.
2. Complex I/Q: recover amplitude, phase, and angular-rate representation while preserving branch ambiguity.
3. 3-D projected motion: separate translation/rotation/scale and report unobservable dimensions.
4. Vibration/modal observation: map measured trajectories to modal/operator coordinates and test reconstruction.
5. Electrical V/I observation: recover work-relevant impedance/power operator state without claiming source identity.

## Gates
- exact or specified-tolerance forward reconstruction;
- correct null-space dimension;
- no source/actor over-identification;
- geometry -> linear algebra -> geometry round-trip;
- calculus decomposition consistency;
- route/tolerance contract preservation;
- deterministic replay.

## Falsification
Fail if inverse machinery returns a unique source where observations admit multiple generators, if reconstruction exceeds tolerance, or if representation translation changes identifiable/null subspaces.
