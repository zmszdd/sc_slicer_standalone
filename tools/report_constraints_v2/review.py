"""Compat 别名：实现已迁至 lib/solving.py（S7）。本文件仅做模块别名与 CLI 转发。"""
import sys, lib.solving as _m
sys.modules[__name__] = _m
if __name__ == '__main__': raise SystemExit(_m.main())
