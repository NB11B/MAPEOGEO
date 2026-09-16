#!/usr/bin/env python3
"""Deterministic zero-prose source parsers for MAPEOGEO v0.21.

Only explicit theorem-like structures are admitted.  The returned objects retain
statement hashes and locators, never source statement/proof text.
"""

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PARSER_VERSION = "v0.21.1"
FORBIDDEN_PERSISTED_KEYS = {
    "statement_text",
    "proof_text",
    "source_prose",
    "page_image",
    "statement",
    "body",
}

_PRETEXT_TYPES = {
    "definition": "DEFINITION",
    "theorem": "THEOREM",
    "proposition": "PROPOSITION",
    "lemma": "LEMMA",
    "corollary": "COROLLARY",
    "axiom": "AXIOM",
}

_LATEX_TYPES = {
    "definition": "DEFINITION",
    "defn": "DEFINITION",
    "theorem": "THEOREM",
    "thm": "THEOREM",
    "proposition": "PROPOSITION",
    "prop": "PROPOSITION",
    "lemma": "LEMMA",
    "lem": "LEMMA",
    "corollary": "COROLLARY",
    "cor": "COROLLARY",
    "axiom": "AXIOM",
}

_XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
_ENV_TOKEN_RE = re.compile(r"\\(begin|end)\{([A-Za-z]+\*?)\}")


@dataclass(frozen=True)
class ExtractedDeclaration:
    node_id: str
    source_id: str
    repository: str
    revision: str
    structured_id: str
    decl_type: str
    source_path: str
    line_start: int
    line_end: int
    statement_sha256: str
    char_count: int
    extraction_method: str
    parser_version: str = PARSER_VERSION
    node_type: str = "SOURCE_DECLARATION"
    canonical_status: str = "UNRESOLVED"
    formal_status: str = "UNFORMALIZED"
    executable_status: str = "UNTESTED"

    def to_metadata(self) -> dict:
        row = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "source_id": self.source_id,
            "repository": self.repository,
            "revision": self.revision,
            "structured_id": self.structured_id,
            "decl_type": self.decl_type,
            "source_path": self.source_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "statement_sha256": self.statement_sha256,
            "char_count": self.char_count,
            "extraction_method": self.extraction_method,
            "parser_version": self.parser_version,
            "canonical_status": self.canonical_status,
            "formal_status": self.formal_status,
            "executable_status": self.executable_status,
        }
        if FORBIDDEN_PERSISTED_KEYS.intersection(row):
            raise AssertionError("forbidden source prose key reached persisted metadata")
        return row


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _matches_any(relative: Path, patterns: Iterable[str]) -> bool:
    posix = Path(relative.as_posix())
    return any(posix.match(pattern) for pattern in patterns)


def _source_files(root: Path, spec, suffixes: set[str]) -> list[Path]:
    selected: dict[str, Path] = {}
    for pattern in spec.include_globs:
        for path in root.glob(pattern):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            relative = path.relative_to(root)
            if _matches_any(relative, spec.exclude_globs):
                continue
            selected[relative.as_posix()] = path
    return [selected[key] for key in sorted(selected)]


def _node_id(spec, source_path: str, structured_id: str, decl_type: str) -> str:
    identity = f"{spec.source_id}\0{spec.repository}\0{spec.revision}\0{source_path}\0{structured_id}\0{decl_type}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    return f"srcdecl:v0_21:{spec.source_id.lower()}:{digest}"


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _xml_statement_text(statement: ET.Element) -> str:
    # PreTeXt whitespace is presentation formatting, so canonicalize runs of
    # whitespace while preserving all non-whitespace source characters.
    return " ".join("".join(statement.itertext()).split())


def _pretext_line(raw: str, structured_id: str, fallback_tag: str, ordinal: int) -> int:
    for needle in (f'xml:id="{structured_id}"', f"xml:id='{structured_id}'"):
        offset = raw.find(needle)
        if offset >= 0:
            return _line_for_offset(raw, offset)
    # A missing xml:id is allowed, but the line locator is still bound to the
    # ordinal occurrence of the explicit structured element.
    pattern = re.compile(rf"<{re.escape(fallback_tag)}(?:\s|>)")
    matches = list(pattern.finditer(raw))
    if 1 <= ordinal <= len(matches):
        return _line_for_offset(raw, matches[ordinal - 1].start())
    return 1


