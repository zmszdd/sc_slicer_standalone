# 共享库层：被 cli/ 与 lib/ 内部复用；不做命令行入口

# 历史模块名兼容注册（与 cli/__init__.py 对称；相对导入不依赖 sys.path）。
from . import compat  # noqa: E402

compat.install()
