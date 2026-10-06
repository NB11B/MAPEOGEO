# Work Router Multi-Domain v0.2

This bounded overlay broadens the router into two additional application
families while keeping physical qualification separate from mathematical route
qualification.

## Vector / inertial sensing

Qualified work routes:

- 3-D vector -> norm;
- norm -> threshold decision;
- vector pair -> normalized alignment.

A single vector pair is deliberately **not** certified as sufficient to recover
a unique full 3-D rotation.  That candidate route returns `CERTIFY` rather
than silently choosing one of infinitely many rotations.

The intended physical source for prospective qualification is UCI dataset 341,
which publishes raw triaxial accelerometer and gyroscope samples at 50 Hz.

## Vibration / condition monitoring

Qualified routes:

- window -> energy -> RMS -> threshold;
- window -> spectrum -> dominant frequency.

RMS/energy work does not traverse spectral materialization.  A frequency-domain
question does.

The intended physical source for prospective qualification is NASA's public IMS
bearing experiment dataset.

No physical-pass claim is made here until those source archives are acquired
and run prospectively.
