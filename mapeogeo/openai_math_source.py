"""Bounded, deterministic lexical source records; never proof verification.

Byte spans are half-open and point into the exact input bytes. Lean qualified
names describe the lexical namespace stack, not elaborated identities. A Lean
span ends at the next recognized source command (including nondeclarations),
and may contain intervening whitespace/comments. Header hashes stop before a
lexically visible top-level ``:=``, ``where`` or constructor ``|``. TeX spans
cover complete mathematical environments/display expressions when closed.

The API returns only identifiers, locators, hashes and machine diagnostics;
it does not return source/proof prose. Storage and time are bounded by a single
file and its extracted records, rather than by the repository size.
"""
from __future__ import annotations

from bisect import bisect_right
from hashlib import sha256
from pathlib import PurePosixPath
import re


_LEAN_KINDS = 'theorem lemma def abbrev instance structure inductive opaque class axiom example'.split()
# Deliberately recognize source commands, not arbitrary occurrences of keywords.
_LEAN_COMMAND = re.compile(
    rb'(?m)^[ \t]*(?:(?:private|protected|noncomputable|unsafe|partial|nonrec|public|local|scoped)[ \t]+'
    rb'|@\[[^\]\n]*\][ \t]*)*'
    rb'(?P<kind>theorem|lemma|def|abbrev|instance|structure|inductive|opaque|class|axiom|example|'
    rb'namespace|section|end|import|open|export|variable|variables|universe|universes|'
    rb'set_option|attribute|initialize|builtin_initialize|syntax|macro_rules|macro|'
    rb'elab_rules|elab|notation|infixl|infixr|infix|prefix|postfix|local|scoped|'
    rb"mutual|include|omit|prelude)(?![A-Za-z0-9_'\x80-\xff])|(?m:^[ \t]*#[A-Za-z_]+)"
)
_IDENT = re.compile(rb'(?:\xc2\xab[^\n]*?\xc2\xbb|[^\s():={}\[\],;|]+)')
_LEAN_SPECIAL = re.compile(rb'/\-|--|(?<![A-Za-z0-9_])r#+"|"|\x27|\xc2\xab')
_COMMENT_MARKERS = re.compile(rb'/\-|-\/')
_STRING_MARKERS = re.compile(rb'["\\]')
_CHAR_LITERAL = re.compile(rb"'(?:\\(?:u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)|[\x00-\x7f]|[\xc2-\xdf][\x80-\xbf]|[\xe0-\xef][\x80-\xbf]{2}|[\xf0-\xf4][\x80-\xbf]{3})'")
_WHITESPACE = re.compile(rb'\s*')
_INSTANCE_PRIORITY = re.compile(rb'\(\s*priority\s*:=\s*[^)]+\)\s*')
_HEADER_TOKEN = re.compile(rb"\xc2\xab[^\n]*?\xc2\xbb|:=|(?<![A-Za-z0-9_'\x80-\xff])where(?![A-Za-z0-9_'\x80-\xff])|[()\[\]{}|]")
_TEX_SPECIAL = re.compile(rb'%|\\begin\{(?P<opaque>verbatim\*?|Verbatim|lstlisting|minted|comment)\}'
                          rb'|\\verb\*?(?P<delimiter>[^\sA-Za-z])')
_TEX_NEW = re.compile(rb'\\newtheorem\*?\s*\{([^{}]+)\}')
_TEX_EVENTS = re.compile(
    rb'\\(?P<envcmd>begin|end)\s*\{(?P<env>[^{}]+)\}'
    rb'|\\(?P<refcmd>input|include|includeonly|subfile|bibliography|addbibresource|label|'
    rb'ref|eqref|pageref|autoref|cref|Cref|vref|cite[a-zA-Z]*|nocite)\*?'
    rb'(?:\s*\[[^\]\n]*\])*\s*\{(?P<target>[^{}]+)\}'
    rb'|\\input[ \t]+(?P<bareinput>[^\s{}%]+)'
    rb'|(?P<display>\\\[|\\\]|\$\$)'
)
_TEX_MATH = set('theorem thm lemma lem corollary cor proposition prop definition defn def remark rem '
                'example ex exercise problem conjecture conj claim fact assumption axiom proposition '
                'proof solution equation equation* align align* aligned gather gather* multline '
                'multline* eqnarray eqnarray* displaymath math'.split())
