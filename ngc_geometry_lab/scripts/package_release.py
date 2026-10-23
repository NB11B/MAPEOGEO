"""Package the full source/evidence tree with an independently inspectable manifest.

The output must be outside the project directory and must not already exist.
Only build products, caches, git internals, and draft visual previews are omitted.
"""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


EXCLUDED_DIRECTORIES = {
    '.git', '.venv', '__pycache__', '.pytest_cache', 'build', 'dist',
    'deliverables_preview',
}


def package(project, output):
    project, output = Path(project).resolve(), Path(output).resolve()
    if project == output or project in output.parents:
        raise ValueError('Archive output must be outside the project directory.')
    if not project.is_dir():
        raise ValueError('Project directory does not exist.')
    files = []
    for path in sorted(project.rglob('*')):
        relative = path.relative_to(project)
        if any(part in EXCLUDED_DIRECTORIES or part.endswith('.egg-info') for part in relative.parts):
            continue
        if path.is_file() and path.suffix != '.pyc':
            data = path.read_bytes()
            files.append((relative.as_posix(), data))
    manifest = {
        'format_version': 1,
        'project_directory': 'ngc_geometry_lab',
        'file_count': len(files),
        'files': [{'path': name, 'bytes': len(data),
                   'sha256': hashlib.sha256(data).hexdigest()} for name, data in files],
        'note': 'The manifest lists every included project file; it excludes itself.',
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in files + [('ARCHIVE_MANIFEST.json', manifest_bytes)]:
                info = zipfile.ZipInfo('ngc_geometry_lab/' + name, date_time=(2026, 10, 22, 0, 0, 0))
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data, compresslevel=9)
    print(json.dumps({'archive': str(output), 'file_count': len(files) + 1,
                      'bytes': output.stat().st_size,
                      'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    package(args.project, args.out)
