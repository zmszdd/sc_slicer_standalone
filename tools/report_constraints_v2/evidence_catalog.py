"""Compat 别名：实现已迁至 lib/ingest.py（S5）。本文件仅做模块别名。"""
import sys, lib.ingest as _m
sys.modules[__name__] = _m
