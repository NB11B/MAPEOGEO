import tempfile
import unittest
from pathlib import Path

import torch
from torch.nn.utils.rnn import pad_sequence

from experiments.mapeogeo_llm.models.action_head import ActionHead
from experiments.mapeogeo_llm.models.recurrent_policy import (
    GRUCausalLM,
    TransformerCausalLM,
)
from experiments.mapeogeo_llm.models.spectral_lm import SpectralConfig, SpectralLM
from experiments.mapeogeo_llm.models.tokenizer import (
    RESERVED_TOKENS,
    SentencePieceTokenizer,
)


class TestSpectralLM(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(7)
        self.config = SpectralConfig(
            vocab_size=64,
            d_model=24,
            n_layers=2,
            max_seq_len=32,
            ffn_hidden_dim=48,
            kernel_sizes=(3, 5, 9),
            dropout=0.0,
        )
        self.model = SpectralLM(self.config).eval()

    def test_future_tokens_do_not_change_past_logits(self):
        first = torch.tensor([[3, 4, 5, 6, 7, 8]])
        second = first.clone()
        second[:, 4:] = torch.tensor([41, 42])
        with torch.no_grad():
            first_logits = self.model(first)
            second_logits = self.model(second)
        torch.testing.assert_close(first_logits[:, :4], second_logits[:, :4])

    def test_right_padding_does_not_change_unpadded_logits(self):
        tokens = torch.tensor([[3, 4, 5, 6]])
        padded = torch.tensor([[3, 4, 5, 6, 0, 0, 0]])
        mask = torch.tensor([[1, 1, 1, 1, 0, 0, 0]])
        with torch.no_grad():
            plain_logits = self.model(tokens)
            padded_logits = self.model(padded, attention_mask=mask)
        torch.testing.assert_close(plain_logits, padded_logits[:, :4])

    def test_prefix_recomputation_matches_full_forward(self):
        tokens = torch.tensor([[3, 4, 5, 6, 7]])
        with torch.no_grad():
            full_logits = self.model(tokens)
            recomputed = torch.stack(
                [self.model(tokens[:, :end])[:, -1] for end in range(1, 6)], dim=1
            )
        torch.testing.assert_close(full_logits, recomputed)

    def test_loss_backpropagates_and_optimizer_updates_weights(self):
        model = SpectralLM(self.config).train()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        tokens = torch.randint(1, self.config.vocab_size, (4, 12))
        before = model.token_embedding.weight.detach().clone()
        loss = model.loss(tokens)
        self.assertTrue(torch.isfinite(loss))
        optimizer.zero_grad()
        loss.backward()
        self.assertGreater(model.token_embedding.weight.grad.abs().sum().item(), 0.0)
        optimizer.step()
        self.assertFalse(torch.equal(before, model.token_embedding.weight))

    def test_loss_ignores_pairs_with_masked_source_or_target(self):
        compact = torch.tensor([[3, 4, 5, 6]])
        left_padded = torch.tensor([[0, 0, 3, 4, 5, 6]])
        left_mask = torch.tensor([[0, 0, 1, 1, 1, 1]])
        right_padded = torch.tensor([[3, 4, 5, 6, 0, 0]])
        right_mask = torch.tensor([[1, 1, 1, 1, 0, 0]])
        expected = self.model.loss(compact)
        torch.testing.assert_close(
            self.model.loss(left_padded, attention_mask=left_mask), expected
        )
        torch.testing.assert_close(
            self.model.loss(right_padded, attention_mask=right_mask), expected
        )

    def test_loss_rejects_mask_without_supervised_token_pair(self):
        with self.assertRaisesRegex(ValueError, "supervised next-token pair"):
            self.model.loss(
                torch.tensor([[0, 3, 0]]),
                attention_mask=torch.tensor([[0, 1, 0]]),
            )

    def test_checkpoint_round_trip_preserves_config_and_logits(self):
        tokens = torch.tensor([[3, 4, 5, 6]])
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "tiny.pt"
            self.model.save(checkpoint)
            loaded = SpectralLM.load(checkpoint)
            with torch.no_grad():
                expected = self.model(tokens)
                actual = loaded(tokens)
        self.assertEqual(loaded.config.to_dict(), self.config.to_dict())
        torch.testing.assert_close(actual, expected)

    def test_generate_recomputes_prefix_and_stops_at_eos(self):
        class ForcedEOS(SpectralLM):
            def forward(self, input_ids, attention_mask=None):
                logits = super().forward(input_ids, attention_mask)
                logits[:, -1, :] = -1e9
                logits[:, -1, 2] = 0.0
                return logits

        model = ForcedEOS(self.config).eval()
        generated = model.generate(torch.tensor([[3, 4]]), 5, eos_token_id=2)
        self.assertEqual(generated.tolist(), [[3, 4, 2]])

    def test_generate_uses_last_real_token_of_padded_prompt(self):
        plain = torch.tensor([[3, 4, 5]])
        padded = torch.tensor([[3, 4, 5, 0, 0]])
        mask = torch.tensor([[1, 1, 1, 0, 0]])
        plain_generated = self.model.generate(plain, 1, eos_token_id=None)
        padded_generated = self.model.generate(
            padded, 1, eos_token_id=None, attention_mask=mask
        )
        self.assertEqual(plain_generated[:, -1].item(), padded_generated[:, -1].item())

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is unavailable")
    def test_cpu_and_gpu_logits_are_numerically_consistent(self):
        tokens = torch.tensor([[3, 4, 5, 6, 7, 8]])
        cpu_model = self.model.cpu()
        gpu_model = SpectralLM(self.config).cuda().eval()
        gpu_model.load_state_dict(cpu_model.state_dict())
        with torch.no_grad():
            cpu_logits = cpu_model(tokens)
            gpu_logits = gpu_model(tokens.cuda()).cpu()
        torch.testing.assert_close(cpu_logits, gpu_logits, rtol=2e-4, atol=2e-4)

    def test_config_is_serializable_and_default_model_is_near_target_size(self):
        config = SpectralConfig.from_dict(SpectralConfig().to_dict())
        self.assertEqual(config, SpectralConfig())
        count = SpectralLM(config).num_parameters
        self.assertGreaterEqual(count, 13_000_000)
        self.assertLessEqual(count, 14_200_000)


class TestTokenizerAndHeads(unittest.TestCase):
    def test_sentencepiece_bpe_round_trip_and_reserved_tokens(self):
        texts = [
            "<ACTION> ADD input a input b <RESULT> 17 <HALT>",
            "<ACTION> VERIFY result <UNSOLVED>",
            "compute XOR of alpha and beta",
        ] * 8
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "math"
            tokenizer = SentencePieceTokenizer.train(texts, prefix, vocab_size=64)
            encoded = tokenizer.encode("compute XOR of alpha and beta")
            decoded = tokenizer.decode(encoded)
            saved = Path(directory) / "copy.model"
            tokenizer.save(saved)
            loaded = SentencePieceTokenizer.load(saved)
        self.assertEqual(decoded, "compute XOR of alpha and beta")
        self.assertEqual(loaded.decode(encoded), decoded)
        self.assertEqual(
            [tokenizer.piece_to_id(token) for token in RESERVED_TOKENS[:4]],
            [0, 1, 2, 3],
        )
        for token in RESERVED_TOKENS[4:]:
            self.assertNotEqual(tokenizer.piece_to_id(token), tokenizer.unk_id)

    def test_sentencepiece_training_appends_model_extension_to_dotted_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "math.v1"
            tokenizer = SentencePieceTokenizer.train(
                ["alpha beta gamma", "delta epsilon"] * 4,
                prefix,
                vocab_size=32,
            )
            expected_model = Path(f"{prefix}.model")
            self.assertEqual(tokenizer.model_file, expected_model)
            self.assertTrue(expected_model.is_file())

    def test_action_head_returns_action_and_pointer_logits(self):
        head = ActionHead(d_model=24, num_actions=11, num_pointer_slots=7)
        output = head(torch.zeros(2, 5, 24))
        self.assertEqual(output["action_logits"].shape, (2, 5, 11))
        self.assertEqual(output["pointer_logits"].shape, (2, 5, 7))


class TestComparableBaselines(unittest.TestCase):
    def test_transformer_and_gru_share_causal_forward_contract(self):
        config = SpectralConfig(
            vocab_size=64,
            d_model=24,
            n_layers=2,
            max_seq_len=16,
            ffn_hidden_dim=48,
            kernel_sizes=(3, 5, 9),
            dropout=0.0,
        )
        tokens = torch.tensor([[3, 4, 5, 6]])
        for model in (TransformerCausalLM(config, n_heads=4), GRUCausalLM(config)):
            logits = model(tokens)
            self.assertEqual(logits.shape, (1, 4, 64))
            self.assertTrue(torch.isfinite(model.loss(tokens)))
            generated = model.generate(tokens[:, :2], 2, eos_token_id=None)
            self.assertEqual(generated.shape, (1, 4))

    def test_baseline_generation_compacts_unequal_right_padded_prompts(self):
        config = SpectralConfig(
            vocab_size=64,
            d_model=24,
            n_layers=2,
            max_seq_len=16,
            ffn_hidden_dim=48,
            kernel_sizes=(3, 5, 9),
            dropout=0.0,
        )
        padded = torch.tensor([[3, 4, 5, 0, 0], [6, 7, 0, 0, 0]])
        mask = torch.tensor([[1, 1, 1, 0, 0], [1, 1, 0, 0, 0]])
        for model in (TransformerCausalLM(config, n_heads=4), GRUCausalLM(config)):
            model.eval()
            expected = pad_sequence(
                [
                    model.generate(padded[row, mask[row].bool()].unsqueeze(0), 2, None)
                    .squeeze(0)
                    for row in range(2)
                ],
                batch_first=True,
                padding_value=config.pad_token_id,
            )
            actual = model.generate(padded, 2, None, attention_mask=mask)
            torch.testing.assert_close(actual, expected)

    def test_baseline_generation_does_not_decode_past_per_row_eos(self):
        config = SpectralConfig(
            vocab_size=16,
            d_model=8,
            n_layers=1,
            max_seq_len=12,
            ffn_hidden_dim=16,
            kernel_sizes=(3,),
        )

        class ForcedEOSGRU(GRUCausalLM):
            def forward(self, input_ids, attention_mask=None):
                logits = torch.full(
                    (*input_ids.shape, self.config.vocab_size),
                    -1e9,
                    device=input_ids.device,
                )
                next_ids = torch.where(
                    input_ids[:, 0].eq(3),
                    torch.full_like(input_ids[:, 0], 2),
                    torch.full_like(input_ids[:, 0], 8),
                )
                logits[torch.arange(input_ids.shape[0]), -1, next_ids] = 0.0
                return logits

        model = ForcedEOSGRU(config).eval()
        padded = torch.tensor([[3, 4, 0], [6, 7, 9]])
        mask = torch.tensor([[1, 1, 0], [1, 1, 1]])
        generated = model.generate(padded, 3, eos_token_id=2, attention_mask=mask)
        self.assertEqual(generated[0].tolist(), [3, 4, 2, 0, 0, 0])
        self.assertEqual(generated[1].tolist(), [6, 7, 9, 8, 8, 8])

    def test_baseline_generation_keeps_finished_rows_at_eos(self):
        config = SpectralConfig(
            vocab_size=16,
            d_model=8,
            n_layers=1,
            max_seq_len=12,
            ffn_hidden_dim=16,
            kernel_sizes=(3,),
        )

        class ChangingAfterEOSGRU(GRUCausalLM):
            def forward(self, input_ids, attention_mask=None):
                logits = torch.full(
                    (*input_ids.shape, self.config.vocab_size),
                    -1e9,
                    device=input_ids.device,
                )
                first_row_next = torch.where(
                    input_ids[:, -1].eq(2),
                    torch.full_like(input_ids[:, 0], 9),
                    torch.full_like(input_ids[:, 0], 2),
                )
                next_ids = torch.where(
                    input_ids[:, 0].eq(3),
                    first_row_next,
                    torch.full_like(input_ids[:, 0], 8),
                )
                logits[torch.arange(input_ids.shape[0]), -1, next_ids] = 0.0
                return logits

        model = ChangingAfterEOSGRU(config).eval()
        generated = model.generate(
            torch.tensor([[3, 4, 5], [6, 7, 9]]),
            3,
            eos_token_id=2,
        )
        self.assertEqual(generated[0].tolist(), [3, 4, 5, 2, 2, 2])
        self.assertEqual(generated[1].tolist(), [6, 7, 9, 8, 8, 8])

    def test_baseline_losses_ignore_masked_source_target_pairs(self):
        config = SpectralConfig(
            vocab_size=64,
            d_model=24,
            n_layers=2,
            max_seq_len=16,
            ffn_hidden_dim=48,
            kernel_sizes=(3, 5, 9),
            dropout=0.0,
        )
        compact = torch.tensor([[3, 4, 5, 6]])
        left_padded = torch.tensor([[0, 0, 3, 4, 5, 6]])
        left_mask = torch.tensor([[0, 0, 1, 1, 1, 1]])
        right_padded = torch.tensor([[3, 4, 5, 6, 0, 0]])
        right_mask = torch.tensor([[1, 1, 1, 1, 0, 0]])
        for model in (TransformerCausalLM(config, n_heads=4), GRUCausalLM(config)):
            model.eval()
            expected = model.loss(compact)
            torch.testing.assert_close(
                model.loss(left_padded, attention_mask=left_mask), expected
            )
            torch.testing.assert_close(
                model.loss(right_padded, attention_mask=right_mask), expected
            )
            with self.assertRaisesRegex(ValueError, "supervised next-token pair"):
                model.loss(
                    torch.tensor([[0, 3, 0]]),
                    attention_mask=torch.tensor([[0, 1, 0]]),
                )


if __name__ == "__main__":
    unittest.main()
