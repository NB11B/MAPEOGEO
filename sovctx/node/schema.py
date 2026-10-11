from __future__ import annotations

WORK_SCHEMA_VERSION = "0.5"

WORK_PRAGMAS = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = FILE;
PRAGMA cache_size = -65536;
PRAGMA mmap_size = 67108864;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
"""

WORK_SCHEMA = """
-- 1. Metadata and schema version tracking
CREATE TABLE IF NOT EXISTS work_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 2. Fetch queue for bounded discovery and acquisition
CREATE TABLE IF NOT EXISTS fetch_queue (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    url TEXT NOT NULL UNIQUE,
    priority TEXT NOT NULL DEFAULT 'P1',
    status TEXT NOT NULL DEFAULT 'QUEUED',
    goal TEXT,
    etag TEXT,
    last_modified TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    nominated_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 3. Audit ledger of every fetch attempt
CREATE TABLE IF NOT EXISTS fetch_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id TEXT NOT NULL,
    url TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status_code INTEGER,
    headers_json TEXT,
    bytes_downloaded INTEGER,
    sha256 TEXT,
    elapsed_sec REAL,
    error_message TEXT,
    attempted_at TEXT NOT NULL,
    FOREIGN KEY(queue_id) REFERENCES fetch_queue(id)
);

-- 4. Content-Addressed Store (CAS) registry of raw immutable source blobs
CREATE TABLE IF NOT EXISTS source_blobs (
    sha256 TEXT PRIMARY KEY,
    storage_path TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    content_type TEXT,
    inferred_type TEXT,
    first_acquired_at TEXT NOT NULL,
    first_url TEXT NOT NULL,
    verified_hash INTEGER NOT NULL DEFAULT 1
);

-- 5. Extracted candidate sources (before canonical promotion)
CREATE TABLE IF NOT EXISTS candidate_sources (
    id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    originating_queue_item TEXT,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT,
    FOREIGN KEY(sha256) REFERENCES source_blobs(sha256)
);

-- 6. Extracted candidate fragments grounded in source blobs
CREATE TABLE IF NOT EXISTS candidate_fragments (
    id TEXT PRIMARY KEY,
    candidate_source_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    locator TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT,
    FOREIGN KEY(candidate_source_id) REFERENCES candidate_sources(id)
);

-- 7. Candidate equations bound to fragments
CREATE TABLE IF NOT EXISTS candidate_equations (
    id TEXT PRIMARY KEY,
    source_fragment_id TEXT NOT NULL,
    equation_family TEXT,
    original_notation TEXT NOT NULL,
    normalized_notation TEXT,
    extracted_at TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT,
    FOREIGN KEY(source_fragment_id) REFERENCES candidate_fragments(id)
);

-- 8. Candidate symbols from equations
CREATE TABLE IF NOT EXISTS candidate_symbols (
    id TEXT PRIMARY KEY,
    candidate_equation_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    native_name TEXT,
    meaning TEXT,
    extracted_at TEXT NOT NULL,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT,
    FOREIGN KEY(candidate_equation_id) REFERENCES candidate_equations(id)
);

-- 9. Candidate historical claims
CREATE TABLE IF NOT EXISTS candidate_claims (
    id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    source_fragment_ids_json TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT
);

-- 10. Candidate graph edges
CREATE TABLE IF NOT EXISTS candidate_edges (
    id TEXT PRIMARY KEY,
    edge_type TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    originating_queue_item TEXT,
    candidate_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT
);

-- 11. Behavioral test execution records
CREATE TABLE IF NOT EXISTS behavior_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_equation_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    test_type TEXT NOT NULL,
    verdict TEXT NOT NULL,
    evaluator_version TEXT NOT NULL,
    details_json TEXT,
    executed_at TEXT NOT NULL,
    FOREIGN KEY(candidate_equation_id) REFERENCES candidate_equations(id)
);

-- 12. Staging queue for canonical promotion review
CREATE TABLE IF NOT EXISTS promotion_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    current_status TEXT NOT NULL,
    target_status TEXT NOT NULL,
    qualification_receipt_json TEXT NOT NULL,
    queued_at TEXT NOT NULL,
    promoted_at TEXT,
    decision TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
    reviewer_notes TEXT
);

-- 13. Quarantine ledger for unsafe/oversized/malformed payloads
CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    sha256 TEXT,
    quarantine_reason TEXT NOT NULL,
    file_path TEXT,
    quarantined_at TEXT NOT NULL,
    metadata_json TEXT
);

