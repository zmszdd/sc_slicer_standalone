# 样本独立性与规模（项目聚类稳健统计）

自动召回 75.8%（TP=119/157，案例级）
- naive Wilson 95%CI = 68.5%–81.8%
- 设计效应 DEFF=1.28，ICC=0.04，平均簇大小=7.85
- 有效样本量 n_eff=122（157 个相关案例）
- 聚类稳健 Wilson 95%CI = 67.5%–82.5%
- cluster bootstrap 95%CI = 67.4%–83.5%

**主口径：项目级召回（独立单位）=100.0%**（20/20 项目）
- Wilson 95%CI = 83.9%–100.0%
- cluster bootstrap 95%CI = 100.0%–100.0%

判例锚定准确率 88.8%（TP=119, FP=15）
- Wilson 95%CI = 82.3%–93.1%
- cluster bootstrap 95%CI = 77.1%–97.4%

负样本集中度：FP=15，跨 3 个项目；最大项目占比 80%
  {'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2, 'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1, 'SukukFi_syLyTBz5KNA': 12}

## 独立样本口径（finding 级）

- 召回(finding级)=81.4%（TP=70/86，95%CI 71.9%–88.2%）
- 准确率(finding级)=92.1%（TP=70 FP=6，95%CI 83.8%–96.3%）
- FP 由 15 条 impact claim 合并为 6 个独立 finding，项目分布 {'SukukFi_syLyTBz5KNA': 3, 'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2, 'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1}

## 根因家族口径（负样本）

- 准确率(根因家族级)=92.1%（TP_finding=70 FP_family=6，95%CI 83.8%–96.3%）
- FP 根因家族数=6，最大项目占比 33%
- 家族明细：GTE_Perps_and_Launchpad_gtn2Umg6KsC__ajDovMJcy4Z, GTE_Perps_and_Launchpad_gtn2Umg6KsC__xK7NZycdpFR, GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__EXx2KHrPZfx, SukukFi_syLyTBz5KNA__7gXLhGcETg4, SukukFi_syLyTBz5KNA__A78JaZeDQAg, SukukFi_unregisterVault_dust_dos

| 项目 | 案例数 | TP | 项目内召回 |
| --- | ---: | ---: | ---: |
| Forte | 6 | 6 | 100% |
| Panoptic_Hypovault_c9MhophgwGP | 7 | 7 | 100% |
| Upside_xKJfM48g3oD | 2 | 2 | 100% |
| Blackhole_GUT9Y3UVuWn | 1 | 1 | 100% |
| Hybra_Finance_xo4hapwL2Jy | 10 | 9 | 90% |
| Sequence | 10 | 9 | 90% |
| Covenant_d4uY8y2AMSs | 7 | 6 | 86% |
| Monetrix_L3gNZDymiju | 7 | 6 | 86% |
| Brix_Money_qy7NXr77sDh | 7 | 6 | 86% |
| Panoptic | 13 | 11 | 85% |
| Morpheus_kdPtwopH6ws | 5 | 4 | 80% |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 9 | 7 | 78% |
| Olas_j3PRAMM3fVq | 9 | 7 | 78% |
| Kinetiq_k8aVPPVguSE | 8 | 6 | 75% |
| Merkl_T4ExvutBBXC | 8 | 6 | 75% |
| SukukFi_syLyTBz5KNA | 12 | 8 | 67% |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 13 | 8 | 62% |
| Virtuals_Protocol_hzMS6ZZkBTg | 4 | 2 | 50% |
| Ekubo_3FTodhsvBkM | 7 | 3 | 43% |
| Intuition_2VUsxVJwReb | 12 | 5 | 42% |
