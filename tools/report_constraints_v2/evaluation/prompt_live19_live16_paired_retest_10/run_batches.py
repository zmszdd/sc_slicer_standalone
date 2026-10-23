import subprocess
import sys
from pathlib import Path

stage2 = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
output = here / 'runs'
for batch_no in (1, 2):
    manifest = here / f'manifest_{batch_no:02d}.json'
    command = [
        sys.executable, '-m', 'cli.batch_verify', '--manifest', str(manifest),
        '--resume', '--allow-report-upload', '--provider', 'deepseek',
        '--model', 'deepseek-flash', '--concurrency', '2',
        '--readiness-retries', '1', '--element-retries', '1', '--formal-retries', '1',
        '--lean-formal-input', '--continue-on-review',
        '--claim-verdict', 'signals', '--prompt-version', 'semantic-live',
        '--output', str(output),
    ]
    print(f'=== BATCH {batch_no:02d}/02 ===', flush=True)
    result = subprocess.run(command, cwd=stage2)
    if result.returncode:
        raise SystemExit(result.returncode)