-- 14. Daemon lifecycle and telemetry ledger
CREATE TABLE IF NOT EXISTS daemon_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    daemon_name TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    stopped_at TEXT,
    items_processed INTEGER NOT NULL DEFAULT 0,
    items_succeeded INTEGER NOT NULL DEFAULT 0,
    items_failed INTEGER NOT NULL DEFAULT 0,
    metrics_json TEXT
);

-- 15. Hardware resource telemetry samples
CREATE TABLE IF NOT EXISTS resource_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sampled_at TEXT NOT NULL,
    disk_free_gb REAL NOT NULL,
    ram_available_mb REAL NOT NULL,
    swap_used_gb REAL NOT NULL,
    thermal_max_c REAL,
    load_1m REAL,
    worker_rss_mb REAL,
    guard_verdict TEXT NOT NULL,
    guard_reasons TEXT
);

-- 16. Native terms identified across passages
CREATE TABLE IF NOT EXISTS candidate_terms (
    id TEXT PRIMARY KEY,
    surface_form TEXT NOT NULL,
    normalized_unicode TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'ru',
    script TEXT NOT NULL DEFAULT 'Cyrillic',
    term_type TEXT NOT NULL,
    technicality_score REAL NOT NULL,
    signals_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CANDIDATE',
    rejection_reason TEXT
);

-- 17. Grounded occurrences of terms in specific passages
CREATE TABLE IF NOT EXISTS candidate_term_occurrences (
    id TEXT PRIMARY KEY,
    term_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    surface_form TEXT NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    sentence_index INTEGER NOT NULL,
    context_snippet TEXT,
    FOREIGN KEY(term_id) REFERENCES candidate_terms(id),
    FOREIGN KEY(passage_id) REFERENCES candidate_fragments(id)
);

-- 18. Interpretive and morphological relationships between terms
CREATE TABLE IF NOT EXISTS candidate_term_relations (
    id TEXT PRIMARY KEY,
    from_term_id TEXT NOT NULL,
    to_term_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    method TEXT NOT NULL,
    confidence REAL NOT NULL,
    details_json TEXT,
    FOREIGN KEY(from_term_id) REFERENCES candidate_terms(id)
);

-- 19. Candidate definition spans and trigger patterns
CREATE TABLE IF NOT EXISTS candidate_definition_spans (
    id TEXT PRIMARY KEY,
    passage_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    subject_term_id TEXT,
    trigger TEXT NOT NULL,
    defining_span TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY(passage_id) REFERENCES candidate_fragments(id),
    FOREIGN KEY(subject_term_id) REFERENCES candidate_terms(id)
);

-- 20. Mathematical symbol occurrences bound to local context
CREATE TABLE IF NOT EXISTS candidate_symbol_occurrences (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    source_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    equation_witness_id TEXT,
    surface_context TEXT NOT NULL,
    meaning_candidate TEXT,
    FOREIGN KEY(passage_id) REFERENCES candidate_fragments(id)
);

-- 21. Historical equation witnesses preserving unnormalized surface notation
CREATE TABLE IF NOT EXISTS candidate_equation_witnesses (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    page_physical INTEGER NOT NULL,
    surface_representation TEXT NOT NULL,
    locator TEXT,
    neighboring_terms_json TEXT,
    neighboring_symbols_json TEXT,
    extraction_method TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY(passage_id) REFERENCES candidate_fragments(id)
);

-- 22. Bibliographic reference candidates extracted from literature (SOVREF:...)
CREATE TABLE IF NOT EXISTS reference_candidates (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    reference_index INTEGER,
    raw_reference TEXT NOT NULL,
    authors_raw TEXT,
    title_raw TEXT,
    publication_raw TEXT,
    year_raw INTEGER,
    volume_raw TEXT,
    issue_raw TEXT,
    pages_raw TEXT,
    identifier_raw TEXT,
    language TEXT NOT NULL DEFAULT 'ru',
    extraction_method TEXT NOT NULL DEFAULT 'regex_citations_v0.2',
    confidence REAL NOT NULL DEFAULT 0.85
);

-- 23. Resolution attempts matching reference candidates to candidate sources
CREATE TABLE IF NOT EXISTS reference_resolution_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_id TEXT NOT NULL,
    candidate_source_id TEXT,
    resolution_state TEXT NOT NULL DEFAULT 'UNRESOLVED',
    confidence REAL NOT NULL DEFAULT 0.0,
    resolved_url TEXT,
    author_score REAL NOT NULL DEFAULT 0.0,
    title_score REAL NOT NULL DEFAULT 0.0,
    year_score REAL NOT NULL DEFAULT 0.0,
    identifier_score REAL NOT NULL DEFAULT 0.0,
    attempted_at TEXT NOT NULL,
    details_json TEXT,
    FOREIGN KEY(reference_id) REFERENCES reference_candidates(id)
);

