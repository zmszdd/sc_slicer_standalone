#!/usr/bin/env python3
"""Re-run stage-2 for a fixed list of goldset cases in batches of <=5.

Batch runner ``cli.batch_verify`` enforces a 1..5 case limit and requires
explicit upload consent. This driver writes one manifest per chunk, invokes
``python main.py batch`` with DeepSeek, and copies successful per-case run dirs
back into the goldset ``runs_XX`` layout so stage-3 eval-run can pick them up.

Run from repo root:
    python -m tools.report_constraints_v2.cli.rerun_stage2_cases \
        --goldset-root tools/report_constraints_v2/evaluation/goldset_v2_pos91 \
        --flatten-root /root/poc_repro_work/verified_flatten_pass_1568_exact_cases \
        --cases <cid>[,<cid>...] --out-root /tmp/stage2_rerun --copy-back
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STAGE2 = REPO / 'tools' / 'report_constraints_v2'
CHUNK = 5


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goldset-root', type=Path, required=True)
    parser.add_argument('--flatten-root', type=Path, required=True)
    parser.add_argument('--cases', required=True,
                        help='comma-separated case ids')
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--copy-back', action='store_true',
                        help='copy successful runs into goldset runs_XX dirs')
    parser.add_argument('--resume', action='store_true',
                        help='forward --resume so completed cases are skipped')
    parser.add_argument('--claim-verdict', choices=('legacy', 'signals'),
                        default='signals')
    parser.add_argument('--prompt-version', default='semantic-v3.16',
                        help='frozen stage-2 prompt version to forward to batch')
    parser.add_argument('--continue-on-review', action='store_true',
                        help='转发 --continue-on-review：fidelity needs_review 的 claim 也保留')
    args = parser.parse_args(argv)

    goldset = Path(args.goldset_root).resolve()
    flatten = Path(args.flatten_root).resolve()
    out_root = Path(args.out_root).resolve()
    ids = [x.strip() for x in args.cases.split(',') if x.strip()]

    for cid in ids:
        if not (flatten / cid / 'report.json').is_file():
            raise SystemExit(f'report not found: {cid}')
    out_root.mkdir(parents=True, exist_ok=True)

    for idx, chunk in enumerate(chunked(ids, CHUNK), 1):
        manifest = {
            'data_root': str(flatten),
            'cases': [{'id': cid, 'case_directory': cid} for cid in chunk],
        }
        manifest_path = out_root / f'manifest_{idx:02d}.json'
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        batch_out = out_root / f'batch_{idx:02d}'
        cmd = [sys.executable, str(REPO / 'main.py'), 'batch',
               '--manifest', str(manifest_path),
               '--output', str(batch_out),
               '--allow-report-upload',
               '--provider', 'deepseek', '--model', 'deepseek-flash',
               '--claim-verdict', args.claim_verdict,
               '--prompt-version', args.prompt_version]
        if args.resume:
            cmd.append('--resume')
        if args.continue_on_review:
            cmd.append('--continue-on-review')
        print('RUN', ' '.join(cmd), flush=True)
        proc = subprocess.run(cmd, cwd=str(REPO))
        if proc.returncode != 0:
            print(f'batch {idx} exited {proc.returncode}', flush=True)
            continue
        if args.copy_back:
            next_run = max(
                [int(p.name.rsplit('_', 1)[1]) for p in goldset.glob('runs_*')
                 if p.name.rsplit('_', 1)[1].isdigit()] or [0]) + 1
            new_run_dst = goldset / f'runs_{next_run:02d}'
            new_run_dst.mkdir(parents=True, exist_ok=True)
            copied = []
            for case_dir in batch_out.iterdir():
                if not (case_dir / 'stage3-spec.json').is_file():
                    continue
                existing = None
                for run_dir in sorted(goldset.glob('runs_*')):
                    if (run_dir / case_dir.name).is_dir():
                        existing = run_dir / case_dir.name
                        break
                if existing is not None:
                    shutil.rmtree(existing)
                    dst = existing
                else:
                    dst = new_run_dst / case_dir.name
                shutil.copytree(case_dir, dst)
                copied.append(case_dir.name)
            print(f'copied {len(copied)} cases in batch {idx}', flush=True)
    print('done')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
