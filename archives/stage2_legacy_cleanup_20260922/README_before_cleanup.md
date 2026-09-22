# 第二阶段：报告核心要素、不变量推导与形式化

工程导航：

- [统一入口 main.py](../../main.py)：唯一推荐入口，命令表见文件顶部
- [目录结构与文件职责](STRUCTURE.md)
- [路径迁移说明](MIGRATION.md)
- [Prompt 版本说明](prompts/README.md)
- [测试分类与运行方式](tests/README.md)
- [文档索引](docs/README.md)
- [评测目录索引](evaluation/README.md)
- [运行产物说明](results/README.md)
- [当前状态](docs/STAGE2_CURRENT_STATUS.md)

根目录只保留运行代码、入口配置和导航；Prompt、测试和报告分别位于 `prompts/`、`tests/`
和 `docs/`。新增文件请遵守 [迁移说明](MIGRATION.md)，不要再次把版本文件堆回根目录。

当前状态：阶段二从报告到 P/I/V、形式约束和 Z3 的工程链已跑通，但真实报告
提取准确率尚无可信数值，PoC 一致性仍未评估。可选的前提审查 v5、受约束修复、
数值与零地址保真守卫已在 Intuition/Hybra 开发案例中发现并减少具体错误；
修复结果仍路由 `review`，不能算已验证正确。输入策略 v3 修复了部分报告在 PoC/修复
建议之后的影响段落漏读；本地 v4 进一步排除无标题修复建议。新版离线重放器覆盖
后续计划版本。清理退役切片绑定分支后，当前 335 项主线本地回归通过。[八份新报告的首次测试](evaluation/fresh_holdout_01/REPORT.md)
已真实运行：4/8 提取要素，1/8 走到 Z3；唯一完整例仍需审查，语义准确率未知。
原批次 v3 曾误上传 Morpheus 的无标题修复建议，已停止进一步外部调用并本地修复。
后续开发版 v3.12 增加正常执行限定提示、首步受控重试及可选轻量第二步输入。Brix 在旧环境的复验曾超时；后来用户授权了指定案例的报告片段和派生 P/I/V 经 DeepSeek API 发送，并进行了真实小样本测试，但仍无可信语义准确率。见[开发复验](evaluation/recovery_v312_01/REPORT.md)、[最新进度与剩余问题](docs/STAGE2_CURRENT_STATUS.md)和[输入覆盖复验](evaluation/input_coverage_01/REPORT.md)。
最新 `semantic-v3.14` 增加复合谓词、报告明确乘积关系、定量事实保留及 I/V 极性检查。
[GTE/Hybra 开发复验](evaluation/prompt_v314_polarity_01/REPORT.md)中 GTE 已端到端完成且
方向正确；Hybra 的核心 I/V 已改善，但数值 P 仍被保真检查拒绝。该批为开发回归，不能
作为总体准确率。
本地实验版 `semantic-v3.15` 已新增 12 类[通用安全关系分类](docs/SAFETY_RELATION_TAXONOMY.md)、
关系义务/单调性/守恒模板和有单位的加减乘表达。要素层可保留 1–4 个直接影响，但单个
形式计划只选择一个影响，避免把不同关系拼成一条公式。它保持 v3.14 历史结果不变，并已
完成[三例开发回归](docs/V315_DEVELOPMENT_REPORT.md)和
[五份冻结新报告留出测试](evaluation/prompt_v315_holdout_01/REPORT.md)：工程完成 4/5，
关系分类初评 4/4，但严格 P/I/V 公式全通过为 0/4，另有 1/5 输入结构误拒绝。
这说明分类覆盖改善，公式语义绑定仍是主瓶颈；小样本结果不是总体准确率。
新增的核心观测量对齐门要求 I/V 关系变量的来源覆盖所选意图及全部直接影响，输出
`relation-alignment.json`；实现与边界见 [v3.15 本地报告](docs/V315_RELATION_REPORT.md)。