_BINARY_SUFFIXES = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.zip', '.gz',
                    '.tar', '.xz', '.bz2', '.olean', '.ilean', '.o', '.so', '.a', '.bin',
                    '.ttf', '.woff', '.woff2', '.mp4', '.sqlite'}
_MD_LINK = re.compile(rb'\[[^\]\n]*\]\(\s*(?:<(?P<angle>[^>\n]+)>|(?P<plain>[^\s)]+))(?:\s+[^)\n]*)?\)')


def _blank(mask: bytearray, start: int, end: int) -> None:
    """Mask syntax while keeping original byte/newline positions."""
    mask[start:end] = re.sub(rb'[^\r\n]', b' ', mask[start:end])


def _mask_lean(data: bytes, diagnostics: list) -> bytes:
    mask = bytearray(data)
    pos = 0
    while match := _LEAN_SPECIAL.search(data, pos):
        start = match.start()
        token = match.group()
        if token == b'--':
            end = data.find(b'\n', start)
            end = len(data) if end < 0 else end
        elif token == b'/-':
            depth, end = 1, match.end()
            while depth and (marker := _COMMENT_MARKERS.search(data, end)):
                depth += 1 if marker.group() == b'/-' else -1
                end = marker.end()
            if depth:
                end = len(data)
                diagnostics.append({'code': 'unterminated_block_comment', 'start_byte': start})
        elif token.startswith(b'r'):
            closing_marker = b'"' + token[1:-1]
            closing = data.find(closing_marker, match.end())
            if closing < 0:
                end = len(data)
                diagnostics.append({'code': 'unterminated_string', 'start_byte': start})
            else:
                end = closing + len(closing_marker)
        elif token == b'"':
            end = start + 1
            closed = False
            while end < len(data):
                marker = _STRING_MARKERS.search(data, end)
                if marker is None:
                    end = len(data)
                    break
                end = marker.end()
                if data[end - 1] == 34:
                    closed = True
                    break
                end = min(end + 1, len(data))
            if not closed:
                diagnostics.append({'code': 'unterminated_string', 'start_byte': start})
        elif token == b'\xc2\xab':
            closing = data.find(b'\xc2\xbb', match.end())
            pos = len(data) if closing < 0 else closing + 2
            continue
        else:
            # A prime in a Lean identifier is not a character literal. Recognize
            # a single Unicode scalar or backslash escape followed by a quote.
            previous = data[start - 1] if start else 32
            if previous >= 128 or chr(previous).isalnum() or previous in (95, 39):
                pos = match.end()
                continue
            char = _CHAR_LITERAL.match(data, start)
            if char is None:
                pos = match.end()
                continue
            end = char.end()
        _blank(mask, start, end)
        pos = end
    return bytes(mask)


def _line_starts(data: bytes) -> list[int]:
    return [0] + [m.end() for m in re.finditer(b'\n', data)]


def _record(data: bytes, lines: list[int], kind: str, name: str,
            start: int, end: int, header_end: int, qualified_name: str | None = None) -> dict:
    record = {'kind': kind, 'name': name, 'start_byte': start, 'end_byte': end,
              'start_line': bisect_right(lines, start), 'end_line': bisect_right(lines, end - 1),
              'span_sha256': sha256(memoryview(data)[start:end]).hexdigest(),
              'header_sha256': sha256(memoryview(data)[start:header_end]).hexdigest()}
    if qualified_name is not None:
        record['qualified_name'] = qualified_name
    return record


def _header_end(mask: bytes, start: int, end: int) -> int:
    depth = 0
    for token in _HEADER_TOKEN.finditer(mask, start, end):
        text = token.group()
        if text.startswith(b'\xc2\xab'):
            continue
        if text in (b'(', b'[', b'{'):
            depth += 1
        elif text in (b')', b']', b'}'):
            depth = max(0, depth - 1)
        elif depth == 0:
            return token.start()
    return end


