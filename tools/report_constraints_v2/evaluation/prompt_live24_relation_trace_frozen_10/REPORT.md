# semantic-live-24 frozen-source relationship-trace retest

## Method

- Reused the exact 52 `(Impact, I source, P source set)` pairs from `prompt_live21_frozen_sources_paired`; source IDs were not reselected.
- Compared against the preceding live-23 run on those same pairs. The model (`deepseek-flash`) and the single post-generation audit remained the same.
- live-24 adds a generator-proposed `relationship_trace`: alongside the formal plan, the model returns an audit-only object citing a path through the supplied `relation_context` (frozen P/I/V IDs plus a cited action/root-cause statement and its evidence IDs). The trace is removed before synthesis and never becomes a rule condition or a new source. The audit independently verifies every cited ID and treats the trace as an unverified pointer; an unsupported trace cannot improve a verdict, and a missing trace cannot erase excerpts that are present. The element prompt also now asks extraction to preserve a complete causal or temporal bridge inside action/root_cause statements with all supporting fragments cited.
- The run made 117 model calls. Eleven of the 52 source pairs produced no rule.

## Results

| Outcome | live-23 | live-24 |
|---|---:|---:|
| Frozen source pairs | 52 | 52 |
| Rules generated | 46 | 41 |
| Passed | 36 | 37 |
| Needs review | 9 | 4 |
| Failed | 0* | 0 |
| No rule generated | 6 | 11 |
| Audit unavailable | 0 | 0 |
| Model calls | 122 | 117 |

\* live-23 recorded 1 failed pair; it appears here as 0 because that pair moved to
no-rule in live-24 (see transitions below).

Among the 41 generated rules, 37 passed (90.2%, up from 36/46 = 78.3%) and 4 were
needs-review. All 41 audits completed; the 37 passed rules had `piv_relation`
consistent and all per-source checks consistent, and the 4 needs-review rules had
weakened relations with faithful individual predicates. The overall pass rate rose
from 36/52 (69.2%) to 37/52 (71.2%), but the **generation rate fell from 46/52
(88.5%) to 41/52 (78.8%)** — under the pre-registered guard that a faithfulness
gain must not come from dropping complete rules, this is a mixed result, not a
clean improvement.

Paired end-state transitions live-23 → live-24: 32 pass→pass, 4
needs-review→pass, 1 no-rule→pass, 2 needs-review→needs-review, 1
pass→needs-review, 1 no-rule→needs-review, 3 pass→no-rule, 3
needs-review→no-rule, 1 failed→no-rule, 4 no-rule→no-rule.

### No-rule failure families (11 pairs)

| Family | Count | Cases |
|---|---:|---|
| Malformed JSON (`Extra data` after the object) | 4 | Hybra 1, Monetrix 2, Panoptic lockmode 1 |
| Type/unit mismatch `eq shares underlying_assets` | 3 | Panoptic Hypovault 3 |
| `lt` on bool/None operands | 2 | Monetrix 2 |
| Local repair changed plan schema | 1 | Panoptic Hypovault 1 |
| Invalid truth binding | 1 | Panoptic Hypovault 1 |

The Panoptic Hypovault construction failures (5 pairs) are the same family as
live-23's (shares vs underlying-assets comparability plus schema/truth binding);
they did not regress — they are a persistent DSL-discipline rejection family
that relation context does not address. The regression is concentrated in the
**4 JSON-format failures and 2 bool-comparison failures at Monetrix/Hybra/Panoptic
lockmode**, which were absent from live-23's no-rule set.

The JSON failures were then confirmed by inspecting the saved raw responses
(zero model calls): all four are byte-for-byte the same malformed shape — the
model writes the flat `report-formal-plan/8` object, closes it, and then
continues `,"relationship_trace":{...}}` outside the brace, a hybrid of the
legacy flat form and live-24's two-key requirement. A deterministic,
content-gated repair now exists (`lib/salvage.py::
merge_appended_relationship_trace`, wired into `request_formalization` and the
`verify` replay with a `response-normalization.json` record; the raw response
is never rewritten). Applying it offline to all four saved responses recovers
a parseable flat plan plus trace for each. This repair was implemented
**after** the paired run above, so this run's numbers do not include it; its
effect needs the next paired retest to measure. The 2 bool-comparison failures
at Monetrix are a separate, unattributed generation defect.

## Targeted cases

- **Panoptic Hypovault:** unchanged at 7/12 pairs generated, 7 passed, 5
  construction failures (same families as live-23). The relation-trace change
  neither helped nor hurt this case; its bottleneck is rule construction, not
  relation evidence.
- **Monetrix:** 4/8 pairs generated (live-23: 8/8 generated, 2 passed). The 4
  generated pairs all passed this round (live-23: 2 passed, 6 needs-review), and
  the explicit registration-to-accounting links that the audit previously judged
  unsupported are now represented and accepted for those pairs. But 4 pairs now
  die before the audit on two JSON-format and two bool-comparison errors. Net:
  clearer relations on what is generated, worse generation stability.
- **Merkl:** 1/2 passed; the timestamp+seconds type failure from live-23 did not
  recur, but one pair remains needs-review (weakened relation).

## Reading the result

The relationship trace moved the audit in the intended direction — among
generated rules, needs-review dropped from 9 to 4 and the sole failed pair is
resolved — without relaxing the pass standard or touching frozen sources.
However, the pre-registered guard fails: the generation rate fell from 88.5% to
78.8%, and the new no-rule families (JSON format, bool comparison) are
concentrated exactly where the two-key output requirement landed. The
attribution was confirmed by inspecting the saved raw responses (zero model
calls), and the chosen fix is mechanical tolerance of the appended-object form
(`merge_appended_relationship_trace`, the same normalization-contract approach
the element layer already uses) rather than more prompt instructions. The next
paired retest should measure whether it recovers the generation rate while
holding the 90.2% faithfulness figure.

The audit is model-based and same-family (deepseek-flash); these figures measure
this pipeline's internal audit outcomes, not externally established semantic
accuracy. The 52 frozen pairs have now been reused across live-19 through
live-24 comparisons and are a development set; any final claim needs a fresh
frozen blind batch.