最新实验版 `semantic-v3.16` 新增 `report-formal-plan/4`：关系类别唯一决定公式模板，
派生量必须通过 `derived_definitions` 定义，形式化重试只能修改校验器允许的局部字段。
[五例开发回归](docs/V316_DEVELOPMENT_REPORT.md)最终工程完成 5/5，但严格公式初评仅 1/5；冻结后
的[五份全新报告留出测试](evaluation/prompt_v316_holdout_01/REPORT.md)得到 5/5 合法要素、
3/5 最终候选、严格公式 1/3。当前主要问题仍是攻击限定与公式作用域不一致；此外数值扫描
会把 ERC-4337/EIP-191 误认成数值约束。所有结果仍是 `needs_review`，不是总体准确率。

本地实验版 `semantic-v3.17` 已增加权限、边界、比例、状态对应、时序和进度专用模板，
并在 SMT 前检查 impact 限定、不同 P 的独立来源绑定及协议编号误识别。全量本地回归
336/336，v3.16 历史候选仍可重放。授权后的五例开发回归得到 2/5 候选，两例均可离线
重放，但语义初评仅一例较完整，且发现派生定义空真风险；因此推荐命令暂时仍使用 v3.16，
v3.17 只作实验。见 [v3.17 实现报告](docs/V317_IMPLEMENTATION_REPORT.md)、
[开发回归报告](evaluation/prompt_v317_development_03/REPORT.md)和
[阶段性成果汇报](docs/STAGE2_PRESENTATION_REPORT.md)。
以下 v3.8/v3.9 内容保留为历史实验记录。

后续阶段二完整神经测试统一显式选择 `--provider deepseek --model deepseek-flash`；
官方 API 的 `deepseek-flash` 对应 DeepSeek-V4.1-Flash。密钥只从被 Git 忽略的
`config/stage2_deepseek.local.env` 读取。底层 CLI 保留 OpenCode 默认值以兼容旧离线回归，
因此直接调用时必须显式加上述两项。已完成[三报告真实开发测试](evaluation/deepseek_flash_pilot_01/REPORT.md)：3/3 返回首步 JSON，2/3 通过要素校验，首次 0/3 进入 Z3。随后通过[显式机械修复及部分继续](evaluation/deepseek_flash_salvage_01/REPORT.md)，在另一开发目录使 3/3 要素可用、2/3 形成公式并运行 Z3，但发现 I/V 极性反转等语义问题，不能据此报告准确率。[V4.1-Flash 三份新报告测试](evaluation/deepseek_v41_fresh_01/REPORT.md)也已完成。`--mechanical-salvage` 默认关闭，且不放宽数值、来源或公式校验。
填写方法、权限检查和运行示例见[直连配置说明](docs/DIRECT_DEEPSEEK_SETUP.md)。

最新针对 P 准确性的改进是可选的**证据/时序双轴审查**：既看每条前提是否由其
编号原文支持，也看它是否真发生在测试动作和坏结果之前。条件式报告无需证明
历史上已发生，但额外权限、历史事实或混入 P 的坏结果会进入待审。
[小样本真实回归、模型空响应及准确率边界](docs/PRECONDITION_AUDIT_V4_REPORT.md)；
实验版 `semantic-v3.9` 仅完成单次要素提取，尚未证明比 v3.8 更准确，默认版本不变。
已有两步运行结果可额外审查一次（会向配置的外部模型发送该运行引用的报告原文片段）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/preconditions.py audit \
  --run-dir tools/report_constraints_v2/results/semantic/prompt_v38_holdout_01/sukuk_vault_approval \
  --output tools/report_constraints_v2/results/semantic/my_support_audit \
  --allow-report-upload
