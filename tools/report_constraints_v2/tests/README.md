# 测试目录说明

测试统一放在本目录，不再与运行代码混在项目根目录。

| 文件模式 | 作用 |
| --- | --- |
| `test_prompt_v*.py` | Prompt 版本差异、schema 和回归约束 |
| `test_*_fidelity.py` | 数值、地址等语义保真门 |
| `test_plan_synthesizer.py` | 确定性形式计划合成 |
| `test_semantic_core.py` | P/I/V schema、类型和编译 |
| `test_*evaluation.py` | 冻结评测脚本和指标重放 |
| `test_replay_current.py` | 已保存候选的只读重放 |
| 其他 `test_*.py` | 输入、修复、分流、DeepSeek 传输等专项测试 |

运行全部测试（推荐用统一入口）：

```bash
cd /root/sc_slicer_standalone
python main.py test
```

等价的原始命令：

```bash
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py' -q
```
