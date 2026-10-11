from __future__ import annotations

WORK_SCHEMA_VERSION = "0.1"

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
CREATE TABLE IF NOT EXISTS work_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 1. Fetch queue for bounded discovery and acquisition
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

-- 2. Audit ledger of every fetch attempt
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

-- 3. Content-Addressed Store (CAS) registry of raw immutable source blobs
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

-- 4. Extracted candidate sources (before canonical promotion)
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

-- 5. Extracted candidate fragments grounded in source blobs
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

-- 6. Candidate equations bound to fragments
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

-- 7. Candidate symbols from equations
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

-- 8. Candidate historical claims
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

-- 9. Candidate graph edges
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

-- 10. Behavioral test execution records
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

-- 11. Staging queue for canonical promotion review
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

-- 12. Quarantine ledger for unsafe/oversized/malformed payloads
CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    sha256 TEXT,
    quarantine_reason TEXT NOT NULL,
    file_path TEXT,
    quarantined_at TEXT NOT NULL,
    metadata_json TEXT
);

-- 13. Daemon lifecycle and telemetry ledger
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

-- 14. Hardware resource telemetry samples
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
"""
