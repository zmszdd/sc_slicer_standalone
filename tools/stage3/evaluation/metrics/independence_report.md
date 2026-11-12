# 样本独立性与规模（项目聚类稳健统计）

自动召回 58.4%（TP=59/101，案例级）
- naive Wilson 95%CI = 48.7%–67.5%
- 设计效应 DEFF=1.84，ICC=0.21，平均簇大小=5.05
- 有效样本量 n_eff=55（101 个相关案例）
- 聚类稳健 Wilson 95%CI = 45.2%–70.5%
- cluster bootstrap 95%CI = 44.9%–71.3%

**主口径：项目级召回（独立单位）=90.0%**（18/20 项目）
- Wilson 95%CI = 69.9%–97.2%
- cluster bootstrap 95%CI = 75.0%–100.0%

判例锚定准确率 79.7%（TP=59, FP=15）
- Wilson 95%CI = 69.2%–87.3%
- cluster bootstrap 95%CI = 62.5%–95.0%

负样本集中度：FP=15，跨 3 个项目；最大项目占比 80%
  {'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2, 'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1, 'SukukFi_syLyTBz5KNA': 12}

## 独立样本口径（finding 级）

- 召回(finding级)=61.2%（TP=41/67，95%CI 49.2%–72.0%）
- 准确率(finding级)=87.2%（TP=41 FP=6，95%CI 74.8%–94.0%）
- FP 由 15 条 impact claim 合并为 6 个独立 finding，项目分布 {'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1, 'SukukFi_syLyTBz5KNA': 3, 'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2}

## 根因家族口径（负样本）

- 准确率(根因家族级)=87.2%（TP_finding=41 FP_family=6，95%CI 74.8%–94.0%）
- FP 根因家族数=6，最大项目占比 33%
- 家族明细：GTE_Perps_and_Launchpad_gtn2Umg6KsC__ajDovMJcy4Z, GTE_Perps_and_Launchpad_gtn2Umg6KsC__xK7NZycdpFR, GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__EXx2KHrPZfx, SukukFi_syLyTBz5KNA__7gXLhGcETg4, SukukFi_syLyTBz5KNA__A78JaZeDQAg, SukukFi_unregisterVault_dust_dos

| 项目 | 案例数 | TP | 项目内召回 |
| --- | ---: | ---: | ---: |
| Panoptic_Hypovault_c9MhophgwGP | 6 | 6 | 100% |
| Sequence | 6 | 6 | 100% |
| SukukFi_syLyTBz5KNA | 3 | 3 | 100% |
| Upside_xKJfM48g3oD | 2 | 2 | 100% |
| Merkl_T4ExvutBBXC | 6 | 5 | 83% |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 5 | 4 | 80% |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 5 | 4 | 80% |
| Covenant_d4uY8y2AMSs | 6 | 4 | 67% |
| Forte | 6 | 4 | 67% |
| Brix_Money_qy7NXr77sDh | 6 | 4 | 67% |
| Olas_j3PRAMM3fVq | 5 | 3 | 60% |
| Kinetiq_k8aVPPVguSE | 6 | 3 | 50% |
| Monetrix_L3gNZDymiju | 6 | 3 | 50% |
| Morpheus_kdPtwopH6ws | 5 | 2 | 40% |
| Ekubo_3FTodhsvBkM | 6 | 2 | 33% |
| Panoptic | 6 | 2 | 33% |
| Virtuals_Protocol_hzMS6ZZkBTg | 4 | 1 | 25% |
| Intuition_2VUsxVJwReb | 5 | 1 | 20% |
| Hybra_Finance_xo4hapwL2Jy | 6 | 0 | 0% |
| Blackhole_GUT9Y3UVuWn | 1 | 0 | 0% |
