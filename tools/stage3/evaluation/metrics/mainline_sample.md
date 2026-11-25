# 主口径分层抽样

- 来源：`judge_ground_truth.json` 全量判例，seed `20261115`。
- 策略：20 个项目分层，项目内按 severity 比例分配；总 positive 目标 `350`。
- 抽样总体已排除冻结 dev252/dev24 与开发负例，共 `334` 例，保证 dev/eval 不相交。
- negative 来源：`official_negative_pool_20261121.json`，标签规则 `latest validity evaluation for the same finding uid`。
- negative 总体：排除 dev/GT 后的 `165` 例。

| 项目 | 总体 | 抽中 | severity 分布 |
| --- | ---: | ---: | --- |
| Brix_Money_qy7NXr77sDh | 10 | 4 | low=9, medium=1 |
| Covenant_d4uY8y2AMSs | 16 | 5 | low=16 |
| Ekubo_3FTodhsvBkM | 16 | 5 | low=14, medium=2 |
| Forte | 13 | 4 | high=12, low=1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 190 | 54 | high=140, medium=50 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 93 | 27 | high=19, low=23, medium=51 |
| Hybra_Finance_xo4hapwL2Jy | 163 | 46 | high=22, low=99, medium=42 |
| Intuition_2VUsxVJwReb | 112 | 32 | low=59, medium=53 |
| Kinetiq_k8aVPPVguSE | 13 | 4 | high=6, low=2, medium=3, unknown=2 |
| Merkl_T4ExvutBBXC | 56 | 16 | low=43, medium=13 |
| Monetrix_L3gNZDymiju | 56 | 16 | low=38, medium=18 |
| Morpheus_kdPtwopH6ws | 2 | 1 | low=2 |
| Olas_j3PRAMM3fVq | 66 | 19 | high=57, low=9 |
| Panoptic | 140 | 40 | high=53, low=34, medium=53 |
| Panoptic_Hypovault_c9MhophgwGP | 53 | 16 | high=6, low=47 |
| Sequence | 53 | 15 | low=53 |
| SukukFi_syLyTBz5KNA | 160 | 45 | high=95, low=58, medium=7 |
| Virtuals_Protocol_hzMS6ZZkBTg | 1 | 1 | high=1 |

## 负样本

- 目标 `60`，可选总体 `60`，实际选中 `60`，缺口 `0`。
- 按项目分层，单项目上限 `25%`。

- 运行就绪：报告 `60`，源码切片 `2`。

| 项目 | 总体 | 抽中 |
| --- | ---: | ---: |
| Blackhole_GUT9Y3UVuWn | 6 | 6 |
| Ekubo_3FTodhsvBkM | 1 | 1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 6 | 6 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 5 | 5 |
| Kinetiq_k8aVPPVguSE | 10 | 10 |
| Olas_j3PRAMM3fVq | 10 | 10 |
| Panoptic_Next_Core_iqcUwAhCZyD | 5 | 5 |
| SukukFi_syLyTBz5KNA | 10 | 10 |
| Upside_xKJfM48g3oD | 5 | 5 |
| Virtuals_Protocol_hzMS6ZZkBTg | 2 | 2 |

共选中 positive `350`，negative `60`。
