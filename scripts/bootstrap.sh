#!/usr/bin/env bash
# 一键补齐 SC_Slicer 的可移植依赖（幂等）：
#   python3 + z3-solver + Foundry(forge) + Rust(cargo/rustc)
# 默认仅 doctor；传 install 才会写入系统/用户环境。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="${PYTHON:-python3}"

case "${1:-doctor}" in
  doctor)
    "$REPO/scripts/doctor.sh"
    exit $?
    ;;
  install)
    ;;
  *)
    echo "用法: $0 [doctor|install]" >&2
    exit 2
    ;;
esac

# 1) python + z3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "未找到 python3；请先安装 Python 3.10+ 后重试。" >&2
  exit 1
fi
if ! "$PY" -c 'import z3' >/dev/null 2>&1; then
  echo ">> 安装 z3-solver（按 requirements.txt 锁定版本）"
  "$PY" -m pip install --user -r requirements.txt
fi

# 2) Foundry
if ! command -v "${FORGE:-forge}" >/dev/null 2>&1; then
  echo ">> 安装 Foundry（forge/cast/anvil）"
  curl -L https://foundry.paradigm.xyz | bash
  # shellcheck disable=SC1091
  export PATH="$HOME/.foundry/bin:$PATH"
  foundryup
fi

# 3) Rust
if ! command -v cargo >/dev/null 2>&1 || ! command -v rustc >/dev/null 2>&1; then
  echo ">> 安装 Rust 工具链"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  # shellcheck disable=SC1091
  export PATH="$HOME/.cargo/bin:$PATH"
fi

echo
"$REPO/scripts/doctor.sh"
