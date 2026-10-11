from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


DEFAULT_FORBIDDEN_PATHS = [
    "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3",
]


@dataclass
class IsolationConfig:
    forbidden_write_paths: list[str] = field(
        default_factory=lambda: list(DEFAULT_FORBIDDEN_PATHS)
    )
    forbidden_read_paths: list[str] = field(
        default_factory=lambda: list(DEFAULT_FORBIDDEN_PATHS)
    )
    normal_runtime_reads_mapeogeo: bool = False

    def is_forbidden(self, path: str | Path, is_write: bool = False) -> bool:
        normalized = str(Path(path).as_posix()).lower()
        targets = self.forbidden_write_paths if is_write else (
            self.forbidden_write_paths if self.normal_runtime_reads_mapeogeo
            else self.forbidden_read_paths + self.forbidden_write_paths
        )
        for target in targets:
            norm_target = str(Path(target).as_posix()).lower()
            if (
                normalized == norm_target
                or normalized.endswith(norm_target)
                or normalized.startswith(norm_target)
                or normalized.startswith(norm_target.rstrip("/") + "/")
            ):
                return True
        return False


@dataclass
class ResourceLimits:
    disk_warn_free_gb: float = 18.0
    disk_stop_free_gb: float = 14.0
    ram_warn_available_mb: float = 450.0
    ram_stop_available_mb: float = 300.0
    swap_stop_used_gb: float = 2.5
    thermal_warn_c: float = 70.0
    thermal_stop_c: float = 77.0
    load1_stop: float = 3.25
    max_worker_rss_mb: float = 650.0


@dataclass
class StorageCaps:
    raw_gb: float = 6.0
    cache_gb: float = 2.0
    work_db_gb: float = 2.0
    graph_db_gb: float = 3.0
    evidence_gb: float = 2.0
    snapshots_gb: float = 2.0
    temp_quarantine_gb: float = 1.0


@dataclass
class SQLiteSettings:
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    temp_store: str = "FILE"
    cache_kib: int = 65536
    mmap_bytes: int = 67108864
    busy_timeout_ms: int = 5000


@dataclass
class BatchSettings:
    source_documents: int = 25
    fragments: int = 100
    equations: int = 100


@dataclass
class CrawlerSettings:
    max_citation_depth: int = 2
    max_new_urls_per_source: int = 25
    max_payload_mb: int = 100
    request_timeout_sec: float = 30.0
    user_agent: str = "SOVCTX-Ingest/0.1 (+https://github.com/NB11B/MAPEOGEO)"


@dataclass
class PromotionSettings:
    auto_canonical: bool = False
    require_full_qualification: bool = True


