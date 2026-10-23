#!/usr/bin/env python3
"""Run frozen semantic-live-17 blind manifests without exposing labels."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))

from prompts.active import resolve_prompt_set  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_frozen_selection():
    selection = json.loads((HERE / 'SELECTION.json').read_text())
    if selection.get('status') != 'frozen_before_model_run':
        raise SystemExit('blind selection is not frozen')
    for name, expected in selection['code_sha256'].items():
        if sha((STAGE2 / name).read_bytes()) != expected:
            raise SystemExit(f'code changed after selection freeze: {name}')
    prompts = resolve_prompt_set('semantic-live-17', 'ids', 'core')
    if (prompts.sha256('element') != selection['element_prompt_sha256'] or
            prompts.sha256('formal') != selection['formal_prompt_sha256']):
        raise SystemExit('prompt changed after selection freeze')


def main():
    check_frozen_selection()
    for index in (1, 2):
        output = HERE / f'runs_{index:02d}'
        if output.exists():
            raise SystemExit(f'refusing to overwrite existing run directory: {output}')
        command = [
            sys.executable, '-m', 'cli.batch_verify',
            '--manifest', str(HERE / f'manifest_{index:02d}.json'),
            '--output', str(output), '--allow-report-upload',
            '--provider', 'deepseek', '--model', 'deepseek-flash',
            '--prompt-version', 'semantic-live-17', '--concurrency', '2',
            '--readiness-retries', '1', '--element-retries', '1',
            '--formal-retries', '1', '--lean-formal-input',
            '--continue-on-review', '--claim-verdict', 'signals',
            '--deepseek-proxy', 'direct',
        ]
        print(f'START blind batch {index:02d}', flush=True)
        subprocess.run(command, cwd=STAGE2, check=True)
    check_frozen_selection()


if __name__ == '__main__':
    main()
