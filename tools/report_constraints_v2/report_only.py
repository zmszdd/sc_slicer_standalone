"""Compat 别名：实现已迁至 lib/report_only.py（S3）。本文件仅做模块别名。"""
import sys, lib.report_only as _m
sys.modules[__name__] = _m
