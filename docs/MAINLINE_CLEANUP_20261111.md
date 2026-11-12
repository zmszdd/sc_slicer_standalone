# 主线清理记录（2026-11-11）

删除的冗余分支（均为 untracked 且未被 docs 引用）：

- `archives/_cleanup_20261103`
- `panoptic_multi__core_claim`
- `panoptic_builder_init.pipeline.json`
- `tools/report_constraints_v2/evaluation/live26_confirm30_blind_30`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_blind_30`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun10`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun11`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun12`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun13`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun14`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun15`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun16`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun17`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun18`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun19`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun2`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun20`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun21`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun22`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun23`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun24`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun25`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun26`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun27`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun28`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun29`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun3`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun30`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun31`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun4`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun5`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun6`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun7`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun8`
- `tools/report_constraints_v2/evaluation/live26_fix_confirm30_rerun9`
- `tools/report_constraints_v2/evaluation/live26_fix_retest`
- `tools/report_constraints_v2/evaluation/post_revert_deepseek_blind_10`
- `tools/report_constraints_v2/evaluation/post_vacuityfix_live5_v25`
- `tools/report_constraints_v2/evaluation/post_vacuityfix_live5_v26`
- `tools/report_constraints_v2/evaluation/post_vacuityfix_live_5`
- `tools/report_constraints_v2/evaluation/prompt_live24_confirm30_blind_30`
- `tools/report_constraints_v2/evaluation/prompt_live24_frozensymbolfix_blind_10`
- `tools/report_constraints_v2/evaluation/prompt_live24_jsonsuffix_blind_5`
- `tools/report_constraints_v2/evaluation/prompt_live24_prescreen_blind_30`
- `tools/report_constraints_v2/evaluation/prompt_live24_quantityfix_blind_10`
- `tools/report_constraints_v2/evaluation/prompt_live24_repairscope_blind_10`

保留：主线代码、`docs/`、`tools/report_constraints_v2/docs/` 中仍引用的 5 个评测目录、`goldset_*`、`tools/pipeline`、`manifests`、`pipeline_manifests`、`stage1_input`。