```

检查新目录的 `support-audit.json` 和 `audited-triage.json`；审查只会降低候选等级，
不替代独立人工核验。输出目录必须是新路径，避免覆盖历史记录。

最新实验版 `semantic-v3.8` 增强前提证据蕴含检查的提示、区分规范要求与实际触发条件，
并支持正固定除数的整数整除约束。两份预先冻结的新报告均完成提取、形式化和 Z3，
但都路由到 `review`，不能据此宣称准确率；结果和耗时见
[v3.8 留出小测](evaluation/prompt_v38_holdout_01/REPORT.md)。另有可选的逐条 P 证据支持
审查脚本 `preconditions.py audit`，其结论仅作人工复核提示，不自动放行候选。
默认提示版本及历史运行未被替换。

当前可选用 `--formal-retries 1` 或 `2` 对第二步空/非法 JSON、超时或无效形式计划进行
至多两次有记录重试；
`--extract` 模式另可使用 `--element-retries 1` 对第一步超时或非法 JSON 最多重试一次。
`semantic-v3.12` 至 `semantic-v3.17` 的神经形式化还可选 `--lean-formal-input`，只把已提取的语句/实体内容送入第二步；这仍属于报告衍生数据外传，需要单独明确授权。
可先用 `preview.py plan --case-dir CASE_DIR --elements ELEMENTS_IDS_JSON` 在本地查看这一步的确切 JSON，不会调用外部模型。
两者默认都不重试，各次尝试分别保存；历史实验不变。完整运行另生成 `auto-triage.json`，将结果分为
`candidate`、`review`、`abstain`、`pipeline_failure`，**不是漏洞真实性判定**。
同一份 Sequence 报告在受限终端 `exit 1`，在允许外部访问的环境中一次完成第二步与 Z3；
环境对照及准确性边界见[诊断报告](evaluation/DIAGNOSE_SEQUENCE_01.md)。
Sequence 与 GTE 两个旧失败案例的第二步在可访问环境中各一次完成，均仍需语义复核；
见[稳定性复验](evaluation/STABILITY_RETEST_01.md)。
两份新报告的完整两步小测与首次真实受控重试见
[Forte/Merkl 小测](evaluation/generalization_probe_01/REPORT.md)；工程链完成不代表语义通过。
通用性评测及抽样人工核验的边界见
[GENERALIZATION_PROTOCOL.md](evaluation/GENERALIZATION_PROTOCOL.md)。

## 当前推荐入口

所有操作统一走仓库根目录的 `main.py`。它只做分发，不改变任何脚本行为，参数原样转发、退出码原样返回：

```bash
cd /root/sc_slicer_standalone
python main.py doctor                 # 环境与配置自检
python main.py versions               # 已冻结 Prompt 版本与功能开关
python main.py preview-prompt --part definitions  # 查看 P/I/V 规范，不调用模型
python main.py preview-prompt --part element      # 查看第一步最终 Prompt
python main.py preview-prompt --part formal       # 查看第二步最终 Prompt
python main.py run --case-dir ...     # 单案例端到端
python main.py verify <候选目录>      # 零模型调用重放
python main.py test                   # 全量本地回归
```

提示：`main.py` 的相对路径按你调用时的当前目录解析。

下面保留的原始脚本写法属于**历史命令**，必须保持可重放，因此继续有效；`main.py` 中的对应命令与它们完全等价。

新报告的完整阶段二测试统一使用下列入口。DeepSeek 路径先做一次信息充分性筛选；
通过后才调用 P/I/V 提取和形式化，因此通过时通常是三次模型调用，被排除时只有一次：

```bash
PYTHONDONTWRITEBYTECODE=1 /root/.local/share/uv/tools/halmos/bin/python \
  tools/report_constraints_v2/semantic_pipeline.py \
  --case-dir /absolute/path/to/case-directory \
  --extract --provider deepseek --model deepseek-flash \
  --prompt-version semantic-v3.16 --lean-formal-input \
  --continue-on-review \
  --allow-report-upload --output tools/report_constraints_v2/results/semantic/new-run-001