-- 24. Frontier items driving targeted acquisition and expansion (SOVFRONT:...)
CREATE TABLE IF NOT EXISTS frontier_items (
    id TEXT PRIMARY KEY,
    frontier_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P1',
    dedup_key TEXT NOT NULL UNIQUE,
    target_label TEXT NOT NULL,
    normalized_target TEXT NOT NULL,
    origin_source_id TEXT NOT NULL,
    origin_passage_id TEXT,
    raw_support_count INTEGER NOT NULL DEFAULT 1,
    independent_source_count INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'OPEN',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 25. Evidence links binding frontier items to citations, terms, or entities
CREATE TABLE IF NOT EXISTS frontier_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frontier_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    passage_id TEXT,
    weight REAL NOT NULL DEFAULT 1.0,
    observed_at TEXT NOT NULL,
    FOREIGN KEY(frontier_id) REFERENCES frontier_items(id)
);

-- 26. Concrete source nominations feeding into fetch_queue (SOVNOM:...)
CREATE TABLE IF NOT EXISTS source_nominations (
    id TEXT PRIMARY KEY,
    frontier_id TEXT NOT NULL,
    nominated_url TEXT NOT NULL,
    goal TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P1',
    nomination_reason TEXT NOT NULL,
    nominated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    acquired_source_id TEXT,
    FOREIGN KEY(frontier_id) REFERENCES frontier_items(id)
);

-- 27. Historical entity mentions (Person, Institution, Method, Instrument)
CREATE TABLE IF NOT EXISTS entity_mentions (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    surface_text TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    source_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.85,
    details_json TEXT
);

-- 28. Complete acquisition causality ledger (Source <- Nom <- Frontier <- Evidence <- Origin)
CREATE TABLE IF NOT EXISTS acquisition_provenance (
    source_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL DEFAULT 0,
    nomination_id TEXT,
    frontier_id TEXT,
    origin_source_id TEXT,
    origin_passage_id TEXT,
    frontier_type TEXT,
    reason TEXT,
    resolution_state TEXT,
    parent_path_json TEXT,
    recorded_at TEXT NOT NULL
);

-- 29. Source-family classification (IDENTICAL_BLOB, SAME_SCAN, SAME_EDITION, SAME_WORK, TRANSLATION_OF, DERIVED_FROM, UNKNOWN_RELATION)
CREATE TABLE IF NOT EXISTS source_family_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id_a TEXT NOT NULL,
    source_id_b TEXT NOT NULL,
    relationship TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    details_json TEXT,
    observed_at TEXT NOT NULL
);

-- 30. Candidate research school clusters (Person -> Institution -> Publication -> Term -> Method)
CREATE TABLE IF NOT EXISTS research_school_candidates (
    id TEXT PRIMARY KEY,
    school_label TEXT NOT NULL,
    lead_person TEXT NOT NULL,
    institution TEXT NOT NULL,
    methods_json TEXT NOT NULL,
    terms_json TEXT NOT NULL,
    supporting_sources_json TEXT NOT NULL,
    subgraph_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    discovered_at TEXT NOT NULL
);

-- 31. First-class temporal intervals for historical entities and institutional lineages
CREATE TABLE IF NOT EXISTS temporal_entity_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    valid_from INTEGER,
    valid_to INTEGER,
    source_date INTEGER,
    observation_date TEXT,
    asserted_date TEXT,
    relation_type TEXT,
    target_entity TEXT,
    observed_at TEXT NOT NULL
);

-- 32. Historical synthesis dossiers with explicit evidence packets and support classes
CREATE TABLE IF NOT EXISTS historical_synthesis_dossiers (
    id TEXT PRIMARY KEY,
    proposed_label TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    promotion_state TEXT NOT NULL,
    support_class TEXT NOT NULL,
    raw_sources_count INTEGER NOT NULL,
    independent_sources_count INTEGER NOT NULL,
    independence_ratio REAL NOT NULL,
    earliest_year INTEGER,
    latest_year INTEGER,
    temporal_validity TEXT NOT NULL,
    dossier_json TEXT NOT NULL,
    synthesized_at TEXT NOT NULL
);

-- 33. Multi-type historical lineages (intellectual, institutional, terminological, technical)
CREATE TABLE IF NOT EXISTS lineage_candidates (
    id TEXT PRIMARY KEY,
    lineage_type TEXT NOT NULL,
    source_entity TEXT NOT NULL,
    target_entity TEXT NOT NULL,
    temporal_span_json TEXT NOT NULL,
    supporting_sources_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    details_json TEXT NOT NULL,
    discovered_at TEXT NOT NULL
);

