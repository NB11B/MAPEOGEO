"""Explicitly new causal FFT language model for the MAPEOGEO experiment.

This is a clean implementation from the engineering handoff, not a recovered
historical model and not claimed to be checkpoint compatible with one.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class SpectralConfig:
    vocab_size: int = 4096
    d_model: int = 384
    n_layers: int = 6
    max_seq_len: int = 512
    ffn_hidden_dim: int | None = None
    kernel_sizes: tuple[int, ...] = (16, 32, 128)
    local_kernel_size: int = 3
    dropout: float = 0.0
    pad_token_id: int = 0

    def __post_init__(self) -> None:
        if min(self.vocab_size, self.d_model, self.n_layers, self.max_seq_len) <= 0:
            raise ValueError("vocabulary, model, layer, and sequence sizes must be positive")
        if not self.kernel_sizes or any(size <= 0 for size in self.kernel_sizes):
            raise ValueError("kernel_sizes must contain positive integers")
        if self.local_kernel_size <= 0:
            raise ValueError("local_kernel_size must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if not 0 <= self.pad_token_id < self.vocab_size:
            raise ValueError("pad_token_id must be in the vocabulary")

    @property
    def resolved_ffn_hidden_dim(self) -> int:
        return self.ffn_hidden_dim if self.ffn_hidden_dim is not None else 1520

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["kernel_sizes"] = list(self.kernel_sizes)
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SpectralConfig":
        copied = dict(value)
        if "kernel_sizes" in copied:
            copied["kernel_sizes"] = tuple(copied["kernel_sizes"])
        return cls(**copied)


def _causal_depthwise_fft(x: Tensor, weight: Tensor) -> Tensor:
    """Apply a zero-padded causal depthwise convolution in float32."""
    _, length, _ = x.shape
    kernel_size = weight.shape[-1]
    fft_length = 1 << (length + kernel_size - 2).bit_length()
    x_float = x.float().transpose(1, 2)
    weight_float = weight.float()
    x_spectrum = torch.fft.rfft(x_float, n=fft_length)
    weight_spectrum = torch.fft.rfft(weight_float, n=fft_length)
    output = torch.fft.irfft(x_spectrum * weight_spectrum.unsqueeze(0), n=fft_length)
    return output[..., :length].transpose(1, 2).to(dtype=x.dtype)


class _SpectralBlock(nn.Module):
    def __init__(self, config: SpectralConfig) -> None:
        super().__init__()
        d_model = config.d_model
        hidden = config.resolved_ffn_hidden_dim
        self.norm_spectral = nn.LayerNorm(d_model)
        self.spectral_weights = nn.ParameterList(
            [nn.Parameter(torch.empty(d_model, size)) for size in config.kernel_sizes]
        )
        self.local_weight = nn.Parameter(torch.empty(d_model, config.local_kernel_size))
        self.spectral_projection = nn.Linear(d_model, d_model)
        self.norm_ffn = nn.LayerNorm(d_model)
        self.gate_projection = nn.Linear(d_model, hidden)
        self.value_projection = nn.Linear(d_model, hidden)
        self.output_projection = nn.Linear(hidden, d_model)
        self.dropout = nn.Dropout(config.dropout)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for weight in self.spectral_weights:
            nn.init.normal_(weight, mean=0.0, std=0.02 / math.sqrt(weight.shape[-1]))
        nn.init.normal_(self.local_weight, mean=0.0, std=0.02)

    def forward(self, x: Tensor, mask: Tensor) -> Tensor:
        normalized = self.norm_spectral(x) * mask
        spectral = sum(
            _causal_depthwise_fft(normalized, weight) for weight in self.spectral_weights
        ) / math.sqrt(len(self.spectral_weights))
        local = _causal_depthwise_fft(normalized, self.local_weight)
        x = (x + self.dropout(self.spectral_projection(spectral + local))) * mask
        normalized = self.norm_ffn(x)
        ffn = F.silu(self.gate_projection(normalized)) * self.value_projection(normalized)
        return (x + self.dropout(self.output_projection(ffn))) * mask


class SpectralLM(nn.Module):
    """Decoder-only causal language model using prefix-recomputed FFT blocks."""

    def __init__(self, config: SpectralConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(
            config.vocab_size, config.d_model, padding_idx=config.pad_token_id
        )
        self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        self.blocks = nn.ModuleList([_SpectralBlock(config) for _ in range(config.n_layers)])
        self.final_norm = nn.LayerNorm(config.d_model)

    @property
    def num_parameters(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def _mask_and_positions(
        self, input_ids: Tensor, attention_mask: Tensor | None
    ) -> tuple[Tensor, Tensor]:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape [batch, sequence]")
        if input_ids.shape[1] == 0 or input_ids.shape[1] > self.config.max_seq_len:
            raise ValueError("sequence length must be between 1 and max_seq_len")
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids, dtype=torch.bool)
        elif attention_mask.shape != input_ids.shape:
            raise ValueError("attention_mask must match input_ids")
        else:
            attention_mask = attention_mask.to(device=input_ids.device, dtype=torch.bool)
        positions = attention_mask.long().cumsum(dim=1).sub(1).clamp_min(0)
        return attention_mask.unsqueeze(-1), positions

    def hidden_states(
        self, input_ids: Tensor, attention_mask: Tensor | None = None
    ) -> Tensor:
        mask, positions = self._mask_and_positions(input_ids, attention_mask)
        x = (self.token_embedding(input_ids) + self.position_embedding(positions)) * mask
        for block in self.blocks:
            x = block(x, mask)
        return self.final_norm(x) * mask

    def forward(self, input_ids: Tensor, attention_mask: Tensor | None = None) -> Tensor:
        hidden = self.hidden_states(input_ids, attention_mask)
        return F.linear(hidden, self.token_embedding.weight)

    def loss(
        self,
        input_ids: Tensor,
        labels: Tensor | None = None,
        attention_mask: Tensor | None = None,
        ignore_index: int = -100,
    ) -> Tensor:
        if input_ids.shape[1] < 2:
            raise ValueError("next-token loss requires at least two tokens")
        labels = input_ids if labels is None else labels
        if labels.shape != input_ids.shape:
            raise ValueError("labels must match input_ids")
        targets = labels[:, 1:].clone()
        if attention_mask is not None:
            if attention_mask.shape != input_ids.shape:
                raise ValueError("attention_mask must match input_ids")
            token_mask = attention_mask.to(device=input_ids.device, dtype=torch.bool)
            supervised_pairs = token_mask[:, :-1] & token_mask[:, 1:]
            if not bool(supervised_pairs.any()):
                raise ValueError("attention_mask contains no supervised next-token pair")
            targets.masked_fill_(~supervised_pairs, ignore_index)
        logits = self(input_ids, attention_mask)[:, :-1]
        return F.cross_entropy(
            logits.reshape(-1, self.config.vocab_size),
            targets.reshape(-1),
            ignore_index=ignore_index,
        )

    @torch.no_grad()
    def generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int,
        eos_token_id: int | None,
        attention_mask: Tensor | None = None,
    ) -> Tensor:
        if max_new_tokens < 0:
            raise ValueError("max_new_tokens must be non-negative")
        if attention_mask is not None:
            if attention_mask.shape != input_ids.shape:
                raise ValueError("attention_mask must match input_ids")
            prompt_mask = attention_mask.to(device=input_ids.device, dtype=torch.bool)
            if not bool(prompt_mask.all()):
                sequences = []
                for row, row_mask in zip(input_ids, prompt_mask, strict=True):
                    prompt = row[row_mask].unsqueeze(0)
                    if prompt.shape[1] == 0:
                        raise ValueError("each generation prompt needs at least one token")
                    sequences.append(
                        self.generate(prompt, max_new_tokens, eos_token_id).squeeze(0)
                    )
                return nn.utils.rnn.pad_sequence(
                    sequences,
                    batch_first=True,
                    padding_value=self.config.pad_token_id,
                )
        tokens = input_ids
        mask = (
            torch.ones_like(tokens, dtype=torch.bool)
            if attention_mask is None
            else attention_mask.to(device=tokens.device, dtype=torch.bool)
        )
        finished = torch.zeros(tokens.shape[0], dtype=torch.bool, device=tokens.device)
        for _ in range(max_new_tokens):
            if tokens.shape[1] >= self.config.max_seq_len:
                break
            logits = self(tokens, mask)
            next_token = logits[:, -1].argmax(dim=-1)
            if eos_token_id is not None:
                next_token = torch.where(
                    finished, torch.full_like(next_token, eos_token_id), next_token
                )
                finished |= next_token.eq(eos_token_id)
            tokens = torch.cat((tokens, next_token[:, None]), dim=1)
            mask = torch.cat(
                (mask, torch.ones((mask.shape[0], 1), dtype=torch.bool, device=mask.device)),
                dim=1,
            )
            if eos_token_id is not None and bool(finished.all()):
                break
        return tokens

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"config": self.config.to_dict(), "state_dict": self.state_dict()}, path)

    @classmethod
    def load(
        cls, path: str | Path, map_location: str | torch.device = "cpu"
    ) -> "SpectralLM":
        checkpoint = torch.load(path, map_location=map_location, weights_only=True)
        model = cls(SpectralConfig.from_dict(checkpoint["config"]))
        model.load_state_dict(checkpoint["state_dict"])
        return model