```

仅在已确认相应报告片段及派生 P/I/V 可发往外部模型时使用 `--allow-report-upload`。
每次改用未存在的输出目录；不要传 `--elements`、`--formalize-only` 或历史响应作为新测试输入。
CLI 仍保存本次输出供审计，但不自动把旧输出送入下一次调用。
入口筛选要求报告同时具有：受影响对象、触发条件或行为、直接效果、可推导安全关系的依据。
任一项明确缺失时写入 `excluded_before_extraction`；仅有不确定项时写入
`needs_input_review`。两者均在 P/I/V 前停止且不生成 `elements.json`。该筛选只判断信息是否充分，
不提前提取 P/I/V，也不判断漏洞真假。
`--continue-on-review` 是阶段二的**带警告继续**：仅当 P/I/V 公式齐备、
`P∧V` 可满足且 V 直接否定 I、没有模型声明的阻塞性未决时，
即使有次级影响未覆盖、报告歧义等提示，也返回成功码并在 `status.json`、
`auto-triage.json` 列出问题。此时仍是 `needs_review`，不是语义正确、
PoC 一致或第三阶段可执行的认证；关键公式缺失、矛盾、未知证据和未定义变量仍拒绝。
不传该选项时保留旧的严格退出码，便于复现历史实验。

### 提取前输入筛选

在新案例调用模型前，可先检查 `report.json` 能否解析、配对身份和可用描述/影响文本：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/preview.py screen \
  --case-dir /absolute/path/to/case-directory
```

`preview.py screen` 只在本地检查文件可读性、精确配对身份和可发送文本，不检查任何已生成
P/I/V，也不接受 `--run-dir` 或 `--audit-dir`。其 `requires_semantic_input_screen` 表示必须
继续执行上述 DeepSeek 入口门，而不是已经允许提取。此前的提取后自动筛选和独立复核已从
活动工作流移除；结构、证据、类型和 Z3 检查仍属于规则化过程本身，不是案例入口筛选。
历史实验产物保留在 `evaluation/deepseek_v41_fresh_01/`，仅用于说明旧设计及其缺陷。

阶段二的标准 P/I/V 输入现统一为 `report.json`。程序采用字段白名单，从
`title` 和 `body` 提取被识别为漏洞描述、影响的片段，跳过 Markdown 或独立文本行标记的
修复建议/PoC；后续独立描述/影响章节仍可恢复读取。新来源可先运行
`/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/preview.py report --case-dir <案例目录>`
在本地查看将被发送的文字；该命令不调用模型、不写文件。任意格式的正文无法仅靠标题规则
保证无漏网片段。
程序不读取 `proof_of_concept`、`source_record`、
`contract.flattened.t.sol` 或其他代码字段。`metadata.json` 若存在，只核对报告身份并记录来源，
不参与语义提取。输入预处理会对 `title` 与正文首个同名 H1 去重。第二步同时接收程序生成的
P/I/V 允许 ID 列表，`impact_ids` 和覆盖项只能逐字复制已提取 impact ID，不能新造标签。
Markdown/纯文本入口仅为历史实验兼容。

若第一步要素已通过证据校验，可用 `--formalize-only --elements elements-ids.json`
只重跑第二步；它会根据同一报告重建证据目录并重新校验 ID，不修补或跳过第一步结果。

`semantic-v3.4` 在 v3.3 基础上进一步要求：每个 claim 的
`effect_coverage.statement_id` 集合必须与该 claim 的 `impact_ids` 完全相等；未认领影响
只能进入 limitations，不能生成额外 coverage 行。v3.2/v3.3 保持不变以保留历史复现。
本地完整回归 188/188 通过；GTE `--formalize-only` 真实单调用在 240 秒超时且未返回候选，
因此外部效果仍为 `not_evaluated`，未进入 Z3。见
[v3.4 coverage 复验](evaluation/prompt_v34_formalize_only_01/REPORT.md)。