-- 34. First-class contradiction sets preserving conflicting claims and attribution
CREATE TABLE IF NOT EXISTS contradiction_sets (
    id TEXT PRIMARY KEY,
    contradiction_type TEXT NOT NULL,
    entity_or_subject TEXT NOT NULL,
    claim_a_json TEXT NOT NULL,
    claim_b_json TEXT NOT NULL,
    description TEXT NOT NULL,
    observed_at TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_fetch_queue_status_prio ON fetch_queue(status, priority);
CREATE INDEX IF NOT EXISTS idx_fetch_attempts_queue ON fetch_attempts(queue_id);
CREATE INDEX IF NOT EXISTS idx_blobs_sha256 ON source_blobs(sha256);
CREATE INDEX IF NOT EXISTS idx_cand_sources_status ON candidate_sources(status);
CREATE INDEX IF NOT EXISTS idx_cand_frags_src ON candidate_fragments(candidate_source_id);
CREATE INDEX IF NOT EXISTS idx_cand_eq_frag ON candidate_equations(source_fragment_id);
CREATE INDEX IF NOT EXISTS idx_cand_eq_status ON candidate_equations(status);
CREATE INDEX IF NOT EXISTS idx_behavior_runs_eq ON behavior_runs(candidate_equation_id);
CREATE INDEX IF NOT EXISTS idx_resource_samples_time ON resource_samples(sampled_at);
CREATE INDEX IF NOT EXISTS idx_promo_queue_decision ON promotion_queue(decision);
CREATE INDEX IF NOT EXISTS idx_cand_terms_norm ON candidate_terms(normalized_unicode);
CREATE INDEX IF NOT EXISTS idx_cand_term_occ_term ON candidate_term_occurrences(term_id);
CREATE INDEX IF NOT EXISTS idx_cand_term_occ_pass ON candidate_term_occurrences(passage_id);
CREATE INDEX IF NOT EXISTS idx_cand_term_rel_from ON candidate_term_relations(from_term_id);
CREATE INDEX IF NOT EXISTS idx_cand_def_pass ON candidate_definition_spans(passage_id);
CREATE INDEX IF NOT EXISTS idx_cand_sym_occ_pass ON candidate_symbol_occurrences(passage_id);
CREATE INDEX IF NOT EXISTS idx_cand_eq_wit_pass ON candidate_equation_witnesses(passage_id);
CREATE INDEX IF NOT EXISTS idx_ref_cand_src ON reference_candidates(source_id);
CREATE INDEX IF NOT EXISTS idx_ref_cand_pass ON reference_candidates(passage_id);
CREATE INDEX IF NOT EXISTS idx_ref_res_ref ON reference_resolution_attempts(reference_id);
CREATE INDEX IF NOT EXISTS idx_ref_res_state ON reference_resolution_attempts(resolution_state);
CREATE INDEX IF NOT EXISTS idx_frontier_type_prio ON frontier_items(frontier_type, priority);
CREATE INDEX IF NOT EXISTS idx_frontier_dedup ON frontier_items(dedup_key);
CREATE INDEX IF NOT EXISTS idx_frontier_ev_front ON frontier_evidence(frontier_id);
CREATE INDEX IF NOT EXISTS idx_src_nom_front ON source_nominations(frontier_id);
CREATE INDEX IF NOT EXISTS idx_src_nom_status ON source_nominations(status);
CREATE INDEX IF NOT EXISTS idx_entity_type_norm ON entity_mentions(entity_type, normalized_name);
CREATE INDEX IF NOT EXISTS idx_acq_prov_gen ON acquisition_provenance(generation);
CREATE INDEX IF NOT EXISTS idx_acq_prov_origin ON acquisition_provenance(origin_source_id);
CREATE INDEX IF NOT EXISTS idx_src_family_rel ON source_family_relations(source_id_a, source_id_b);
CREATE INDEX IF NOT EXISTS idx_research_school_lead ON research_school_candidates(lead_person);
CREATE INDEX IF NOT EXISTS idx_temp_entity_name ON temporal_entity_intervals(entity_name);
CREATE INDEX IF NOT EXISTS idx_synth_dossiers_type ON historical_synthesis_dossiers(candidate_type);
CREATE INDEX IF NOT EXISTS idx_lineage_type ON lineage_candidates(lineage_type);
CREATE INDEX IF NOT EXISTS idx_contradictions_type ON contradiction_sets(contradiction_type);
"""
