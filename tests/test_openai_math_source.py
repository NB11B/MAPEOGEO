"""Lexical source extraction contracts, never mathematical validity tests."""
import hashlib

from mapeogeo.openai_math_source import scan_source


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_spans(data, records):
    for record in records:
        start, end = record['start_byte'], record['end_byte']
        assert 0 <= start < end <= len(data)
        assert record['span_sha256'] == digest(data[start:end])
        assert record['start_line'] == data[:start].count(b'\n') + 1
        assert record['end_line'] == data[:end - 1].count(b'\n') + 1
        assert set(record) <= {'kind', 'name', 'qualified_name', 'start_byte',
                               'end_byte', 'start_line', 'end_line',
                               'span_sha256', 'header_sha256'}


def test_lean_masks_nested_comments_and_escaped_strings():
    data = b'''/- theorem fake : True := by trivial\n /- def nested := 1 -/ -/\n-- lemma fake2 : True := by trivial\ndef message := "hello \\\"\ntheorem hidden : True := by trivial"\ntheorem real : True := by trivial\n'''
    result = scan_source('Example.lean', data)
    assert [(r['kind'], r['name']) for r in result['records']] == [('def', 'message'), ('theorem', 'real')]
    assert result['disposition'] == 'lean_lexically_scanned'
    check_spans(data, result['records'])


def test_lean_unicode_offsets_lexical_namespaces_and_header_hash():
    data = 'namespace α\nsection Inner\n@[simp] theorem β (x : Nat) : x = x := by rfl\nend Inner\nend α\ndef z := 2\n'.encode()
    result = scan_source('unicode.lean', data)
    first, second = result['records']
    start = data.index('theorem β'.encode())
    header_end = data.index(b':=')
    assert first['start_byte'] == start
    assert first['qualified_name'] == 'α.β'
    assert second['qualified_name'] == 'z'
    assert first['header_sha256'] == digest(data[start:header_end])
    assert data[first['end_byte']:].startswith(b'end Inner')
    check_spans(data, result['records'])


def test_lean_recognizes_kinds_anonymous_and_quoted_identifiers():
    data = '''private lemma «with space» : True := by trivial
abbrev short := Nat
instance named : Inhabited Nat := ⟨0⟩
instance : Inhabited Bool := ⟨false⟩
structure Box where
  x : Nat
inductive Color where
  | red
opaque secret : Nat
class C where
  p : Prop
axiom agreed : True
example : True := by trivial
'''.encode()
    records = scan_source('kinds.lean', data)['records']
    assert [r['kind'] for r in records] == ['lemma', 'abbrev', 'instance', 'instance', 'structure', 'inductive', 'opaque', 'class', 'axiom', 'example']
    assert records[0]['name'] == '«with space»'
    assert records[3]['name'].startswith('__anonymous_instance_')
    assert records[-1]['name'].startswith('__anonymous_example_')
    check_spans(data, records)


def test_lean_imports_and_command_boundaries():
    data = b'import Mathlib.Algebra.Basic Mathlib.Data.Nat\nnamespace X\ndef a := 1\nopen Nat\ndef b := 2\nend X\n'
    result = scan_source('imports.lean', data)
    assert [(r['kind'], r['target']) for r in result['references']] == [('lean_import', 'Mathlib.Algebra.Basic'), ('lean_import', 'Mathlib.Data.Nat')]
    assert data[result['records'][0]['end_byte']:].startswith(b'open Nat')


def test_lean_local_body_keywords_do_not_become_declarations():
    data = b'def a := by\n  let theorem := 1\n  exact theorem\ndef b := 2\n'
    assert [r['name'] for r in scan_source('local.lean', data)['records']] == ['a', 'b']


def test_lean_unterminated_comment_is_explicit():
    result = scan_source('bad.lean', b'def good := 1\n/- unfinished theorem fake : True')
    assert [r['name'] for r in result['records']] == ['good']
    assert any(d['code'] == 'unterminated_block_comment' for d in result['diagnostics'])


