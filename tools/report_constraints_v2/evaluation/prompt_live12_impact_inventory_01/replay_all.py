import json
import subprocess
import sys
from pathlib import Path

stage2 = Path(__file__).resolve().parents[2]
root = Path(__file__).resolve().parent / 'runs'
results = []
for directory in sorted(p for p in root.iterdir()
                        if p.is_dir() and (p / 'status.json').exists()):
    status = json.loads((directory / 'status.json').read_text())
    if not (directory / 'formalization-ids.json').is_file():
        if status.get('acceptance_status') == 'needs_impact_review':
            proc = subprocess.run(
                [sys.executable, '-m', 'cli.batch_verify', 'verify', str(directory)],
                cwd=stage2, capture_output=True, text=True)
            try:
                value = json.loads(proc.stdout)
            except json.JSONDecodeError:
                value = {'offline_verified': False,
                         'error': proc.stderr[-4000:], 'stdout': proc.stdout[-1000:]}
            results.append({'case_id': directory.name, 'returncode': proc.returncode,
                            **value})
            print(json.dumps({'case_id': directory.name,
                              'offline_verified': value.get('offline_verified'),
                              'acceptance_status': status.get('acceptance_status')},
                             ensure_ascii=False), flush=True)
        else:
            value = {'offline_verified': None, 'not_applicable': True,
                     'reason': 'Extraction stopped before P/I/V artifacts were produced',
                     'model_calls': 0}
            results.append({'case_id': directory.name, 'returncode': 0, **value})
            print(json.dumps({'case_id': directory.name, 'not_applicable': True,
                              'reason': status.get('error')}, ensure_ascii=False),
                  flush=True)
        continue
    proc = subprocess.run(
        [sys.executable, '-m', 'cli.batch_verify', 'verify', str(directory)],
        cwd=stage2, capture_output=True, text=True)
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError:
        value = {'offline_verified': False, 'error': proc.stderr[-4000:],
                 'stdout': proc.stdout[-1000:]}
    results.append({'case_id': directory.name, 'returncode': proc.returncode,
                    **value})
    print(json.dumps({'case_id': directory.name,
                      'offline_verified': value.get('offline_verified'),
                      'error': value.get('error')}, ensure_ascii=False), flush=True)
(root.parent / 'OFFLINE_REPLAY.json').write_text(json.dumps({
    'schema_version': 'stage2-impact-inventory-offline-replay/1',
    'model_calls': 0, 'results': results,
}, ensure_ascii=False, indent=2) + '\n')
