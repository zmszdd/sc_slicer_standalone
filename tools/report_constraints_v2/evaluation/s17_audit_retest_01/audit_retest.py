#!/usr/bin/env python3
"""S17 audit attribution retest against the saved blind-batch_06 run.

Blind batch 06 produced the first confirmed unfaithful plan (GTE
feLafF5S5sM: "a launchpad fee is accrued but not distributed" encoded as
``undistributed_fee == 0`` -- a fact inversion no deterministic gate can
see).  S17 added the semantic cross-audit AFTER that batch, so the saved
plan was never audited.  This probe feeds the real saved plan (not a
reconstruction) through the production audit path and records whether the
auditor judges the inverted predicate ``inverted``.

Zero production code is changed; every function is reused from the live
pipeline (``faithfulness_audit_input`` / ``request_faithfulness_audit``),
so the probe exercises exactly the code a new run would.  ``--dry-run``
builds the payload and the record skeleton with zero model calls.

The saved run lives under /tmp and is ephemeral: both input files are
hashed into the probe record so the attribution stays verifiable after
the artifacts are gone.

Authorization: a live invocation sends the cited report statement texts
to the chosen provider (1 call, at most 1 format retry).  Run it only
with explicit user authorization.
"""

import argparse
import functools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))

from cli.semantic_pipeline import (faithfulness_audit_input,  # noqa: E402
                                   request_faithfulness_audit)
from lib.deepseek import (DEEPSEEK_MODELS, DEFAULT_DEEPSEEK_MODEL,  # noqa: E402
                          extract_deepseek)
from lib.plan_synthesizer import faithfulness_mismatches  # noqa: E402
from lib import report_only as r  # noqa: E402

#: The real blind-batch_06 rejected run (pre-S17, never audited).
DEFAULT_RUN = Path('/tmp/blind_batch_06/runs/'
                   'GTE_Perps_and_Launchpad_gtn2Umg6KsC__f9M82Pw5RX4__feLafF5S5sM')

PROBE_RECORD = 'S17_AUDIT_RETEST_PROBE.json'

LIMITATIONS = (
    'Real saved batch-06 artifacts, not a reconstruction (see input sha256s). '
    'The auditor is the same model family as the pipeline (self-preference '
    'limitation stands); n=1 retest; the verdict tests the audit channel on '
    'one documented defect, not general accuracy.',
)

EXPECTATION = ('p_fee_accrued_not_distributed should be judged "inverted": the '
               'statement says the fee exists (accrued, not distributed) while '
               'the predicate encodes undistributed_fee == 0 (blind-batch_06 '
               'GTE feLafF5S5sM).')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, required=True,
                        help='new probe directory (refuses to overwrite)')
    parser.add_argument('--run-dir', type=Path, default=DEFAULT_RUN,
                        help='saved run holding elements-ids.json + formal-plan.json')
    parser.add_argument('--provider', choices=('deepseek', 'opencode'),
                        default='deepseek', help='audit transport')
    parser.add_argument('--model', default=None,
                        help='audit model (default: deepseek-flash / llm.env MODEL_NAME)')
    parser.add_argument('--proxy', default='direct',
                        help='deepseek proxy policy: environment | direct | http(s):// URL')
    parser.add_argument('--dry-run', action='store_true',
                        help='build payload + record skeleton, zero model calls')
    args = parser.parse_args()

    if args.output.exists():
        raise SystemExit(f'refusing to overwrite existing {args.output}')
    for name in ('elements-ids.json', 'formal-plan.json'):
        if not (args.run_dir / name).is_file():
            raise SystemExit(f'missing {name} under {args.run_dir} '
                             '(the /tmp batch artifacts may be gone; '
                             'see STAGE2_CURRENT_STATUS.md S17)')
    args.output.mkdir(parents=True)

    elements = json.loads((args.run_dir / 'elements-ids.json').read_text())
    plan = json.loads((args.run_dir / 'formal-plan.json').read_text())
    payload = faithfulness_audit_input(elements, plan)
    (args.output / 'audit-input.json').write_text(payload)

    model = args.model or (DEFAULT_DEEPSEEK_MODEL if args.provider == 'deepseek'
                           else None)
    if args.provider == 'deepseek':
        if model not in DEEPSEEK_MODELS:
            raise SystemExit(f'{model!r} is not in the deepseek whitelist '
                             f'{sorted(DEEPSEEK_MODELS)}')
        extract_fn = functools.partial(extract_deepseek, proxy=args.proxy)
    else:
        if not model:
            raise SystemExit('opencode transport needs --model '
                             '(config/llm.env MODEL_NAME is not auto-read here)')
        extract_fn = r.extract

    record = {
        'schema_version': 'stage2-s17-audit-retest/1',
        'case': args.run_dir.name,
        'run_dir': str(args.run_dir),
        'elements_sha256': r.sha((args.run_dir / 'elements-ids.json').read_bytes()),
        'plan_sha256': r.sha((args.run_dir / 'formal-plan.json').read_bytes()),
        'provider': args.provider,
        'model': model,
        'expectation': EXPECTATION,
        'dry_run': args.dry_run,
        'limitations': LIMITATIONS,
    }

    if args.dry_run:
        (args.output / PROBE_RECORD).write_text(json.dumps(record, indent=1) + '\n')
        print(json.dumps({'dry_run': True, 'output': str(args.output),
                          'payload_bytes': len(payload),
                          'p_sources': [term['source_id']
                                        for term in plan['precondition_terms']]}))
        return 0

    verdict = request_faithfulness_audit(payload, model, args.output, plan,
                                         extract_fn)
    attempts = json.loads((args.output / 'faithfulness-audit-attempts.json')
                          .read_text())
    mismatches = faithfulness_mismatches(verdict)
    record.update({
        'checks': verdict['checks'],
        'mismatches': mismatches,
        'attempts': attempts,
        'expectation_met': any(check['source_id'] == 'p_fee_accrued_not_distributed'
                               and check['verdict'] == 'inverted'
                               for check in verdict['checks']),
    })
    (args.output / PROBE_RECORD).write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps({'expectation_met': record['expectation_met'],
                      'mismatch_count': len(mismatches),
                      'output': str(args.output)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