def test_tex_aliases_nested_proofs_labels_and_explicit_references():
    data = br'''\newtheorem{claim}[theorem]{Claim}
% \begin{theorem} false \end{theorem}
\input{sections/intro}
\include{body}
\begin{claim}\label{cl:first} Statement.
\begin{proof} See \ref{other} and \cite[p. 3]{smith,jones}.\end{proof}
\end{claim}
'''
    result = scan_source('paper.tex', data)
    assert [r['kind'] for r in result['records']] == ['claim', 'proof']
    assert result['records'][0]['name'] == 'cl:first'
    assert result['disposition'] == 'tex_lexically_scanned'
    assert {(r['kind'], r['target']) for r in result['references']} == {('tex_input', 'sections/intro'), ('tex_include', 'body'), ('tex_label', 'cl:first'), ('tex_reference', 'other'), ('tex_citation', 'smith'), ('tex_citation', 'jones')}
    label = next(r for r in result['references'] if r['kind'] == 'tex_label')
    assert label['record_start_byte'] == result['records'][0]['start_byte']
    check_spans(data, result['records'])


def test_tex_equations_escaped_percent_and_verbatim_are_lexical():
    data = br'''\begin{verbatim}
\begin{theorem} fake \end{theorem}
\end{verbatim}
\begin{equation}x = 10\%\label{eq:x}\end{equation}
\[y=2\]
$$z=3$$
'''
    result = scan_source('math.tex', data)
    assert [r['kind'] for r in result['records']] == ['equation', 'display_math', 'display_math']
    assert result['records'][0]['name'] == 'eq:x'
    check_spans(data, result['records'])


def test_tex_unclosed_environment_is_explicit():
    result = scan_source('bad.tex', br'\begin{theorem}unfinished')
    assert len(result['records']) == 1
    assert any(d['code'] == 'unclosed_environment' for d in result['diagnostics'])


def test_markdown_links_and_other_resource_dispositions():
    result = scan_source('README.md', b'[paper](papers/a.pdf)\n[code](https://example.test/code)\n')
    assert result['records'] == []
    assert [r['target'] for r in result['references']] == ['papers/a.pdf', 'https://example.test/code']
    assert result['disposition'] == 'markdown_lexically_scanned'
    assert scan_source('settings.yaml', b'x: y\n')['disposition'] == 'metadata_only'
    assert scan_source('paper.pdf', b'%PDF\x00\xff')['disposition'] == 'binary_metadata_only'


def test_undecodable_lexical_source_fails_explicitly():
    result = scan_source('bad.lean', b'theorem x\xff : True')
    assert result['disposition'] == 'decode_error'
    assert result['records'] == []
    assert result['diagnostics'][0]['code'] == 'invalid_utf8'


def test_named_end_closes_enclosing_namespace_across_anonymous_sections():
    data = b'namespace A\nnoncomputable section\ndef x := 1\nend A\nnamespace B\ndef y := 2\nend B\n'
    result = scan_source('scope.lean', data)
    assert [r['qualified_name'] for r in result['records']] == ['A.x', 'B.y']
    assert result['diagnostics'] == []


def test_lean_multiline_names_and_mixed_attributes_modifiers():
    data = b'@[simp] private noncomputable def first := 1\ntheorem\n  second : True := by trivial\n'
    result = scan_source('head.lean', data)
    assert [r['name'] for r in result['records']] == ['first', 'second']
    assert result['diagnostics'] == []


def test_lean_quoted_keyword_identifiers_do_not_split_headers():
    data = 'def «where» : Nat := 1\n'.encode()
    record = scan_source('quoted.lean', data)['records'][0]
    assert record['header_sha256'] == digest(data[:data.index(b':=')])


def test_lean_unterminated_string_reports_even_when_quote_is_last_byte():
    result = scan_source('bad.lean', b'def x := "')
    assert any(d['code'] == 'unterminated_string' for d in result['diagnostics'])


def test_lean_instance_priority_with_named_identifier():
    data = b'instance (priority := 100) named : Inhabited Nat := <0>\n'
    record = scan_source('instance.lean', data)['records'][0]
    assert record['name'] == 'named'
    assert record['header_sha256'] == digest(data[:data.index(b':= <')])


def test_anonymous_sections_and_end_do_not_take_next_command_as_name():
    data = b'namespace A\nsection\ndef x := 1\nend\ndef y := 2\nend A\ndef z := 3\n'
    result = scan_source('anonymous.lean', data)
    assert [r['qualified_name'] for r in result['records']] == ['A.x', 'A.y', 'z']
    assert result['diagnostics'] == []


