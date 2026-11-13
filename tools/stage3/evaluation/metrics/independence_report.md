# 样本独立性与规模（项目聚类稳健统计）

自动召回 65.3%（TP=66/101，案例级）
- naive Wilson 95%CI = 55.7%–73.9%
- 设计效应 DEFF=2.01，ICC=0.25，平均簇大小=5.05
- 有效样本量 n_eff=50（101 个相关案例）
- 聚类稳健 Wilson 95%CI = 51.5%–77.0%
- cluster bootstrap 95%CI = 51.5%–77.5%

**主口径：项目级召回（独立单位）=90.0%**（18/20 项目）
- Wilson 95%CI = 69.9%–97.2%
- cluster bootstrap 95%CI = 75.0%–100.0%

判例锚定准确率 81.5%（TP=66, FP=15）
- Wilson 95%CI = 71.7%–88.4%
- cluster bootstrap 95%CI = 65.0%–95.5%

负样本集中度：FP=15，跨 3 个项目；最大项目占比 80%
  {'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2, 'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1, 'SukukFi_syLyTBz5KNA': 12}

## 独立样本口径（finding 级）

- 召回(finding级)=67.2%（TP=45/67，95%CI 55.3%–77.2%）
- 准确率(finding级)=88.2%（TP=45 FP=6，95%CI 76.6%–94.5%）
- FP 由 15 条 impact claim 合并为 6 个独立 finding，项目分布 {'SukukFi_syLyTBz5KNA': 3, 'GTE_Perps_and_Launchpad_gtn2Umg6KsC': 2, 'GTE_Spot_CLOB_and_Router_qa8y3zjgyCn': 1}

## 根因家族口径（负样本）

- 准确率(根因家族级)=88.2%（TP_finding=45 FP_family=6，95%CI 76.6%–94.5%）
- FP 根因家族数=6，最大项目占比 33%
- 家族明细：GTE_Perps_and_Launchpad_gtn2Umg6KsC__ajDovMJcy4Z, GTE_Perps_and_Launchpad_gtn2Umg6KsC__xK7NZycdpFR, GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__EXx2KHrPZfx, SukukFi_syLyTBz5KNA__7gXLhGcETg4, SukukFi_syLyTBz5KNA__A78JaZeDQAg, SukukFi_unregisterVault_dust_dos

| 项目 | 案例数 | TP | 项目内召回 |
| --- | ---: | ---: | ---: |
| Panoptic_Hypovault_c9MhophgwGP | 6 | 6 | 100% |
| Sequence | 6 | 6 | 100% |
| SukukFi_syLyTBz5KNA | 3 | 3 | 100% |
| Upside_xKJfM48g3oD | 2 | 2 | 100% |
| Forte | 6 | 5 | 83% |
| Merkl_T4ExvutBBXC | 6 | 5 | 83% |
| Monetrix_L3gNZDymiju | 6 | 5 | 83% |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 5 | 4 | 80% |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 5 | 4 | 80% |
| Morpheus_kdPtwopH6ws | 5 | 4 | 80% |
| Olas_j3PRAMM3fVq | 5 | 4 | 80% |
| Covenant_d4uY8y2AMSs | 6 | 4 | 67% |
| Brix_Money_qy7NXr77sDh | 6 | 4 | 67% |
| Kinetiq_k8aVPPVguSE | 6 | 3 | 50% |
| Panoptic | 6 | 3 | 50% |
| Ekubo_3FTodhsvBkM | 6 | 2 | 33% |
| Virtuals_Protocol_hzMS6ZZkBTg | 4 | 1 | 25% |
| Intuition_2VUsxVJwReb | 5 | 1 | 20% |
| Hybra_Finance_xo4hapwL2Jy | 6 | 0 | 0% |
| Blackhole_GUT9Y3UVuWn | 1 | 0 | 0% |