@dataclass
class NanoConfig:
    root: Path
    data_root: Path
    canonical_repo_branch: str = "research/sovctx-kg"
    nano_candidate_branch: str = "nano/sovctx-ingest"
    isolation: IsolationConfig = field(default_factory=IsolationConfig)
    resources: ResourceLimits = field(default_factory=ResourceLimits)
    storage_caps: StorageCaps = field(default_factory=StorageCaps)
    sqlite: SQLiteSettings = field(default_factory=SQLiteSettings)
    batch: BatchSettings = field(default_factory=BatchSettings)
    crawler: CrawlerSettings = field(default_factory=CrawlerSettings)
    promotion: PromotionSettings = field(default_factory=PromotionSettings)

    @property
    def raw_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def cas_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def cache_dir(self) -> Path:
        return self.data_root / "cache"

    @property
    def staging_dir(self) -> Path:
        return self.data_root / "staging"

    @property
    def quarantine_dir(self) -> Path:
        return self.data_root / "quarantine"

    @property
    def db_dir(self) -> Path:
        return self.data_root / "db"

    @property
    def work_db_path(self) -> Path:
        return self.data_root / "db" / "sovctx_work.sqlite3"

    @property
    def graph_db_path(self) -> Path:
        return self.data_root / "db" / "sovctx_graph.sqlite3"

    @property
    def evidence_dir(self) -> Path:
        return self.data_root / "evidence"

    @property
    def snapshots_dir(self) -> Path:
        return self.data_root / "snapshots"

    @property
    def logs_dir(self) -> Path:
        return self.data_root / "logs"

    @property
    def tmp_dir(self) -> Path:
        return self.data_root / "tmp"

    @property
    def pause_file(self) -> Path:
        return self.data_root / "PAUSE"

    def ensure_directories(self) -> None:
        dirs = [
            self.raw_dir,
            self.cache_dir,
            self.staging_dir,
            self.quarantine_dir,
            self.db_dir,
            self.evidence_dir / "runs",
            self.evidence_dir / "manifests",
            self.evidence_dir / "equation_results",
            self.snapshots_dir,
            self.logs_dir,
            self.tmp_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


def parse_yaml_or_json(text: str) -> dict[str, Any]:
    if yaml is not None:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    import json
    return json.loads(text)


def load_config(path: str | Path | None = None) -> NanoConfig:
    if path is None:
        env_path = os.environ.get("SOVCTX_CONFIG")
        if env_path and Path(env_path).exists():
            path = Path(env_path)
        else:
            default_path = (
                Path(__file__).resolve().parents[1] / "deploy" / "nano" / "config.example.yaml"
            )
            if default_path.exists():
                path = default_path

    if path and Path(path).exists():
        raw = parse_yaml_or_json(Path(path).read_text(encoding="utf-8"))
    else:
        raw = {}

    runtime = raw.get("runtime", {})
    configured_root = runtime.get("root")
    if configured_root and Path(configured_root).exists():
        root = Path(configured_root)
    else:
        # Check if parent is sovctx or repo root
        node_dir = Path(__file__).resolve().parent
        sovctx_dir = node_dir.parent
        repo_dir = sovctx_dir.parent
        if (sovctx_dir / "corpus").exists():
            root = sovctx_dir
        else:
            root = repo_dir

    configured_data_root = runtime.get("data_root")
    if configured_data_root and (Path(configured_data_root).exists() or os.name != "nt"):
        data_root = Path(configured_data_root)
    else:
        data_root = root / ".data"

    iso_raw = raw.get("isolation", {})
    isolation = IsolationConfig(
        forbidden_write_paths=iso_raw.get("forbidden_write_paths", list(DEFAULT_FORBIDDEN_PATHS)),
        forbidden_read_paths=iso_raw.get("forbidden_read_paths", list(DEFAULT_FORBIDDEN_PATHS)),
        normal_runtime_reads_mapeogeo=iso_raw.get("normal_runtime_reads_mapeogeo", False),
    )

    res_raw = raw.get("resources", {})
    resources = ResourceLimits(
        disk_warn_free_gb=float(res_raw.get("disk_warn_free_gb", 18.0)),
        disk_stop_free_gb=float(res_raw.get("disk_stop_free_gb", 14.0)),
        ram_warn_available_mb=float(res_raw.get("ram_warn_available_mb", 450.0)),
        ram_stop_available_mb=float(res_raw.get("ram_stop_available_mb", 300.0)),
        swap_stop_used_gb=float(res_raw.get("swap_stop_used_gb", 2.5)),
        thermal_warn_c=float(res_raw.get("thermal_warn_c", 70.0)),
        thermal_stop_c=float(res_raw.get("thermal_stop_c", 77.0)),
        load1_stop=float(res_raw.get("load1_stop", 3.25)),
        max_worker_rss_mb=float(res_raw.get("max_worker_rss_mb", 650.0)),
    )

    caps_raw = raw.get("storage_caps", {})
    storage_caps = StorageCaps(
        raw_gb=float(caps_raw.get("raw_gb", 6.0)),
        cache_gb=float(caps_raw.get("cache_gb", 2.0)),
        work_db_gb=float(caps_raw.get("work_db_gb", 2.0)),
        graph_db_gb=float(caps_raw.get("graph_db_gb", 3.0)),
        evidence_gb=float(caps_raw.get("evidence_gb", 2.0)),
        snapshots_gb=float(caps_raw.get("snapshots_gb", 2.0)),
        temp_quarantine_gb=float(caps_raw.get("temp_quarantine_gb", 1.0)),
    )

    sql_raw = raw.get("sqlite", {})
    sqlite = SQLiteSettings(
        journal_mode=sql_raw.get("journal_mode", "WAL"),
        synchronous=sql_raw.get("synchronous", "NORMAL"),
        temp_store=sql_raw.get("temp_store", "FILE"),
        cache_kib=int(sql_raw.get("cache_kib", 65536)),
        mmap_bytes=int(sql_raw.get("mmap_bytes", 67108864)),
        busy_timeout_ms=int(sql_raw.get("busy_timeout_ms", 5000)),
    )

    batch_raw = raw.get("batch", {})
    batch = BatchSettings(
        source_documents=int(batch_raw.get("source_documents", 25)),
        fragments=int(batch_raw.get("fragments", 100)),
        equations=int(batch_raw.get("equations", 100)),
    )

    crawler_raw = raw.get("crawler", {})
    crawler = CrawlerSettings(
        max_citation_depth=int(crawler_raw.get("max_citation_depth", 2)),
        max_new_urls_per_source=int(crawler_raw.get("max_new_urls_per_source", 25)),
        max_payload_mb=int(crawler_raw.get("max_payload_mb", 100)),
        request_timeout_sec=float(crawler_raw.get("request_timeout_sec", 30.0)),
        user_agent=crawler_raw.get("user_agent", "SOVCTX-Ingest/0.1 (+https://github.com/NB11B/MAPEOGEO)"),
    )

    promo_raw = raw.get("promotion", {})
    promotion = PromotionSettings(
        auto_canonical=promo_raw.get("auto_canonical", False),
        require_full_qualification=promo_raw.get("require_full_qualification", True),
    )

    return NanoConfig(
        root=root,
        data_root=data_root,
        canonical_repo_branch=runtime.get("canonical_repo_branch", "research/sovctx-kg"),
        nano_candidate_branch=runtime.get("nano_candidate_branch", "nano/sovctx-ingest"),
        isolation=isolation,
        resources=resources,
        storage_caps=storage_caps,
        sqlite=sqlite,
        batch=batch,
        crawler=crawler,
        promotion=promotion,
    )