def test_tex_verbatim_string_and_comment_combinations_suppress_commands():
    data = br'''\verb|\begin{theorem}false\end{theorem}|
\begin{verbatim}
% \end{verbatim} is literal inside this line
\end{verbatim}
\begin{lemma}real\end{lemma}
'''
    # The first end{verbatim} lexically terminates TeX verbatim; the rest remains
    # outside. A comment must not expose the hidden mathematical environment.
    result = scan_source('opaque.tex', data)
    assert [r['kind'] for r in result['records']] == ['lemma']


def test_lean_raw_strings_suppress_embedded_quoted_declarations():
    data = b'def s := r#"a "quote"\ntheorem hidden : True := by trivial\n"#\ndef real := 1\n'
    result = scan_source('raw.lean', data)
    assert [r['name'] for r in result['records']] == ['s', 'real']


def test_anonymous_section_followed_by_variable_and_end_by_theorem():
    data = b'namespace A\nsection\nvariable (x : Nat)\ndef d := x\nend\ntheorem t : True := by trivial\nend A\n'
    result = scan_source('scope2.lean', data)
    assert result['diagnostics'] == []
    assert [r['qualified_name'] for r in result['records']] == ['A.d', 'A.t']


def test_lean_raw_string_with_single_embedded_quote():
    data = b'def s := r##"one "\ntheorem hidden : True := by trivial\n"##\ndef real := 1\n'
    result = scan_source('raw2.lean', data)
    assert [r['name'] for r in result['records']] == ['s', 'real']
    assert result['diagnostics'] == []


def test_lean_local_instances_and_mutual_end_preserve_namespace():
    # Reduced from the pinned upstream lean/ComparatorChallenges/WitnessedChoice.lean.
    data = b'namespace OAI\nlocal instance : Inhabited Nat := <0>\nmutual\n  inductive Term where\n    | atom\n  inductive Formula where\n    | truth\nend\ndef after := 1\nend OAI\n'
    result = scan_source('WitnessedChoice.lean', data)
    assert [r['kind'] for r in result['records']] == ['instance', 'inductive', 'inductive', 'def']
    assert result['records'][-1]['qualified_name'] == 'OAI.after'
    assert result['diagnostics'] == []


def test_lean_file_wide_noncomputable_section_can_end_at_eof():
    # Pinned upstream HardSphere.lean opens a file-wide noncomputable section.
    result = scan_source('HardSphere.lean', b'noncomputable section\nnamespace OAI.HardSphere\ndef x := 1\nend OAI.HardSphere\n')
    assert result['diagnostics'] == []


def test_tex_comment_cannot_start_verbatim_environment():
    data = br'''% \begin{verbatim}
\begin{theorem}real\end{theorem}
\begin{verbatim}literal\end{verbatim}
'''
    result = scan_source('comment.tex', data)
    assert [r['kind'] for r in result['records']] == ['theorem']


def test_tex_unclosed_verbatim_masks_fake_declarations_explicitly():
    result = scan_source('verbatim.tex', br'\begin{verbatim}\begin{theorem}fake\end{theorem}')
    assert result['records'] == []
    assert any(d['code'] == 'unterminated_verbatim' for d in result['diagnostics'])


def test_tex_percent_verb_delimiter_is_not_comment():
    data = br'\verb%literal% \begin{theorem}real\end{theorem}'
    result = scan_source('verb.tex', data)
    assert [r['kind'] for r in result['records']] == ['theorem']


def test_lean_unicode_identifier_continuation_is_not_keyword_boundary():
    data = 'def real := by\n  theoremα\n  exact 1\ndef αwhereβ := 2\n'.encode()
    result = scan_source('boundary.lean', data)
    assert [r['name'] for r in result['records']] == ['real', 'αwhereβ']
    second = result['records'][1]
    assert second['header_sha256'] == digest(data[second['start_byte']:data.rindex(b':=')])


def test_lean_primed_identifiers_retain_all_primes():
    result = scan_source('prime.lean', b"def value''' := 1\n")
    assert result['records'][0]['name'] == "value'''"
