"""Verify the delivered repository without executing controls or loading models."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parent
IGNORED = {'.git', '__pycache__', '.venv', 'venv', 'env', '.ipynb_checkpoints'}

def files():
    return {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob('*')
            if p.is_file() and not any(part in IGNORED for part in p.relative_to(ROOT).parts)
            and p.name != 'SHA256SUMS.json'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    expected = json.loads((ROOT/'SHA256SUMS.json').read_text(encoding='utf-8'))
    actual = files()
    assert set(actual) == set(expected), {'missing': sorted(set(expected)-set(actual)), 'extra': sorted(set(actual)-set(expected))}
    for name, path in actual.items():
        assert sha(path) == expected[name], 'Hash mismatch: '+name
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
    baseline = json.loads((ROOT/'docs/source_preservation.json').read_text(encoding='utf-8'))
    snapshot = ROOT/'revision/analysis/data/Suzuki-Miyaura-Automation-main_v20'
    for name, record in baseline['baseline_files'].items():
        assert sha(snapshot/name) == record['source_sha256'], name
        assert (ROOT/name).is_file(), 'Baseline path missing: '+name
        if record['status'] == 'unchanged':
            assert sha(ROOT/name) == record['source_sha256'], name
    print('PASS:', len(actual), 'manifest entries;', len(baseline['baseline_files']), 'baseline paths and input files preserved; Python syntax valid.')

if __name__ == '__main__':
    main()
