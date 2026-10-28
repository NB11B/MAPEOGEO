"""SentencePiece BPE tokenizer with explicit MAPEOGEO control tokens."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

import sentencepiece as spm


RESERVED_TOKENS = (
    "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<ACTION>",
    "<HALT>", "<VERIFY>", "<UNSOLVED>", "<RESULT>", "<ERROR>",
)


def _model_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.suffix == ".model" else Path(f"{path}.model")


class SentencePieceTokenizer:
    def __init__(self, model_file: str | Path) -> None:
        self.model_file = Path(model_file)
        self.processor = spm.SentencePieceProcessor(model_file=str(self.model_file))

    @property
    def vocab_size(self) -> int:
        return self.processor.vocab_size()

    @property
    def unk_id(self) -> int:
        return self.processor.unk_id()

    @classmethod
    def train(cls, texts: Iterable[str], model_prefix: str | Path, vocab_size: int = 4096) -> "SentencePieceTokenizer":
        model_prefix = Path(model_prefix)
        model_prefix.parent.mkdir(parents=True, exist_ok=True)
        sentences = [text for text in texts if isinstance(text, str) and text.strip()]
        if not sentences:
            raise ValueError("texts must contain at least one non-empty string")
        spm.SentencePieceTrainer.train(
            sentence_iterator=iter(sentences), model_prefix=str(model_prefix),
            model_type="bpe", vocab_size=vocab_size, hard_vocab_limit=False,
            pad_id=0, unk_id=1, bos_id=2, eos_id=3,
            pad_piece=RESERVED_TOKENS[0], unk_piece=RESERVED_TOKENS[1],
            bos_piece=RESERVED_TOKENS[2], eos_piece=RESERVED_TOKENS[3],
            user_defined_symbols=list(RESERVED_TOKENS[4:]), character_coverage=1.0,
        )
        return cls(_model_path(model_prefix))

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        return list(self.processor.encode(text, out_type=int, add_bos=add_bos, add_eos=add_eos))

    def decode(self, ids: Iterable[int]) -> str:
        return self.processor.decode(list(ids))

    def piece_to_id(self, piece: str) -> int:
        return self.processor.piece_to_id(piece)

    def save(self, path: str | Path) -> Path:
        path = _model_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.model_file.resolve() != path.resolve():
            shutil.copy2(self.model_file, path)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "SentencePieceTokenizer":
        path = _model_path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        return cls(path)
