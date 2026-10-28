"""Fail-closed Lean verifier for a deliberately narrow closed-Nat theorem family."""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
import tempfile
from pathlib import Path


_TOKEN = re.compile(r"\s*(<=|>=|[0-9]+|[()+*\-=<>])")
_PROOFS = {"by rfl", "by decide"}


class _ClosedNatParser:
    def __init__(self, source: str):
        self.tokens: list[str] = []
        position = 0
        while position < len(source):
            match = _TOKEN.match(source, position)
            if match is None:
                raise ValueError("proposition is outside the closed Nat expression subset")
            self.tokens.append(match.group(1))
            position = match.end()
        self.index = 0

    def _take(self, value: str | None = None) -> str:
        if self.index >= len(self.tokens):
            raise ValueError("unexpected end of proposition")
        token = self.tokens[self.index]
        if value is not None and token != value:
            raise ValueError(f"expected {value}")
        self.index += 1
        return token

    def _atom(self) -> None:
        if self.index < len(self.tokens) and self.tokens[self.index].isdigit():
            self._take()
        elif self.index < len(self.tokens) and self.tokens[self.index] == "(":
            self._take("(")
            self._expression()
            self._take(")")
        else:
            raise ValueError("expected a numeral or parenthesized Nat expression")

    def _term(self) -> None:
        self._atom()
        while self.index < len(self.tokens) and self.tokens[self.index] == "*":
            self._take("*")
            self._atom()

    def _expression(self) -> None:
        self._term()
        while self.index < len(self.tokens) and self.tokens[self.index] in {"+", "-"}:
            self._take()
            self._term()

    def parse_proposition(self) -> None:
        self._expression()
        if self.index >= len(self.tokens) or self.tokens[self.index] not in {"=", "<", "<=", ">", ">="}:
            raise ValueError("closed Nat proposition requires one comparison")
        self._take()
        self._expression()
        if self.index != len(self.tokens):
            raise ValueError("unexpected token after closed Nat proposition")


class LeanAdapter:
    """Check a closed Nat theorem using fixed source and process arguments."""

    def __init__(self, lean_executable: str | Path = "lean"):
        self._executable = str(lean_executable)
        try:
            version = subprocess.run(
                [self._executable, "--version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OSError(f"Lean executable unavailable: {self._executable}") from exc
        self._version = version.stdout.strip()

    @staticmethod
    def _invalid(message: str) -> dict[str, object]:
        return {
            "status": "INVALID_INPUT",
            "evidence": {"kernel_checked": False, "axioms": None, "error": message},
        }

    def verify(self, proposition: str, proof: str, timeout_seconds: float = 10) -> dict[str, object]:
        if not isinstance(proposition, str) or not isinstance(proof, str):
            return self._invalid("proposition and proof must be strings")
        try:
            timeout = float(timeout_seconds)
        except (TypeError, ValueError):
            return self._invalid("timeout_seconds must be a finite positive number")
        if not math.isfinite(timeout) or timeout <= 0:
            return self._invalid("timeout_seconds must be a finite positive number")
        if proof not in _PROOFS:
            return self._invalid("proof is not in the approved proof family")
        if not proposition or proposition != proposition.strip() or "\n" in proposition or "\r" in proposition:
            return self._invalid("proposition must be one trimmed source line")
        try:
            _ClosedNatParser(proposition).parse_proposition()
        except ValueError as exc:
            return self._invalid(str(exc))

        source = (
            f"theorem mapeogeo_checked : ({proposition}) := {proof}\n"
            "#print axioms mapeogeo_checked\n"
        )
        source_digest = hashlib.sha256(source.encode()).hexdigest()
        path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".lean", encoding="utf-8", newline="\n", delete=False
            ) as handle:
                handle.write(source)
                path = Path(handle.name)
            try:
                completed = subprocess.run(
                    [self._executable, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False,
                )
            except subprocess.TimeoutExpired:
                return {
                    "status": "TIMEOUT",
                    "evidence": {
                        "kernel_checked": False,
                        "axioms": None,
                        "lean_version": self._version,
                        "theorem": "mapeogeo_checked",
                        "source_sha256": source_digest,
                        "timeout_seconds": timeout,
                    },
                }
            combined = completed.stdout + completed.stderr
            axiom_free = any(
                marker in combined
                for marker in (
                    "'mapeogeo_checked' does not depend on any axioms",
                    "mapeogeo_checked depends on axioms: []",
                )
            )
            if completed.returncode == 0 and axiom_free:
                return {
                    "status": "VERIFIED",
                    "evidence": {
                        "kernel_checked": True,
                        "axioms": [],
                        "lean_version": self._version,
                        "theorem": "mapeogeo_checked",
                        "source_sha256": source_digest,
                        "proof_family": proof.removeprefix("by "),
                    },
                }
            return {
                "status": "UNSOLVED",
                "evidence": {
                    "kernel_checked": False,
                    "negation_checked": False,
                    "axioms": None,
                    "lean_version": self._version,
                    "theorem": "mapeogeo_checked",
                    "source_sha256": source_digest,
                    "returncode": completed.returncode,
                    "diagnostic": combined[-4000:],
                },
            }
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
