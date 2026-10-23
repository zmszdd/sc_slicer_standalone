import subprocess
import sys
from pathlib import Path

stage2 = Path(__file__).resolve().parents[2]
run_dir = Path(sys.argv[1]).resolve()
for manifest in sorted(run_dir.glob('manifest_*.json')):
    command = [
        sys.executable, '-m', 'cli.batch_verify', '--manifest', str(manifest),
        '--resume', '--allow-report-upload', '--provider', 'deepseek',
        '--model', 'deepseek-flash', '--concurrency', '2',
        '--element-retries', '1', '--formal-retries', '1',
        '--lean-formal-input', '--continue-on-review',
        '--claim-verdict', 'signals', '--prompt-version', 'semantic-live',
        '--output', str(run_dir / 'runs'),
    ]
    print(f'=== {manifest.name} ===', flush=True)
    result = subprocess.run(command, cwd=stage2)
    if result.returncode:
        raise SystemExit(result.returncode)
