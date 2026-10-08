# Prompt 单文件（semantic-live）政策

日期：2026-10-05。本文件记录 Prompt 管理从"多冻结版本"切换到"单一活文件 + 运行目录
重放"的原因与契约。历史背景（v3.5–v3.20 的 16 个冻结版本如何派生）见
`STAGE2_CURRENT_STATUS.md` 与 `prompts/versions/`。

## 为什么切换

- v3.18/v3.19/v3.20 都是 prompt-only 的窄修复，且为保持 schema `report-formal-plan/4`
  与字节级重放不破坏，只能以 `.replace()` 链式打补丁。阅读和编辑都要沿链解析，
  版本数持续膨胀。
- 语义评测已经证明：**要素层 P（时间角色）与形式化层 I（适用条件）是真实瓶颈**
  （见 `../evaluation/prompt_v320_blind_03/REPORT.md`）。修复它们需要高频迭代提示词，
  冻结版本模式与这种迭代不匹配。

## 政策

1. **唯一可编辑的 Prompt 文件是 `prompts/current.py`**（版本名 `semantic-live`）。
   初始文本逐字节等于 `semantic-v3.20` 的解析结果；此后原地修改，不再新建版本文件。
2. **`prompts/versions/` 转为只读存档**。历史 run 的 provenance 仍引用旧版本名，
   registry 保留 `module_for('semantic-v3.x')` 解析能力，但任何新改动都不进 `versions/`。
   `registry.VERSIONS` 恒为 16 个冻结版本；`semantic-live` 只出现在
   `SELECTABLE_VERSIONS`（CLI 可选项）。
3. **功能开关与版本名解耦**。live 的流水线特性在 `current.FEATURES` 显式声明，
   读取一律经 `registry.feature_enabled(version, feature)` / `features_for(version)`。
   冻结版本的功能集合不变（legacy `*_VERSIONS` 原样保留导出）。
   创建时已核实 live 与 v3.16/v3.20 的 14 项 feature 完全一致，因此把默认版本从
   v3.16 换成 live 只改 prompt 文本、不改任何功能门行为。
4. **P/I/V 契约检查对 live 生效**：`prompts/active.py` 的 `_assert_piv_contract`
   覆盖 `semantic-live`。原地改丢 P/I/V 语义分界标记会在解析时直接报错。

## 重放契约（verify 如何对待 prompt）

- 每次 neural 运行在 run 目录落盘两份**纯 prompt 快照**：`prompt-element.txt`、
  `prompt-formal.txt`（不含 payload、不含重试 feedback），并把
  `element_prompt_sha256` / `formal_prompt_sha256` / `prompt_features`（功能开关
  决策）/ `requested_evidence_mode` 写进 provenance。
- `cli/batch_verify.py` 的 `verify()` 优先用快照做哈希比对（`checks_performed` 记为
  `prompt_snapshots`），并交叉校验首 attempt 的 `neural-elements/prompt.txt`
  以快照开头（证明快照就是发给模型的文本）。**这条路径完全不读 `current.py` 的
  当前内容。**
- 旧 run（无快照，均为冻结版本）回落 registry 解析（`resolved_prompt_hashes`）。
  冻结版本文本时间不变，重放安全。
- **旧 live run 删掉快照 = 放弃该 run 的重放能力**：回落会解析到当前 `current.py`
  文本，与 provenance 哈希不一致时 verify 诚实失败。这是有意行为。
- 功能开关同理：回放一律读 provenance 里的 `prompt_features`；无此键的旧 run
  （均为冻结版本）按版本名从冻结矩阵合成，同样时间不变。

## 不随之改变的规则

- `prompts/versions/` 16 个文件字节不动；`evaluation/` 冻结脚本照旧可用。
- `lib/salvage.py` 的 `--prompt-version` 仍硬编码 v3.12–v3.17 选择（遗留重放工具，
  不支持 live，不做修改）。
- 每个新 run 仍必须写到新的唯一输出目录；禁止覆盖历史实验目录。

## 验证与守护测试

- `tests/test_prompt_live.py`：live 的 P/I/V 标记、fixed-template mandate 措辞、
  FEATURES 与 `FEATURE_NAMES` 一致、live≡v3.16 的 feature 基线锁定、
  VERSIONS 冻结性。
- `tests/test_prompt_snapshot.py`：快照存在且哈希一致、`prompt_features` 落盘、
  篡改快照被拒、**原地改 `current.py` 后旧 live run 仍 verify 通过（解耦证明）**、
  删快照后失败（快照是唯一依据）、冻结 run 走 registry 回落路径回归。
- 初始生成等价 gate（一次性，不进测试）：
  `current.ID_ELEMENT_PROMPT == resolve_prompt_set('semantic-v3.20').element_prompt`。

## 迭代纪律与终局保留批（2026-10-06 起）

盲测-归因-修复循环是自适应数据分析：批次对 prompt 盲，但修复者对批次结果不盲，
无限迭代必然过拟。对策不是停止迭代，而是**让最后一次测量不被迭代污染**：

- **终局保留批** `evaluation/final_holdout_01/`（10 例，冻结于 live-3 之前的
  2026-10-06）：永不进迭代、迭代期间不做任何语义查看，循环停止后用当时的
  live prompt 跑一次（两个 5 例 manifest），n=10，是唯一无偏测量。未来所有
  迭代批的 select.py 经 SELECTION.json 扫描自动排除这 10 例。
- **停止规则**：最多再迭代 2 轮（live-3、live-4）；任一轮相对上一盲批无实测
  改善即提前停。
- **规则吝啬门槛**：新增 prompt 规则须有 ≥2 个独立失败案例支撑；单例驱动的
  修正降级为修复反馈，不进 prompt 文本。
- **终局报告披露迭代轮数**（"经 N 轮自适应迭代后测得"），不与历史批次混比。
- **第二终局保留批** `evaluation/final_holdout_02/`（10 例，冻结于 2026-10-08，
  semantic-live-5 结构性修改任何盲测之前）：与 final_holdout_01 同一机械纪律
  （三重排除、冻结后不做任何语义查看、只跑一次），测的是收口后按任务目标
  补充的结构性修改（重复谓词门 + 部分形式化通道的行为，两个 advisory 的
  覆盖面收集）。判据预注册于其 README，跑之前写死。
- **semantic-live-6**（2026-10-08 深夜，final_holdout_02 终测之后、用户批准
  的缺陷侧收口）：三项机械层/反馈层修复（数值门反馈点名缺失来源、空响应
  免费重问一次、示例钉死 advisory）+ 阶段三冒烟发现的查询命名归一化。
  prompt 语义文本未改，但行为已变（重试反馈内容、修复通道预算、新
  advisory 落盘）——**final_holdout_02 的 9/10 不再代表当前代码**。投产
  测量须冻结 `final_holdout_03`（三重排除自动覆盖全部 147 例历史样本），
  判据照本文件预注册纪律先写死再跑。改动明细见
  [STAGE2_CURRENT_STATUS.md](STAGE2_CURRENT_STATUS.md)。

## 修改 live prompt 的流程

1. 直接编辑 `prompts/current.py`（如需翻转功能门，同步改 `FEATURES`）；
2. `python main.py preview-prompt --part element|formal` 检查解析文本；
3. 跑 `python main.py test`；
4. 用小样本真实运行（新输出目录），verify 通过后再上批量；
5. 语义效果评测照 `evaluation/GENERALIZATION_PROTOCOL.md` 的流程走，不用调分
   样本重测。