def _scan_lean(data: bytes, lines: list[int], diagnostics: list) -> tuple[list, list]:
    mask = _mask_lean(data, diagnostics)
    records, references = [], []
    scopes = []  # Sections are scope delimiters but never name prefixes.
    pending = None
    for command in _LEAN_COMMAND.finditer(mask):
        kind_b = command.group('kind')
        start = command.start('kind') if kind_b is not None else command.start()
        if pending is not None:
            kind, name, old_start, qualified = pending
            records.append(_record(data, lines, kind, name, old_start, start,
                                   _header_end(mask, old_start, start), qualified))
            pending = None
        if kind_b is None:
            continue
        kind = kind_b.decode('ascii')
        pos = command.end()
        line_end = mask.find(b'\n', pos)
        line_end = len(mask) if line_end < 0 else line_end
        name_start = _WHITESPACE.match(mask, pos, len(mask) if kind in _LEAN_KINDS else line_end).end()
        if kind == 'instance' and (priority := _INSTANCE_PRIORITY.match(mask, name_start)):
            name_start = priority.end()
        name_match = _IDENT.match(mask, name_start)
        name = name_match.group().decode('utf-8') if name_match else None
        if kind == 'namespace':
            if name:
                scopes.append(('namespace', name))
            else:
                diagnostics.append({'code': 'missing_namespace_name', 'start_byte': start})
        elif kind == 'section':
            scopes.append(('section', name))
        elif kind == 'mutual':
            scopes.append(('mutual', None))
        elif kind == 'end':
            if name:
                closing = next((i for i in range(len(scopes) - 1, -1, -1) if scopes[i][1] == name), None)
                if closing is None:
                    diagnostics.append({'code': 'unmatched_named_end', 'start_byte': start})
                else:
                    del scopes[closing:]
            elif scopes:
                scopes.pop()
            else:
                diagnostics.append({'code': 'unmatched_end', 'start_byte': start})
        elif kind == 'import':
            for target in _IDENT.finditer(mask, pos, line_end):
                references.append({'kind': 'lean_import', 'target': target.group().decode('utf-8'),
                                   'start_line': bisect_right(lines, start)})
        elif kind in _LEAN_KINDS:
            if kind == 'example' or (kind == 'instance' and name is None):
                name = f'__anonymous_{kind}_{start}'
            if not name:
                diagnostics.append({'code': 'missing_declaration_name', 'start_byte': start})
                continue
            prefix = '.'.join(s[1] for s in scopes if s[0] == 'namespace')
            qualified = name.removeprefix('_root_.') if name.startswith('_root_.') else '.'.join(filter(None, (prefix, name)))
            pending = (kind, name, start, qualified)
    if pending is not None:
        kind, name, start, qualified = pending
        records.append(_record(data, lines, kind, name, start, len(data),
                               _header_end(mask, start, len(data)), qualified))
    # File-wide sections need no explicit EOF delimiter. Unclosed namespaces or
    # mutual blocks remain explicit lexical deficits.
    unclosed = sum(s[0] != 'section' for s in scopes)
    if unclosed:
        diagnostics.append({'code': 'unclosed_scope', 'count': unclosed})
    return records, references


def _mask_tex(data: bytes, diagnostics: list) -> bytes:
    mask = bytearray(data)
    pos = 0
    # Process comments and verbatim syntax in source order. Neither may expose
    # apparent commands inside the other. Each opaque block is traversed once.
    while special := _TEX_SPECIAL.search(data, pos):
        start = special.start()
        preceding = start - 1
        while preceding >= 0 and data[preceding] == 92:
            preceding -= 1
        if (start - preceding - 1) % 2:
            pos = special.end()
            continue
        if special.group('opaque'):
            ending = b'\\end{' + special.group('opaque') + b'}'
            closing = data.find(ending, special.end())
            end = len(data) if closing < 0 else closing + len(ending)
            if closing < 0:
                diagnostics.append({'code': 'unterminated_verbatim', 'start_byte': start})
        elif special.group('delimiter'):
            newline = data.find(b'\n', special.end())
            limit = len(data) if newline < 0 else newline
            closing = data.find(special.group('delimiter'), special.end(), limit)
            end = limit if closing < 0 else closing + 1
            if closing < 0:
                diagnostics.append({'code': 'unterminated_verbatim', 'start_byte': start})
        else:
            end = data.find(b'\n', start)
            end = len(data) if end < 0 else end
        _blank(mask, start, end)
        pos = end
    return bytes(mask)