`semantic-v3.5` 改为“模型选择、程序合成”：第二步模型只返回 P/I/V 来源 ID、可观察
符号、P predicate 绑定和一个逻辑 pattern；`plan_synthesizer.py` 确定性生成 AST、
coverage、formula_sources、claim 外壳和未认领影响 limitations，再交给原校验器和 Z3。
这不是漏洞规则目录，模型仍需从报告推导语义；程序只承担结构和逻辑组合。
本地完整回归 193/193 通过。GTE 单次外部验证因缺少“将该报告语义发送到指定模型服务”
的明确授权而被安全审查阻止，数据未发送；见
[v3.5 本地与授权状态](evaluation/prompt_v35_plan_synthesis_01/REPORT.md)。

`semantic-v3.6` 是当前端到端 smoke 版本：不放宽底层校验，只补强
`precondition_ids` 与 `precondition_terms` 的一一对应、P 来源角色和单个核心 impact 要求。
在不含私有数据的合成报告上，真实模型调用已完成，程序生成 AST/SMT、Z3 查询和
`stage3-spec.json`，离线重放通过；结果因保留未决项和延期次级影响而为 `needs_review`。
这证明技术链已跑到底，但不代表真实报告准确率。详见
[v3.5/v3.6 端到端 smoke](evaluation/prompt_v35_e2e_smoke_01/REPORT.md)。
当前版本的效率、单案例语义检查、错误原因和准确率边界汇总见
[semantic-v3.6 当前测试报告](evaluation/prompt_v36_current_01/REPORT.md)。

真实报告金标准第一批已建立为五份公开、非敏感报告，并提供输入哈希、P/I/V 草案、原文证据、
人工审核卡和拒绝未审核评分的工具。当前仍待人工确认，不能提前宣称准确率；见
[gold-v1 说明](evaluation/gold_v1/README.md)和[审核卡](evaluation/gold_v1/REVIEW.md)。

`semantic-v3.7` 将 `unresolved` 结构化为类别、描述、来源 ID 和是否阻塞形式化。正常的符号
地址无具体值、布尔结果无数值定义、尚未绑定代码等不再允许作为未决原因；非阻塞说明保留在
`unresolved-review.json` 中，但不进入 claim 的阻塞 unresolved。v3.5/v3.6 历史输出保持兼容。

```text
report.json -> title + description/impact -> evidence IDs -> P/I/V -> formal constraints
```

最新本地改进版为 `semantic-v3.3`：保留冻结的 v3.2 原文与历史 A/B 哈希不变，新增
`report-json-input/2` 标题去重，以及第二步由程序提供的分角色 statement-ID 白名单。
`impact_ids`、effect 来源和覆盖项只能复制白名单 ID，不能新造描述性标签。185/185
本地回归通过，74 个受保护文件未变。单案例完整 smoke 在第一步因模型返回无证据
assumption 而被拒绝；随后通过 `--formalize-only` 复用已验证要素，真实第二步已正确复制
`imp_fok_fail` 且不再添加非法 `impact_id` 字段，但因多写一个未认领 impact 的 coverage
仍被拒绝、未进入 Z3。目标 ID 修复部分有效，coverage 集合约束仍待加强；见
[v3.3 smoke 记录](evaluation/prompt_v33_smoke_01/REPORT.md)。

最新真实 A/B 测试见 [v3 与 v3.2 的 P/V 优先改进评测](evaluation/prompt_v32_ab_01/REPORT.md)：同一批三份新报告中，v3 三例均发生超时，v3.2 三例均完成两步和离线重放。v3.2 的 Z3 直接 V/I 门槛为 3/3，但人工语义初评只有 2 pass、1 partial；P 完整性仅 1/3 pass，P 角色纯度 0/3 pass，正式 I 0/3 pass。因此只确认管线完成率和候选内部关系改善，尚不能确认准确率提升，默认仍为 v3。

