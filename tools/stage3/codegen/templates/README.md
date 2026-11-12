# 补丁模板

M1 使用案例内 `patched/` 参考源码，不依赖模板。M4 做 AST 注入时，这里放
`require/assert/snapshot` 的 Solidity 模板，由 `lib/codegen.py` 渲染。
