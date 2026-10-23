import subprocess
import sys
from pathlib import Path

stage2 = Path(__file__).resolve().parents[2]
here = Path(__file__).resolve().parent
manifest = here / 'manifest_01.json'
command = [
    sys.executable, '-m', 'cli.batch_verify', '--manifest', str(manifest),
    '--resume', '--allow-report-upload', '--provider', 'deepseek',
    '--model', 'deepseek-flash', '--concurrency', '2',
    '--element-retries', '1', '--formal-retries', '1',
    '--lean-formal-input', '--continue-on-review',
    '--claim-verdict', 'signals', '--prompt-version', 'semantic-live',
    '--output', str(here / 'runs'),
]
print('=== LIVE13 VERBATIM IMPACT BLIND BATCH ===', flush=True)
result = subprocess.run(command, cwd=stage2)
raise SystemExit(result.returncode)
