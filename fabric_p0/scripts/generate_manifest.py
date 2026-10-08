#!/usr/bin/env python3
import hashlib
from pathlib import Path

def main():
    repo = Path(__file__).resolve().parent.parent.parent
    base = repo / "fabric_p0"
    exts = {".sv", ".svh", ".sdc", ".py", ".ys", ".v", ".md", ".json"}
    
    lines = [
        "# MAPEOGEO P0 Cryptographic Release Manifest (Gate RTL-11 Vendor FPGA Technology Mapping)",
        "# Standard: FIPS 180-4 SHA-256",
        "# Machine: MAPEOGEO Preproduction Fabric P0",
        ""
    ]
    
    entries = 0
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix in exts:
            if ".pytest_cache" in p.parts or "__pycache__" in p.parts:
                continue
            if p.name == "manifest.sha256":
                continue
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            rel_path = p.relative_to(repo).as_posix()
            lines.append(f"{h}  {rel_path}")
            entries += 1
            
    manifest_path = base / "manifest.sha256"
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Successfully generated {manifest_path} with {entries} verified cryptographic entries.")

if __name__ == "__main__":
    main()
