from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import NanoConfig, load_config

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


class IsolationViolationError(Exception):
    """Raised when a SOVCTX process attempts to access or write to a forbidden path (e.g. MAPEOGEO DB)."""


class ResourcePressurePause(Exception):
    """Raised when SOVCTX operations are paused due to resource thresholds (disk/RAM/swap/thermal/load)."""


@dataclass
class ResourceSample:
    sampled_at: str
    disk_free_gb: float
    ram_available_mb: float
    swap_used_gb: float
    thermal_max_c: Optional[float]
    load_1m: Optional[float]
    worker_rss_mb: Optional[float]
    verdict: str  # "GREEN", "WARN", "STOP"
    reasons: list[str]


class ResourceGuard:
    """Resource governor and physical isolation auditor for Jetson Nano.

    Monitors:
      - Free disk space (warn: <= 18 GB, stop: <= 14 GB)
      - Available RAM (warn: <= 450 MB, stop: <= 300 MB)
      - Swap used (stop: >= 2.5 GB)
      - Temperature (warn: >= 70 C, stop: >= 77 C)
      - 1-minute load average (stop: >= 3.25)
      - Worker process RSS (stop: >= 650 MB)
      - Physical isolation boundaries (MAPEOGEO canonical DB access blocked)
    """

    def __init__(self, config: Optional[NanoConfig] = None) -> None:
        self.config = config or load_config()
        self.pause_file = self.config.pause_file
        self.limits = self.config.resources
        self.isolation = self.config.isolation

    # ------------------------------------------------------------------
    # Physical Isolation
    # ------------------------------------------------------------------

    def assert_isolation(self, path: str | Path, is_write: bool = False) -> None:
        if self.isolation.is_forbidden(path, is_write=is_write):
            mode_str = "write/open" if is_write else "read/open"
            raise IsolationViolationError(
                f"Physical isolation violation: attempted {mode_str} of forbidden path {path}"
            )

    # ------------------------------------------------------------------
    # Resource Metric Sampling
    # ------------------------------------------------------------------

    def sample_disk_free_gb(self, target_path: Optional[Path] = None) -> float:
        check_path = target_path or self.config.data_root
        if not check_path.exists():
            check_path = check_path.parent
            if not check_path.exists():
                check_path = Path(".")
        usage = shutil.disk_usage(check_path)
        return round(usage.free / (1024.0**3), 2)

    def sample_ram_available_mb(self) -> float:
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            try:
                content = meminfo.read_text(encoding="utf-8")
                lookup: dict[str, int] = {}
                for line in content.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        val = parts[1].strip().split()[0]
                        if val.isdigit():
                            lookup[parts[0].strip()] = int(val)
                if "MemAvailable" in lookup:
                    return round(lookup["MemAvailable"] / 1024.0, 2)
                if "MemFree" in lookup:
                    free = lookup["MemFree"] + lookup.get("Buffers", 0) + lookup.get("Cached", 0)
                    return round(free / 1024.0, 2)
            except Exception:
                pass

        if psutil is not None:
            try:
                vm = psutil.virtual_memory()
                return round(vm.available / (1024.0**2), 2)
            except Exception:
                pass

        # Conservative fallback if no proc/psutil
        return 1400.0

    def sample_swap_used_gb(self) -> float:
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            try:
                content = meminfo.read_text(encoding="utf-8")
                lookup: dict[str, int] = {}
                for line in content.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        val = parts[1].strip().split()[0]
                        if val.isdigit():
                            lookup[parts[0].strip()] = int(val)
                if "SwapTotal" in lookup and "SwapFree" in lookup:
                    used_kb = lookup["SwapTotal"] - lookup["SwapFree"]
                    return round(used_kb / (1024.0**2), 2)
            except Exception:
                pass

        if psutil is not None:
            try:
                sm = psutil.swap_memory()
                return round(sm.used / (1024.0**3), 2)
            except Exception:
                pass

        return 0.0

    def sample_thermal_max_c(self) -> Optional[float]:
        # Jetson Nano sysfs thermal zones
        temps: list[float] = []
        thermal_base = Path("/sys/class/thermal")
        if thermal_base.exists():
            try:
                for zone in thermal_base.glob("thermal_zone*"):
                    temp_file = zone / "temp"
                    if temp_file.exists():
                        val_str = temp_file.read_text(encoding="utf-8").strip()
                        if val_str.isdigit():
                            val = float(val_str)
                            # Convert millidegrees (e.g. 45000 -> 45.0 C)
                            if val > 1000:
                                val = val / 1000.0
                            temps.append(val)
            except Exception:
                pass

        if temps:
            return round(max(temps), 1)

        if psutil is not None and hasattr(psutil, "sensors_temperatures"):
            try:
                st = psutil.sensors_temperatures()
                if st:
                    for name, entries in st.items():
                        for entry in entries:
                            if entry.current is not None:
                                temps.append(entry.current)
            except Exception:
                pass

        if temps:
            return round(max(temps), 1)
        return None

    def sample_load_1m(self) -> Optional[float]:
        if hasattr(os, "getloadavg"):
            try:
                return round(os.getloadavg()[0], 2)
            except Exception:
                pass

        loadavg = Path("/proc/loadavg")
        if loadavg.exists():
            try:
                parts = loadavg.read_text(encoding="utf-8").split()
                if parts:
                    return round(float(parts[0]), 2)
            except Exception:
                pass

        return None

    def sample_worker_rss_mb(self, pid: Optional[int] = None) -> Optional[float]:
        target_pid = pid or os.getpid()
        status_file = Path(f"/proc/{target_pid}/status")
        if status_file.exists():
            try:
                for line in status_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[1].isdigit():
                            return round(float(parts[1]) / 1024.0, 2)
            except Exception:
                pass

        if psutil is not None:
            try:
                proc = psutil.Process(target_pid)
                return round(proc.memory_info().rss / (1024.0**2), 2)
            except Exception:
                pass

        return None

    # ------------------------------------------------------------------
    # Verdict Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        disk_free_gb: float,
        ram_available_mb: float,
        swap_used_gb: float,
        thermal_max_c: Optional[float],
        load_1m: Optional[float],
        worker_rss_mb: Optional[float],
    ) -> tuple[str, list[str]]:
        stop_reasons: list[str] = []
        warn_reasons: list[str] = []

        # Disk
        if disk_free_gb <= self.limits.disk_stop_free_gb:
            stop_reasons.append(
                f"Disk free space {disk_free_gb} GB <= stop threshold {self.limits.disk_stop_free_gb} GB"
            )
        elif disk_free_gb <= self.limits.disk_warn_free_gb:
            warn_reasons.append(
                f"Disk free space {disk_free_gb} GB <= warn threshold {self.limits.disk_warn_free_gb} GB"
            )

        # RAM
        if ram_available_mb <= self.limits.ram_stop_available_mb:
            stop_reasons.append(
                f"RAM available {ram_available_mb} MB <= stop threshold {self.limits.ram_stop_available_mb} MB"
            )
        elif ram_available_mb <= self.limits.ram_warn_available_mb:
            warn_reasons.append(
                f"RAM available {ram_available_mb} MB <= warn threshold {self.limits.ram_warn_available_mb} MB"
            )

        # Swap
        if swap_used_gb >= self.limits.swap_stop_used_gb:
            stop_reasons.append(
                f"Swap used {swap_used_gb} GB >= stop threshold {self.limits.swap_stop_used_gb} GB"
            )

        # Thermal
        if thermal_max_c is not None:
            if thermal_max_c >= self.limits.thermal_stop_c:
                stop_reasons.append(
                    f"Thermal peak {thermal_max_c}°C >= stop threshold {self.limits.thermal_stop_c}°C"
                )
            elif thermal_max_c >= self.limits.thermal_warn_c:
                warn_reasons.append(
                    f"Thermal peak {thermal_max_c}°C >= warn threshold {self.limits.thermal_warn_c}°C"
                )

        # Load
        if load_1m is not None:
            if load_1m >= self.limits.load1_stop:
                stop_reasons.append(
                    f"1-min load {load_1m} >= stop threshold {self.limits.load1_stop}"
                )

        # Worker RSS
        if worker_rss_mb is not None:
            if worker_rss_mb >= self.limits.max_worker_rss_mb:
                stop_reasons.append(
                    f"Worker RSS {worker_rss_mb} MB >= limit {self.limits.max_worker_rss_mb} MB"
                )

        if stop_reasons:
            return "STOP", stop_reasons
        if warn_reasons:
            return "WARN", warn_reasons
        return "GREEN", []

    # ------------------------------------------------------------------
    # Control and Pause Signaling
    # ------------------------------------------------------------------

    def is_paused(self) -> bool:
        return self.pause_file.exists()

    def set_pause(self, reasons: list[str]) -> None:
        self.pause_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "paused_at": datetime.now(timezone.utc).isoformat(),
            "reasons": reasons,
        }
        self.pause_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def clear_pause(self) -> None:
        if self.pause_file.exists():
            try:
                self.pause_file.unlink()
            except OSError:
                pass

    def assert_not_paused(self) -> None:
        if self.is_paused():
            try:
                data = json.loads(self.pause_file.read_text(encoding="utf-8"))
                reasons = data.get("reasons", ["PAUSE file present"])
            except Exception:
                reasons = ["PAUSE file present"]
            raise ResourcePressurePause(
                f"SOVCTX operations paused due to resource backpressure: {'; '.join(reasons)}"
            )

    # ------------------------------------------------------------------
    # Sample and Record
    # ------------------------------------------------------------------

    def sample(self, db: Optional[Any] = None) -> ResourceSample:
        now = datetime.now(timezone.utc).isoformat()
        disk_free = self.sample_disk_free_gb()
        ram_avail = self.sample_ram_available_mb()
        swap_used = self.sample_swap_used_gb()
        thermal_c = self.sample_thermal_max_c()
        load_1m = self.sample_load_1m()
        worker_rss = self.sample_worker_rss_mb()

        verdict, reasons = self.evaluate(
            disk_free_gb=disk_free,
            ram_available_mb=ram_avail,
            swap_used_gb=swap_used,
            thermal_max_c=thermal_c,
            load_1m=load_1m,
            worker_rss_mb=worker_rss,
        )

        if verdict == "STOP":
            self.set_pause(reasons)
        elif verdict == "GREEN" and self.is_paused():
            # Clear pause when recovered to GREEN
            self.clear_pause()

        sample = ResourceSample(
            sampled_at=now,
            disk_free_gb=disk_free,
            ram_available_mb=ram_avail,
            swap_used_gb=swap_used,
            thermal_max_c=thermal_c,
            load_1m=load_1m,
            worker_rss_mb=worker_rss,
            verdict=verdict,
            reasons=reasons,
        )

        if db is not None:
            try:
                db.record_resource_sample(
                    sampled_at=sample.sampled_at,
                    disk_free_gb=sample.disk_free_gb,
                    ram_available_mb=sample.ram_available_mb,
                    swap_used_gb=sample.swap_used_gb,
                    thermal_max_c=sample.thermal_max_c,
                    load_1m=sample.load_1m,
                    worker_rss_mb=sample.worker_rss_mb,
                    guard_verdict=sample.verdict,
                    guard_reasons=sample.reasons,
                )
            except Exception:
                pass

        return sample
