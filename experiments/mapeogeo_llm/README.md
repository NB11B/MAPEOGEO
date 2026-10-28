# MAPEOGEO-LLM: Compositional Operator Generalization Experiment

This experiment evaluates the second milestone of MAPEOGEO-LLM: testing whether a neural controller can compositionally generalize to unseen operator combinations and structures when executing over fixed, zero-parameter compiled operators.

## 1. Architecture

- **Compiled Operator Circuits (`operators.py`)**:
  - Six exact 8-bit operators (`ADD`, `SUB`, `XOR`, `AND`, `OR`, `EQ`), constructed purely from ReLU/affine Boolean logic gates with **0 trainable parameters**.
  - Verified exhaustively against plain-Python ground truth across all $6 \times 65,536 = 393,216$ possible 8-bit input pairs.
- **Learned Controller (`compositional.py`)**:
  - Small Transformer encoder-decoder that translates natural-language-like multi-step goal descriptions (both forward and reverse formulations) into dataflow programs.
  - The controller never performs arithmetic itself; it emits executable execution-order programs referencing operands and intermediate registers (`RES`).
- **Baselines**:
  - **Majority-class**: Always emits the most frequent answer from training.
  - **End-to-End Neural Transformer**: A standard Transformer reading prompt tokens and 8-bit operand bits directly predicting the 8-bit output, without any fixed operator circuits.

## 2. Benchmark Splits (1,000 test cases per split, evaluated across 3 random seeds)

- `iid`: Combinations seen during training (lengths 1–3).
- `L2_heldout_pair`: Length-2 chains whose `(op1, op2)` pair was strictly withheld from training (e.g., `(ADD, XOR)` withheld, though `ADD` and `XOR` appear individually).
- `L3_heldout_pair`: Length-3 chains containing at least one withheld adjacent pair.
- `L3_unseen_triple`: Length-3 chains where every adjacent pair was seen, but the 3-step combination was withheld.
- `L4_length`: Length-4 chains (length generalization; max training length was 3).

## 3. Verified Results (3-seed summary)

| Split | Controller Exact Program | Controller End-to-End Answer | Majority Answer | End-to-End Neural Baseline |
| :--- | :--- | :--- | :--- | :--- |
| **`iid`** | **98.4%** [96.4% – 99.6%] | **99.3%** [98.2% – 99.9%] | 24.6% | 25.9% [20.8% – 28.6%] |
| **`L2_heldout_pair`** | **98.6%** [96.0% – 100.0%] | **98.8%** [96.3% – 100.0%] | 15.5% | 11.5% [2.1% – 19.6%] |
| **`L3_heldout_pair`** | **95.2%** [92.3% – 98.9%] | **97.5%** [95.6% – 99.6%] | 18.9% | 18.5% [12.6% – 25.6%] |
| **`L3_unseen_triple`** | **95.7%** [90.8% – 99.0%] | **97.6%** [94.0% – 99.5%] | 17.5% | 19.0% [5.4% – 34.4%] |
| **`L4_length`** | 0.0% | 26.5% [25.1% – 27.3%] | 21.3% | 19.8% [18.8% – 20.9%] |

### Key Findings
1. **Strong Compositional Generalization**: On unseen operator pairs and triples (`L2_heldout_pair`, `L3_heldout_pair`, `L3_unseen_triple`), the controller achieves **97.5% – 98.8%** execution accuracy, nearly matching seen combinations (`iid`: 99.3%).
2. **Failure of Pure Neural Arithmetic**: The end-to-end neural network fails across all splits (~11% – 26%), barely outperforming the majority baseline, proving that learned neural weights struggle to simulate modular multi-step bit logic without compiled operator grounding.
3. **Length Generalization Frontier**: Length-4 extrapolation completely fails (0.0% exact program, ~26% answer), demonstrating that standard sequence decoders do not extrapolate chain length without explicit looping or recurrent execution structure (e.g. Qwenputer-style recurrent loop).