def extract_pretext_declarations(root: Path, spec) -> list[ExtractedDeclaration]:
    declarations: list[ExtractedDeclaration] = []
    per_path_type: dict[tuple[str, str], int] = {}
    for path in _source_files(root, spec, {".ptx", ".xml"}):
        relative = path.relative_to(root).as_posix()
        raw = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        try:
            tree = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ValueError(f"malformed PreTeXt/XML source {relative}: {exc}") from exc

        for element in tree.iter():
            local = _local_name(element.tag)
            if local not in _PRETEXT_TYPES:
                continue
            statement = next((child for child in list(element) if _local_name(child.tag) == "statement"), None)
            if statement is None:
                continue
            statement_text = _xml_statement_text(statement)
            if not statement_text:
                continue
            key = (relative, local)
            per_path_type[key] = per_path_type.get(key, 0) + 1
            ordinal = per_path_type[key]
            structured_id = element.attrib.get(_XML_ID) or element.attrib.get("xml:id")
            if not structured_id:
                structured_id = f"{relative}#{local}-{ordinal}"
            serialized = ET.tostring(element, encoding="unicode")
            line_start = _pretext_line(raw, structured_id, local, ordinal)
            line_end = line_start + serialized.count("\n")
            digest = hashlib.sha256(statement_text.encode("utf-8")).hexdigest()
            decl_type = _PRETEXT_TYPES[local]
            declarations.append(
                ExtractedDeclaration(
                    node_id=_node_id(spec, relative, structured_id, decl_type),
                    source_id=spec.source_id,
                    repository=spec.repository,
                    revision=spec.revision,
                    structured_id=structured_id,
                    decl_type=decl_type,
                    source_path=relative,
                    line_start=line_start,
                    line_end=max(line_start, line_end),
                    statement_sha256=digest,
                    char_count=len(statement_text),
                    extraction_method="pretext-structured-statement",
                )
            )
    return sorted(declarations, key=lambda d: (d.source_path, d.line_start, d.structured_id))


def _mask_latex_comments(text: str) -> str:
    chars = list(text)
    i = 0
    while i < len(chars):
        if chars[i] == "%":
            backslashes = 0
            j = i - 1
            while j >= 0 and chars[j] == "\\":
                backslashes += 1
                j -= 1
            if backslashes % 2 == 0:
                while i < len(chars) and chars[i] != "\n":
                    chars[i] = " "
                    i += 1
                continue
        i += 1
    return "".join(chars)


def _latex_base_env(env: str) -> str:
    return env[:-1] if env.endswith("*") else env


def extract_latex_declarations(root: Path, spec) -> list[ExtractedDeclaration]:
    declarations: list[ExtractedDeclaration] = []
    for path in _source_files(root, spec, {".tex"}):
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        masked = _mask_latex_comments(raw)
        stack: list[tuple[str, re.Match[str], int]] = []
        ordinal_by_type: dict[str, int] = {}

        for token in _ENV_TOKEN_RE.finditer(masked):
            action, env = token.group(1), token.group(2)
            base_env = _latex_base_env(env)
            if base_env not in _LATEX_TYPES:
                continue
            if action == "begin":
                stack.append((env, token, len(declarations)))
                continue

            if not stack or stack[-1][0] != env:
                raise ValueError(f"unbalanced theorem-like environment in {relative}: unexpected end of {env}")
            open_env, begin_token, _ = stack.pop()
            body = raw[begin_token.end() : token.start()]
            if body.startswith("\n"):
                body = body[1:]
            decl_type = _LATEX_TYPES[_latex_base_env(open_env)]
            ordinal_by_type[decl_type] = ordinal_by_type.get(decl_type, 0) + 1
            label = _LABEL_RE.search(_mask_latex_comments(body))
            structured_id = label.group(1).strip() if label else f"{relative}#{decl_type.lower()}-{ordinal_by_type[decl_type]}"
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            line_start = _line_for_offset(raw, begin_token.start())
            line_end = _line_for_offset(raw, token.end())
            declarations.append(
                ExtractedDeclaration(
                    node_id=_node_id(spec, relative, structured_id, decl_type),
                    source_id=spec.source_id,
                    repository=spec.repository,
                    revision=spec.revision,
                    structured_id=structured_id,
                    decl_type=decl_type,
                    source_path=relative,
                    line_start=line_start,
                    line_end=line_end,
                    statement_sha256=digest,
                    char_count=len(body),
                    extraction_method="latex-theorem-environment",
                )
            )

        if stack:
            env, _, _ = stack[-1]
            raise ValueError(f"unbalanced theorem-like environment in {relative}: missing end of {env}")

    return sorted(declarations, key=lambda d: (d.source_path, d.line_start, d.structured_id))
