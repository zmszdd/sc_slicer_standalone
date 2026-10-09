# 阶段二：直连 DeepSeek 官方 API

这是一条 `semantic_pipeline.py` 主流程的**可选**模型传输路径；其他辅助脚本和原有 OpenCode 默认行为、第一阶段、第三阶段均不变。已在用户授权后进行[三报告真实开发测试](../evaluation/archive/deepseek_flash_pilot_01/REPORT.md)；连接与返回 JSON 正常，但三例都被后续本地校验拒绝，尚未形成有效正式计划。

1. 打开项目根目录的 `config/stage2_deepseek.local.env`，在等号后填入自己的官方密钥：

   ```text
   DEEPSEEK_API_KEY=sk-你的密钥
   ```

   文件已创建为空值、权限设为 `600`，并被 `.gitignore` 的 `config/*.local.env` 规则忽略。不要把密钥填入聊天、报告、命令参数或 `config/llm.env`；后者属于其他工具的统一配置。编辑后可运行 `chmod 600 config/stage2_deepseek.local.env`，避免编辑器重置权限。

2. 可仅在本地验证文件格式与权限（**不联网、不验证额度**）：

   ```bash
   PYTHONDONTWRITEBYTECODE=1 /root/.local/share/uv/tools/halmos/bin/python -c "import sys; sys.path.insert(0, 'tools/report_constraints_v2'); from report_only import load_deepseek_key; load_deepseek_key(); print('密钥文件格式与权限通过；未联网')"
   ```

3. 获得要发送的报告数据范围授权后，先用 `preview.py report` 查看第一步原文，再运行，例如：

   ```bash
   /root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/semantic_pipeline.py \
     --case-dir /path/to/case \
     --extract --provider deepseek --model deepseek-flash \
     --prompt-version semantic-v3.12 --lean-formal-input \
     --continue-on-review --allow-report-upload \
     --output tools/report_constraints_v2/results/semantic/direct_deepseek_01
   ```

   第一步向官方 API 发送经本地解析器筛选的报告编号片段，目标范围是标题、描述和影响；由于报告格式不统一，**实际文本须先预览确认**。第二步发送已提取的 P/I/V 等语句、实体和歧义信息。`--lean-formal-input` 只去掉重复的原文片段，**不等于不上传衍生语义数据**。这些数据范围需要明确授权。`--continue-on-review` 仅让核心公式完整且逻辑关系成立的待审结果带警告继续，绝不表示语义或 PoC 已被证实。输出目录须为新路径，避免覆盖历史结果。

官方接口固定为 `https://api.deepseek.com/chat/completions`；V4.1-Flash 在官方 API 中使用模型 ID `deepseek-flash`，不是 `deepseek-v4.1-flash`。阶段二完整测试须显式传 `--provider deepseek --model deepseek-flash`，两个模型调用才会走同一路径；底层 CLI 保留旧默认值以兼容既有离线测试。启用 JSON 输出、非思考模式和 240 秒请求上限。代码拒绝重定向、不把密钥或 HTTP 错误正文写入日志。JSON 合法只代表可解析，仍需项目的证据、形式约束和语义审核。API 调用可能计费；小样本无超时不代表长期稳定，实际账单需在账户侧核对。接口参数依据 [DeepSeek 官方首次调用说明](https://api-docs.deepseek.com/)与 [JSON 输出说明](https://api-docs.deepseek.com/guides/json_mode/)。
