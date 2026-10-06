# Work Router Power & Control v0.3

This overlay adds two application families.

## Electrical power

Certified minimal routes include phasor complex power `S=V*conj(I)`, real and
reactive power, apparent power from magnitudes, power factor, and waveform RMS.
THD deliberately requires harmonic/spectral state; an RMS->THD shortcut is
included only as an uncertified adversarial edge because equal-RMS waveforms can
have different harmonic distributions.

## Linear control

If PSMSL already carries the planar generator real part `g`, local stability
routes directly through `g<0`.  A general state matrix routes through
eigenvalues and spectral abscissa.  Time-trajectory work additionally requires
an initial state and materializes trajectory state.

These are mathematical/router qualifications.  No new physical power-system or
control-plant qualification is claimed by this overlay.