新增实验版 `semantic-v3.2`：依据[五个公开真实报告参考案例](reference_cases/online_clear_01/README.md)提炼权限、边界、非法输入和状态保护四类**逻辑构造模块**，重点修复已重复出现的 P 污染、I 强度/方向和 V 不能见证 `not I`。要素提示逐项扫描条件词；正式化必须使用已提取的核心 P，遗漏会进入 `unassigned_precondition_ids` 并阻止自动候选通过；`P AND V AND I` 只要可满足或未知，就会触发直接 V/I 关系失败并进入人工复核。实现和边界见 [P/V 优先改进记录](docs/PIV_FOCUS_REPORT.md)。案例答案与运行 Prompt 隔离，并标记为开发集而非留出集；v3.2 尚未经过真实模型盲测，默认仍是 `semantic-v3`。可显式传入 `--prompt-version semantic-v3.2`，无需第一阶段输入。

当前默认仍使用规则更完整的 `semantic-v3`。[P/I/V Prompt v3.1 实验](docs/PROMPT_V31_REPORT.md)将要素/core 提示缩短约 45.8%/55.0%，但[新留出集实测](evaluation/prompt_v31_holdout_01/REPORT.md)中正式 I 为 0 pass、2 partial、3 fail，完整 P/I/V 为 0/5，因此没有升级为默认。v3.1 结果和入口完整保留，可用 `--prompt-version semantic-v3.1` 重放；下一步需针对 schema、模态、等式弱化和 V/I 关系做小范围 v3.2。

[v3.1 第三批一致性复测](evaluation/prompt_v31_consistency_02/REPORT.md)保持 Prompt 不变并更换五个 finding：10 次调用无超时，正式管线完成 4/5，正式 I 初评 3/5，完整 P/I/V 仅 1/5。P 缺失/污染 3/5、V 不能见证 `not I` 2/5、模态升级 1/5，均与上一批错误方向一致；schema 错误和超时没有重复。小批次比例波动大，不能当总体准确率。

最新真实测评：[semantic-v3 留出集测评](evaluation/prompt_v3_holdout_01/REPORT.md)。5 份未参与 Prompt 设计的报告、10 次调用、无重试；要素提取五维严格 pass 单元 22/25（88%，助手初评而非总体准确率），正式 I 和端到端正式化均为 1/5（20%），4/5 在第二步超时。结论是自然语言要素理解较好，但正式化负担过重，当前不适合稳定批量使用。

Prompt 实现说明见 [通用语义 Prompt v3](docs/PROMPT_V3_REPORT.md)。两步提示强化前提/实现/结果分离、执行限定、作者模态、if/only-if、子来源与单位要求，并加入三个不含测试案例答案的教学例。旧提示字节快照已保留，接口、底层校验与第一阶段不改。

v3 接入时完整本地回归 146/146 通过，受保护 74 文件未变。真实留出集已测，但样本小且评分未获独立专家确认，不能给出总体准确率。

最新多报告真实测试：[五报告评测](evaluation/multi_report_01/REPORT.md)。五个不同项目/报告、十次调用、无重试；助手预先参考下核心 I 对应 2/5、部分 1/5、错误 2/5，正式 SMT/Z3 链路完成 2/5（仍 needs_review）。131,036 上报 tokens。该 40% 是小样本助手初评的窄 I 对应比例，不是正式总体准确率；来源、单位、前提和蕴含方向仍有问题。原始输出和逐项评分均独立归档，第一阶段未修改。

最新观察量提示真实复验：[BRIX_OBSERVABLE_RETEST_REPORT.md](docs/BRIX_OBSERVABLE_RETEST_REPORT.md)。同一 Brix 报告两次模型调用，I 本轮自行表达为限定付款条件下不发生特定费用回退，P 增加付款等于 helper 结果；但缺三处布尔子公式来源路径，正式校验拒绝，另发现两项覆盖来源缺项。正式 SMT/Z3 链路未执行，独立数学诊断仅支持窄 I 的逻辑对应，不算自动验收成功。共 43,041 上报 tokens，无重试，第一阶段未修改。

