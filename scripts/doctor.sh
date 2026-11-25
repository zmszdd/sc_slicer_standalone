#!/usr/bin/env bash
# 可移植性自检：只读检查 python3/z3、forge、cargo/rustc，并给出安装命令。
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

ok=1
fail() { echo "[FAIL] $1"; ok=0; }
okp()  { echo "[OK]   $1"; }

PY="${PYTHON:-python3}"
echo "== SC_Slicer 环境自检 =="
echo "repo: $REPO"
echo

if command -v "$PY" >/dev/null 2>&1; then
  py_ver="$($PY -c 'import sys; print(sys.version.split()[0])' 2>/dev/null)"
  okp "python3 ($py_ver)"
  if "$PY" -c 'import z3' >/dev/null 2>&1; then
    z3_ver="$($PY -c 'import z3; print(z3.get_version_string())' 2>/dev/null)"
    okp "z3-solver ($z3_ver)"
  else
    fail "z3-solver 未安装：${PY} -m pip install -r requirements.txt"
  fi
else
  fail "python3 未找到（可用 PYTHON=/path/to/python 覆盖）"
fi

if command -v "${FORGE:-forge}" >/dev/null 2>&1; then
  forge_ver="$("${FORGE:-forge}" --version 2>/dev/null | head -1)"
  okp "foundry/forge ($forge_ver)"
else
  fail "forge 未找到：curl -L https://foundry.paradigm.xyz | bash && foundryup"
fi

if command -v cargo >/dev/null 2>&1 && command -v rustc >/dev/null 2>&1; then
  rust_ver="$(rustc --version 2>/dev/null)"
  okp "Rust 工具链 ($rust_ver)"
else
  fail "cargo/rustc 未找到：curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
fi

for key_file in config/llm.env config/opencode.local.env config/stage2_deepseek.local.env; do
  if [ -f "$key_file" ]; then
    if "$PY" - "$key_file" <<'PY'
import stat
import sys
raise SystemExit(0 if not stat.S_IMODE(__import__('os').stat(sys.argv[1]).st_mode) & 0o077 else 1)
PY
    then
      okp "private key file ($key_file)"
    else
      fail "$key_file is group/world accessible: chmod 600 $key_file"
    fi
  fi
done

echo
if "$PY" - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.getcwd(), 'tools', 'stage3'))
from lib import path_config

report = path_config.describe()
for name in ('c4_output_root', 'verified_flatten_root',
             'negative_flatten_root'):
    path = Path(report[name])
    if not path.is_dir():
        raise SystemExit(f'missing {name}: {path}')
summary = Path(report['negative_flatten_summary'])
if summary.is_file():
    print(summary)
else:
    slices = sorted(Path(report['negative_flatten_root']).glob(
        '*/contract.flattened.t.sol'))
    if not slices:
        raise SystemExit(
            'missing negative_flatten_summary and no flatten slices under '
            + report['negative_flatten_root'])
    print(f'{len(slices)} negative flatten slices; summary optional')
print(report['verified_flatten_root'])
PY
then
  okp "portable path config"
else
  fail "portable path config: see config/paths.env.example"
fi

echo
if [ "$ok" -eq 1 ]; then
  echo "结论：环境可用。下一步："
  echo "  ./scripts/bootstrap.sh install   # 如需补装依赖"
  echo "  python3 -m unittest discover -s tools/stage3/tests -q"
else
  echo "结论：存在缺失项，运行 ./scripts/bootstrap.sh install 尝试补齐。"
fi
exit $((1 - ok))
