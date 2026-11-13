"""Non-qualifying, versioned diagnostic for the Theorem 47.9 pagination drift.

Never used by qualification or in place of the accepted PDF identity check.
Call with the unchanged v0.6 normalized span and independently pinned metadata.
Only the terminal page token in this exact running header may be normalized.
"""
import hashlib
import re

NORMALIZATION_VERSION = 'LP47_9_TRAILING_RUNNING_HEADER_PAGE_V1'
HEADER = '\n47.3. COMPLEMENTARY SLACKNESS CONDITIONS '


def audit_span(span: str, accepted_sha256: str, current_page_end: int,
               accepted_page_end: int) -> dict:
    """Compare hashes without returning or persisting copyrighted source prose."""
    if not isinstance(accepted_sha256, str) or not re.fullmatch('[0-9a-f]{64}', accepted_sha256):
        raise ValueError('accepted_sha256 must be a lowercase SHA256')
    if any(type(p) is not int or p <= 0 for p in (current_page_end, accepted_page_end)):
        raise ValueError('page numbers must be positive integers')
    suffix = HEADER + str(current_page_end)
    if not isinstance(span, str) or not span.endswith(suffix):
        raise ValueError('expected terminal running header and page number missing')
    prefix = span[:-len(str(current_page_end))]
    historical_candidate = prefix + str(accepted_page_end)
    digest = lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()
    return {
        'normalization_version': NORMALIZATION_VERSION,
        'current_statement_sha256': digest(span),
        'accepted_statement_sha256': accepted_sha256,
        'reconstructed_historical_sha256': digest(historical_candidate),
        'pagination_normalized_sha256': digest(prefix.rstrip(' ')),
        'historical_span_reconstructed': digest(historical_candidate) == accepted_sha256,
        'current_page_end': current_page_end,
        'accepted_page_end': accepted_page_end,
        'qualifies_source_edition': False,
    }
