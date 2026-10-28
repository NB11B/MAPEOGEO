# MAPEOGEO Compiled-Operator Pilot

Standalone, reproducible proof-of-concept. **Not** the original FFT Spectral LM,
MAPEOGEOv2 certified runtime, Lean, or a full Qwenputer-style processor.

## Install and run

```bash
python -m pip install numpy torch
python -m unittest -v test_pilot.py
python pilot.py --epochs 18 --out results.json
```

## Implemented

- Compiled, non-trainable ReLU Boolean gates for 8-bit addition, XOR and equality.
- Fixed Clifford(3,0) basis multiplication matrix (8 output coefficients, 64 blade pairs).
- Small trainable embedding/MLP selector mapping synonymous instruction words to four operators.
- End-to-end action selection followed by deterministic execution.
- Exhaustive 8-bit binary arithmetic/equality tests and Clifford basis associativity tests.
- Completely disjoint operand pairs between training and held-out evaluation.

## Important limitations

- This is *not* weight compilation into the user's FFT Spectral LM; compiled operators
  are independent fixed neural modules, not fused into a transformer.
- The controller sees distinctive operation words. Accuracy measures command routing,
  not abstract reasoning, unseen vocabulary, or compositional generalization.
- Full mathematical proof certification, graph traversal, learnable geometric operators,
  multi-step planning, GPU benchmarking, and explicit recurrent state remain unbuilt.
- Fixed-weight Clifford matrix is verified against its construction rule and
  associativity, not independently certified through MAPEOGEO/Lean.
- Some operations are exact only on binary input tensors; 8-bit arithmetic wraps mod 256.
- 3D basis-blade operands are projected from integer inputs by `% 8` in the pilot's
  controller integration benchmark. This is a toy workload convention.

## Files

`pilot.py` implementation and train/test entrypoint; `test_pilot.py` behavior tests;
`results.json` observed results; `results.pt` trained controller checkpoint.
