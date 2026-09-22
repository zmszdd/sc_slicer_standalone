# 入口层：由仓库根目录的 main.py 分发

# 历史模块名兼容注册。这里必须装：`python -m cli.<x>` 会先导入本包，
# 因此这是唯一能覆盖 `-m` 子进程的注册点。
from lib import compat  # noqa: E402

compat.install()
