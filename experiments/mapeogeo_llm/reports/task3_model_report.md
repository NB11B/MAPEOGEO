# Task 3 model implementation report

## Scope and provenance

This task implements a **new** causal FFT language model from the supplied
engineering handoff. No original Spectral LM source or compatible checkpoint
was found in the bounded repository/history search, so this implementation is
not claimed to reproduce or accept historical weights.

Owned implementation files:

- `models/spectral_lm.py`
- `models/tokenizer.py`
- `models/action_head.py`
- `models/recurrent_policy.py`
- `tests/test_spectral.py`

No runtime, adapter, training, or pre-existing `recurrent/` file was changed by
this task.

## Implemented contracts

- `SpectralConfig` is a frozen dataclass with JSON-serializable `to_dict` and
  `from_dict` representations.
- `SpectralLM.hidden_states(input_ids, attention_mask=None)` returns `[B,T,D]`;
  `forward` applies a tied vocabulary projection and returns `[B,T,V]`.
- `SpectralLM.loss` implements shifted causal next-token cross entropy.
- `SpectralLM.generate` uses full-prefix recomputation. It does **not** claim
  constant-time caching. Masked prompts are compacted per batch row before
  decoding so right-padding gaps do not alter convolutional distances.
- Checkpoints contain configuration plus weights and reload with `weights_only`.
- `SentencePieceTokenizer` trains a real SentencePiece BPE model, with fixed
  `<PAD>`, `<UNK>`, `<BOS>`, `<EOS>` IDs and reserved `<ACTION>`, `<HALT>`,
  `<VERIFY>`, `<UNSOLVED>`, `<RESULT>`, and `<ERROR>` pieces.
- `ActionHead` provides per-token action logits and optional public-state
  pointer logits. Integration may layer more specialized typed heads over the
  exposed hidden states.
- `TransformerCausalLM` and `GRUCausalLM` are runnable autoregressive baselines
  with matching `forward`, `loss`, `generate`, and `num_parameters` contracts.

## Architecture and measured sizes

The default Spectral configuration is vocabulary 4096, model width 384, six
blocks, sequence length 512, SwiGLU width 1520, local causal depthwise kernel 3,
and multiresolution causal depthwise FFT kernels 16/32/128. FFT inputs and
filters are promoted to float32 before `rfft`/`irfft`, then converted back to
the activation dtype. Every FFT convolution is linearly zero-padded and sliced
to the input length, rather than circularly wrapped.

Measured trainable parameter counts from the actual implementation:

| Model | Parameters |
|---|---:|
| New Spectral LM | 13,605,696 |
| Transformer baseline | 12,343,200 |
| GRU baseline | 12,391,680 |

The new Spectral model is therefore approximately 13.6M parameters, while the
two baselines are within about 10% for useful matched-capacity comparisons.

## Test evidence

TDD red evidence was observed before implementation (`ModuleNotFoundError` for
the absent `models` package). A separate padding-generation regression was also
observed failing (`expected next token 5, received padding token 0`) before its
fix.

Focused command:

```powershell
& 'C:\Users\nateb\Documents\Codex\2026-10-28\mapeogeo-llm-full-engineering-handoff-for\work\.venv\Scripts\python.exe' `
  -m pytest -q experiments/mapeogeo_llm/tests/test_spectral.py
```

Initial result on 2026-10-28: `12 passed` in 5.00 seconds. The suite covers causal
future perturbation, right-padding invariance, prefix recomputation equivalence,
padded generation, EOS stopping, real gradient flow and optimizer updates,
checkpoint reload equivalence, SentencePiece round-trip and reserved pieces,
action-head shapes, Transformer/GRU contracts, default parameter range, and
CPU/CUDA numerical consistency. CUDA was available and the CUDA test ran rather
than skipping.

Compile and count command:

```powershell
python -m compileall -q experiments/mapeogeo_llm/models experiments/mapeogeo_llm/tests/test_spectral.py
```

Result: exit code 0. Runtime used PyTorch `2.11.0.dev20260127+cu128`; CUDA was
reported available. SentencePiece `0.2.1` was already installed, so no
dependency installation or fake tokenizer artifact was needed.

Warnings were limited to environment/dependency warnings: PyTorch's deprecation
notice for the separately installed `pynvml` package and SentencePiece SWIG
type deprecation notices under Python 3.13.

### Independent-review correction pass

Confirmed reviewer findings were reproduced with failing regression tests and
corrected:

- Transformer/GRU generation now compacts unequal masked prompts per row before
  decoding, and equal-length batched decoding tracks finished rows so they
  remain EOS while unfinished rows continue.
- Spectral, Transformer, and GRU losses supervise a transition only when both
  its source and target tokens are valid. An attention mask with no supervised
  pair raises `ValueError` instead of returning a NaN loss. Masked GRU inputs
  are compacted before recurrent processing so leading pads cannot advance the
  hidden state.
- SentencePiece model paths append `.model` to dotted prefixes rather than
  replacing the existing suffix.

The final focused verification used `OMP_NUM_THREADS=4` and
`MKL_NUM_THREADS=4`: `19 passed` in 5.03 seconds. `compileall` also exited 0.

Repository-wide command:

```powershell
python -m pytest -q experiments/mapeogeo_llm/tests
```

Result during concurrent integration: `97 passed, 1 failed`. The sole failure
was outside Task 3: `test_geo.py::test_native_build_is_byte_reproducible`
failed because the separately owned `scripts/build_geo.ps1` process could not
resolve the `Get-FileHash` cmdlet. No spectral, tokenizer, action-head, or
baseline test failed in the full run.

## Remaining boundaries

- No model has been trained in Task 3; learned quality and handoff gate R8 remain
  OPEN until integration training creates and evaluates real checkpoints.
- No historical weight compatibility is claimed.
- Generation deliberately recomputes prefixes and is not an O(1) streaming
  cache implementation.
- The action head is a compact primitive. The integration policy remains
  responsible for typed op/src/dst heads, public-state formatting, and ensuring
  target programs or private oracle labels never enter inference state.
