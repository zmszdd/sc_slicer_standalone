#!/usr/bin/env python3
"""Run the two frozen semantic-live-16 blind-test manifests."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]

for index in (1, 2):
    command = [
        sys.executable, '-m', 'cli.batch_verify',
        '--manifest', str(HERE / f'manifest_{index:02d}.json'),
        '--output', str(HERE / f'runs_{index:02d}'),
        '--allow-report-upload', '--provider', 'deepseek',
        '--model', 'deepseek-flash', '--prompt-version', 'semantic-live-16',
        '--concurrency', '2', '--readiness-retries', '1',
        '--element-retries', '1', '--formal-retries', '1',
        '--lean-formal-input', '--continue-on-review',
        '--claim-verdict', 'signals',
    ]
    subprocess.run(command, cwd=STAGE2, check=True)
