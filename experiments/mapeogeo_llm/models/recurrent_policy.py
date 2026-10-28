"""Runnable autoregressive Transformer and GRU language-model baselines."""

from __future__ import annotations

import math
import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .spectral_lm import SpectralConfig


class _CausalBaseline(nn.Module):
    config: SpectralConfig

    @property
    def num_parameters(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def loss(self, input_ids: Tensor, labels: Tensor | None = None, attention_mask: Tensor | None = None, ignore_index: int = -100) -> Tensor:
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
        return F.cross_entropy(logits.reshape(-1, self.config.vocab_size), targets.reshape(-1), ignore_index=ignore_index)

    @torch.no_grad()
    def generate(self, input_ids: Tensor, max_new_tokens: int, eos_token_id: int | None, attention_mask: Tensor | None = None) -> Tensor:
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
        mask = torch.ones_like(tokens, dtype=torch.bool) if attention_mask is None else attention_mask.bool()
        finished = torch.zeros(tokens.shape[0], dtype=torch.bool, device=tokens.device)
        for _ in range(max_new_tokens):
            if tokens.shape[1] >= self.config.max_seq_len:
                break
            next_token = self(tokens, mask)[:, -1].argmax(dim=-1)
            if eos_token_id is not None:
                next_token = torch.where(
                    finished, torch.full_like(next_token, eos_token_id), next_token
                )
                finished |= next_token.eq(eos_token_id)
            tokens = torch.cat((tokens, next_token[:, None]), dim=1)
            mask = torch.cat((mask, torch.ones((mask.shape[0], 1), dtype=torch.bool, device=mask.device)), dim=1)
            if eos_token_id is not None and bool(finished.all()):
                break
        return tokens


class TransformerCausalLM(_CausalBaseline):
    def __init__(self, config: SpectralConfig, n_heads: int = 8) -> None:
        super().__init__()
        if config.d_model % n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model, padding_idx=config.pad_token_id)
        self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        layer = nn.TransformerEncoderLayer(config.d_model, n_heads, dim_feedforward=config.resolved_ffn_hidden_dim, dropout=config.dropout, activation=F.silu, batch_first=True, norm_first=True)
        self.transformer = nn.TransformerEncoder(
            layer, config.n_layers, enable_nested_tensor=False
        )
        self.final_norm = nn.LayerNorm(config.d_model)

    def forward(self, input_ids: Tensor, attention_mask: Tensor | None = None) -> Tensor:
        if input_ids.ndim != 2 or not 0 < input_ids.shape[1] <= self.config.max_seq_len:
            raise ValueError("input_ids must have valid [batch, sequence] shape")
        mask = torch.ones_like(input_ids, dtype=torch.bool) if attention_mask is None else attention_mask.to(input_ids.device, dtype=torch.bool)
        if mask.shape != input_ids.shape:
            raise ValueError("attention_mask must match input_ids")
        positions = mask.long().cumsum(1).sub(1).clamp_min(0)
        hidden = (self.token_embedding(input_ids) + self.position_embedding(positions)) * mask.unsqueeze(-1)
        causal_mask = torch.ones(input_ids.shape[1], input_ids.shape[1], dtype=torch.bool, device=input_ids.device).triu(1)
        hidden = self.transformer(hidden, mask=causal_mask, src_key_padding_mask=~mask)
        hidden = self.final_norm(hidden) * mask.unsqueeze(-1)
        return F.linear(hidden, self.token_embedding.weight)


class GRUCausalLM(_CausalBaseline):
    def __init__(self, config: SpectralConfig) -> None:
        super().__init__()
        self.config = config
        self.hidden_dim = max(8, int(round(config.d_model * math.sqrt(2) / 8)) * 8)
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model, padding_idx=config.pad_token_id)
        self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
        self.gru = nn.GRU(config.d_model, self.hidden_dim, num_layers=config.n_layers, dropout=config.dropout if config.n_layers > 1 else 0.0, batch_first=True)
        self.output_projection = nn.Linear(self.hidden_dim, config.d_model)
        self.final_norm = nn.LayerNorm(config.d_model)

    def forward(self, input_ids: Tensor, attention_mask: Tensor | None = None) -> Tensor:
        if input_ids.ndim != 2 or not 0 < input_ids.shape[1] <= self.config.max_seq_len:
            raise ValueError("input_ids must have valid [batch, sequence] shape")
        mask = torch.ones_like(input_ids, dtype=torch.bool) if attention_mask is None else attention_mask.to(input_ids.device, dtype=torch.bool)
        if mask.shape != input_ids.shape:
            raise ValueError("attention_mask must match input_ids")
        positions = mask.long().cumsum(1).sub(1).clamp_min(0)
        embedded = (self.token_embedding(input_ids) + self.position_embedding(positions)) * mask.unsqueeze(-1)
        if bool(mask.all()):
            hidden, _ = self.gru(embedded)
        else:
            hidden = embedded.new_zeros(
                embedded.shape[0], embedded.shape[1], self.hidden_dim
            )
            for row_index, row_mask in enumerate(mask):
                compact = embedded[row_index, row_mask].unsqueeze(0)
                if compact.shape[1] == 0:
                    continue
                compact_hidden, _ = self.gru(compact)
                hidden[row_index, row_mask] = compact_hidden.squeeze(0)
        hidden = self.final_norm(self.output_projection(hidden)) * mask.unsqueeze(-1)
        return F.linear(hidden, self.token_embedding.weight)
