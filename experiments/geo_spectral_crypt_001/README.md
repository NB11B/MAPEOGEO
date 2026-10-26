# GEO-SPECTRAL-CRYPT-001 — Spectra, relabeling, encryption

The exact similarity transform P⁻¹TP preserves the characteristic polynomial and trace(T^m). A fixed secret relabeling is still similarity, so spectral multiplicities survive exactly. Randomized authenticated encryption applied to serialized transition *observations* is not a similarity transform, and ciphertext bytes do not define the original transition matrix. A holder of the key may decrypt and reconstruct the original operator. Externally observable traffic timing/length patterns can survive encryption depending on protocol; this benchmark does not test traffic analysis or claim leakage.

Controls: cyclic shifts n=7,9,12; relabeling sweep all k for n=2..25; round-trip AES-256-GCM with fresh 96-bit nonces; ciphertext differences and fixed-length payloads. CI explicitly installs numpy and cryptography.

Security constraints: test uses fresh secret nonces; never reuse AES-GCM nonce for the same key. This experiment does not defeat encryption or recover plaintext spectral structure from ciphertext.

Run: pip install numpy cryptography && cd experiments/geo_spectral_crypt_001 && python -m unittest discover -v && python experiment.py

Next: separate encrypted computation on an explicitly conjugated representation, pseudorandom ciphertext byte-spectrum nulls, and qualified side-channel observation models. Keep state-coordinate transformation distinct from cryptographic encryption.
