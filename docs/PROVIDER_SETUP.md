# Provider 配置（合作者自配）

本仓库不包含任何真实 API key。`config/llm.env`、`config/stage2_deepseek.local.env`
和其他 `config/*.local.env` 都被 `.gitignore` 排除；请不要把 key 粘贴到 issue、
聊天记录或提交信息中。若曾经误传，先吊销并轮换 key。

## 1. 配置 Stage-2 主 provider

```bash
cp config/llm.env.example config/llm.env
chmod 600 config/llm.env
```

按所用通道填写 `LLM_PROVIDER`、`MODEL_NAME` 和对应 key。OpenCode 可设置
`OPENCODE_API_KEY`；DeepSeek 通道还需要下面的独立本地文件。

## 2. 配置 DeepSeek key

```bash
cp config/stage2_deepseek.local.env.example config/stage2_deepseek.local.env
chmod 600 config/stage2_deepseek.local.env
```

然后填写 `DEEPSEEK_API_KEY`。该文件只用于 Stage-2 / binding 的 DeepSeek 通道。

## 3. 验证

```bash
make provider-check
make doctor
```

`make provider-check` 只发最小请求验证鉴权、额度和网络，并在 15 秒内返回结构化结果；
`make doctor` 还会检查外部数据根是否配置。两者都不需要把 key 提交进仓库。
