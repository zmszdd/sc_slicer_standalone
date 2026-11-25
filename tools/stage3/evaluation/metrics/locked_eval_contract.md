# Locked evaluation contract

- protocol: `mainline/1.7.36` / `0bd0e65e2f60`
- ready: **true**
- publishable: **false**
- publication status: `coverage-limited`

- primary publishable: **false**
- primary publication status: `coverage-limited`

| item | value | floor | recommended |
| --- | ---: | ---: | ---: |
| positives | 40 | 30 | 40 |
| negatives | 40 | 8 | 40 |
| projects | 16 | 5 | - |

| negative sampling | value | floor | cap |
| --- | ---: | ---: | ---: |
| negative projects | 10 | 5 | - |
| max project share | 17.50% | - | 25% |
| negative target shortfall | 0 | - | - |

| negative source slices | 35 | 8 | - |

| gate | value |
| --- | --- |
| `refresh_ready` | true |
| `refresh_allowed` | true |
| `eligible_current` | 46 |

| coverage | value | floor |
| --- | ---: | ---: |
| eligible positives | 35 | 30 |
| eligible negatives | 11 | 24 |
| positive | 35/40 = 87.5% | 80% |
| negative | 11/40 = 27.5% | 60% |

| publication quality | value | cap |
| --- | ---: | ---: |
| negative FPR upper95 | 23.8% | 12% |
| label review | label_review_required | - |

## Blockers

- eligible negatives below publication floor: 11 < 24 (FPR upper95 23.8% > 12%)
- label review required for 2 negative case(s): GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC, Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3
