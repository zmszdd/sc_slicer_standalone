# live16 manual Impact and qualifier review

Checked against the frozen `extraction-input.txt` and `impact-inventory.json` files. Impact candidates must come only from the explicitly marked Impact area.

## Inventory omissions

- Covenant explicitly lists “Accelerates market collapse instead of preventing it”. The live16 inventory placed it in `ambiguities` as an omitted outcome. The inventory had a four-item cap; this report contains at least five distinct bullets.
- Hybra explicitly states that DeFi integrations (pools, lending, vaults) cannot manually clean up or migrate to new addresses, enabling permanent griefing. The inventory omitted this outcome.
- Kinetiq explicitly says users can profit if the exchange rate decreases between withdrawal queueing and confirmation. The inventory omitted this conditional result.

## Qualifiers weakened in formalization

- GTE Spot reduced a broader market-interference outcome to one post-only order failure.
- Hybra dropped the repeated re-deposit-before-expiry condition that keeps the DoS permanent and its approximate `$100/day` cost.
- Intuition omitted ERC-7562 `STO-021` / `STO-022` and the scope “every newly created atom”.
- Kinetiq weakened “the queued amount is greater than its value at confirmation” to a generic inequality, losing the direction.

These are frozen development findings and regression targets. They do not count as a gold set or as a model-independent score.