最新本地进展：I 的观察量表达要求、`review.py` 和新输出审核文件已接入；原始真实候选的独立旗标会触发人工复核提醒。另存助手对照样例显示以观察量表达 I 后可消除该逻辑缺口，但不算模型成绩。119/119 回归测试通过，本轮模型调用为零，第一阶段与原始输出不改。见 [观察量改进记录](docs/BRIX_CORE_RETEST_REPORT.md#后续本地改进观察量表达及审核提示)。

最新真实结果：[BRIX_CORE_RETEST_REPORT.md](docs/BRIX_CORE_RETEST_REPORT.md)。核心模式首次完成两次模型调用、SMT/Z3 和只读重放，但候选仍 `needs_review`：P/V 更精确，I 却是未定义关联的独立布尔量，坏效果与 I 可同时成立，不能宣称语义合格。两次共 35,297 上报 tokens，第一阶段未变。

本地改进已完成：自动路径默认请求 `--formalization-scope core`，先聚焦核心 P/I/V；`full` 保留更广生成模式。完整要素不裁剪，未形式化影响继续提示覆盖不完整。提示加强严格比较、付款关系、特定失败原因、窄安全义务及 claim 模态保持；校验器和 SMT/Z3 底层逻辑未改。109/109 回归测试通过，本轮外部调用为零；不代表新提示已真实跑通或准确率提高。详见 [复验报告中的改进记录](docs/BRIX_RETEST_REPORT.md#本地改进完成记录)。

最新真实复验见 [BRIX_RETEST_REPORT.md](docs/BRIX_RETEST_REPORT.md)：改进提示后第一步通过，第二步生成候选但因可能性升级被拒绝；两次调用共 40,853 上报 tokens，Z3 未执行。用户已认可的 Brix 审核卡也发现前提放宽、I 偏强及 V 回退种类不精确等差异，不能称语义合格或端到端成功。

真实报告准确性推进（2026-09-14）：新增 [Brix 逐条语义审核卡](review_samples/brix_report/REVIEW.md)和[复核记录](review_samples/brix_report/PROGRESS.md)，通用提示加强前提独立提取、安全意图、效果原子化及动作引用要求，校验器不放宽。新增真实失败回归；本轮不调用模型，准确性改善仍待真实复验。

新增 [公开规范参考审核样例](review_samples/README.md)：三份简单性质的中文练习、参考 AST、[逐条审核卡](review_samples/REVIEW.md)和本地公式比较工具。参考材料依据 Certora 官方规范整理，均待用户审核；不是真实漏洞报告，不算模型准确率，本轮不调用外部模型。

最新实现见 [EVIDENCE_IDS_REPORT.md](docs/EVIDENCE_IDS_REPORT.md)：模型默认只返回原文证据编号，程序精确取回原文；新增模块化 SMT、Z3 求解状态及规范层反例。实现轮 84/84 回归测试通过。

最新真实复验见 [EVIDENCE_IDS_REAL_REPORT.md](docs/EVIDENCE_IDS_REAL_REPORT.md)：同一份 Brix 报告调用一次，编号解析成功，但动作序列引用了 `root_cause` 陈述，被类型检查拒绝。第二步和 Z3 未执行，链路尚未端到端跑通；原始失败输出保留，未手工修补或追加调用。

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_semantic.py \
  tools/report_constraints_v2/results/semantic/brix_fee_ids_offline_final
```

历史引文模式复验见 [TWO_STEP_REPORT.md](docs/TWO_STEP_REPORT.md)：Brix 第一步返回核心要素，但一条引文被模型拼接改写，精确证据检查拒绝；第二步未执行。共一次调用、15,055 上报 tokens。以下框架和离线验证结果不能代替真实抽取质量。

已增加“报告核心要素 → 形式化候选 → 自动符号验收”的分层流程，设计、方法来源及评测方案见 [SECOND_STAGE_DESIGN.md](docs/SECOND_STAGE_DESIGN.md)。本轮不增加模型调用、不修改第一阶段；68/68 回归测试通过，不代表自动抽取准确率。

```text
semantic_core.py       核心要素、来源/模态/覆盖校验及逐 claim 验收
prompts/definitions.py P/I/V 集中式规范定义
prompts/active.py      生产 Prompt 的显式解析、契约检查与哈希
prompts/registry.py    Prompt 版本与功能矩阵统一入口
prompts/versions/      冻结 Prompt 实现，不原地改写旧版本
semantic_pipeline.py   独立报告或配对案例入口；默认离线
verify_semantic.py     原报告、证据、规范与 SMT 的只读复验
tests/                 自动回归测试
docs/                  当前状态、设计和历史报告
samples/brix_fee/      明确标记为助手推导的分层示例
results/semantic/      新分层结果，历史模型输出未覆盖
```

离线复验已有示例：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_semantic.py \
  tools/report_constraints_v2/results/semantic/brix_fee_offline_01
```

从已有核心材料与候选公式生成新结果（输出目录必须不存在）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/semantic_pipeline.py \
  --report tools/report_constraints_v2/results/report_only/brix_fee_assistant_final/report.json \
  --elements tools/report_constraints_v2/samples/brix_fee/elements.json \
  --formalization tools/report_constraints_v2/samples/brix_fee/formalization.json \
  --origin assistant_review --output runs/report_semantics/NEW_ID
```

`--report` 接受含 body 的 JSON、Markdown 或文本，**不需要第一阶段输出**。`--case-dir` 则额外只读核对精确配对与代码 SHA。只处理核心要素可用 `--elements ... --elements-only`。

获得本次报告外发授权后，自动路径为 `--report FILE --extract --allow-report-upload --output NEW_DIR`，最多两次调用，无自动重试；本轮未运行该新路径。第一次生成要素，第二次仅看要素和报告 prose 生成公式，不读 PoC/已有公式。

输出包含 `elements.json`、`evidence-spans.json`、`formalization.json`、`constraints.json`、每个 claim 的 SMT、`stage3-spec.json` 与状态。核心形式化状态、语义验收状态、代码绑定状态分离。本示例 I 已形式化，因部分报告影响与歧义未解决，验收仍为 needs_review。

新 schema 为 `report-elements/1`、`report-formalization/1`、`stage2-semantic-bundle/1`，接口为 `stage3-semantic-spec/1`。该接口是待绑定规范，不是旧 consumer 的执行就绪格式。SMT 不含代码 T，不能独立证明 PoC 一致性。

## 先前报告实验（保留记录）

**当前主线已调整为报告驱动的独立推导与形式化**，见 [REPORT_ONLY_REPORT.md](docs/REPORT_ONLY_REPORT.md)。下文迁移/切片实验保留为历史，不再要求切片成功后才能开展第二阶段。

**最新真实自动验证见 [AUTO_REPORT.md](docs/AUTO_REPORT.md)**：Brix 一次模型调用完成，但模型将坏效果写成安全性质，语义验收不通过。原始输出保留在 `results/report_only/brix_fee_model_01/`；新增离线关系审查将其标为 `needs_review`。当前测试 45/45 通过，不代表抽取正确。

此前三样例本地验证见 [BATCH_REPORT.md](docs/BATCH_REPORT.md)，结果位于 `results/report_only/batch_assistant_01/`。费用、时间及权限三个候选全部为助手原文推导，该批不算外部自动评测。

此前单调用入口 `report_only.py` 不使用样例专用符号目录或不变量模板。曾被审核阻拦，后来批准的 Brix 一次真实调用发现安全方向错误；助手成功候选与真实模型失败输出分开保存，不能混算自动提取评测。

离线复验新样例（零模型调用）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_report_only.py \
  tools/report_constraints_v2/results/report_only/brix_fee_assistant_final
```

获得报告外发授权后，可运行任意精确配对案例；输出目录必须不存在：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/report_only.py \
  --case-dir /path/to/exact_case --allow-report-upload \
  --output runs/report_constraints_report_only/NEW_ID
```

新 schema 为 `report-semantics/1`；`stage3-spec.json` 是待绑定规范，不是符号执行就绪输入。
早期切片绑定和旧阶段三接口实验已退出阶段二主线，其未使用代码与产物已从本目录清理。