def _scan_tex(data: bytes, lines: list[int], diagnostics: list) -> tuple[list, list]:
    mask = _mask_tex(data, diagnostics)
    environments = _TEX_MATH | {m.group(1).decode('utf-8') for m in _TEX_NEW.finditer(mask)}
    records, references, stack = [], [], []
    # Placeholders preserve source ordering without sorting nested records.
    def begin(kind: str, start: int, header_end: int, env: str):
        slot = len(records) if kind else None
        if slot is not None:
            records.append(None)
        stack.append({'env': env, 'kind': kind, 'start': start, 'header_end': header_end,
                      'slot': slot, 'name': None})

    def finish(item, end):
        if item['slot'] is not None:
            name = item['name'] or f"__{item['kind']}_{item['start']}"
            records[item['slot']] = _record(data, lines, item['kind'], name, item['start'], end, item['header_end'])

    for event in _TEX_EVENTS.finditer(mask):
        # A doubled slash is a linebreak, not a command escape.
        preceding = event.start() - 1
        while preceding >= 0 and mask[preceding] == 92:
            preceding -= 1
        if (event.start() - preceding - 1) % 2:
            continue
        if event.group('envcmd'):
            env = event.group('env').decode('utf-8').strip()
            if event.group('envcmd') == b'begin':
                kind = env if env in environments or env.removesuffix('*') in environments else ''
                begin(kind, event.start(), event.end(), env)
            elif stack and stack[-1]['env'] == env:
                finish(stack.pop(), event.end())
            else:
                diagnostics.append({'code': 'unmatched_environment_end', 'start_byte': event.start()})
        elif event.group('display'):
            token = event.group('display')
            if token == b'\\[' or (token == b'$$' and (not stack or stack[-1]['env'] != '$$')):
                begin('display_math', event.start(), event.end(), '\\[' if token == b'\\[' else '$$')
            elif stack and stack[-1]['env'] == ('\\[' if token == b'\\]' else '$$'):
                finish(stack.pop(), event.end())
            else:
                diagnostics.append({'code': 'unmatched_display_end', 'start_byte': event.start()})
        else:
            command = event.group('refcmd').decode('ascii') if event.group('refcmd') else 'input'
            raw = event.group('target') or event.group('bareinput')
            if command.startswith('cite') or command == 'nocite':
                kind = 'tex_citation'
            elif command in {'ref', 'eqref', 'pageref', 'autoref', 'cref', 'Cref', 'vref'}:
                kind = 'tex_reference'
            else:
                kind = f'tex_{command}'
            owner = next((s for s in reversed(stack) if s['slot'] is not None), None)
            for value in raw.decode('utf-8').split(','):
                target = value.strip()
                if not target:
                    continue
                reference = {'kind': kind, 'target': target, 'start_line': bisect_right(lines, event.start())}
                if owner is not None:
                    reference['record_start_byte'] = owner['start']
                    if command == 'label' and owner['name'] is None:
                        owner['name'] = target
                references.append(reference)
    for item in stack:
        finish(item, len(data))
        diagnostics.append({'code': 'unclosed_environment', 'start_byte': item['start']})
    return records, references


def scan_source(path: str, data: bytes) -> dict:
    """Extract lexical candidates and explicit references from one exact resource.

    Unknown formats are explicitly metadata-only. Invalid UTF-8 in a supported
    text format yields no records and a decode_error disposition. The caller
    binds file context, source revision and hashes; this function reads no files.
    """
    result = {'records': [], 'references': [], 'disposition': 'metadata_only', 'diagnostics': []}
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in _BINARY_SUFFIXES or b'\0' in data:
        result['disposition'] = 'binary_metadata_only'
        if suffix in {'.lean', '.tex', '.md', '.markdown'}:
            result['diagnostics'].append({'code': 'binary_content_in_text_source'})
        return result
    if suffix not in {'.lean', '.tex', '.md', '.markdown'}:
        result['diagnostics'].append({'code': 'unsupported_format'})
        return result
    try:
        data.decode('utf-8')
    except UnicodeDecodeError as error:
        result['disposition'] = 'decode_error'
        result['diagnostics'].append({'code': 'invalid_utf8', 'start_byte': error.start, 'end_byte': error.end})
        return result
    lines = _line_starts(data)
    if suffix == '.lean':
        result['records'], result['references'] = _scan_lean(data, lines, result['diagnostics'])
        result['disposition'] = 'lean_lexically_scanned'
    elif suffix == '.tex':
        result['records'], result['references'] = _scan_tex(data, lines, result['diagnostics'])
        result['disposition'] = 'tex_lexically_scanned'
    else:
        result['references'] = [{'kind': 'markdown_link', 'target': (m.group('angle') or m.group('plain')).decode('utf-8'),
                                 'start_line': bisect_right(lines, m.start())} for m in _MD_LINK.finditer(data)]
        result['disposition'] = 'markdown_lexically_scanned'
    return result
