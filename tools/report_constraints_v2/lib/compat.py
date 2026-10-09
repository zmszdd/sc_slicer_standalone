"""历史模块名 → 当前实现的兼容注册。

阶段二重构后，下面 14 个旧模块名不再对应任何文件：

* 8 个因**合并**而消失（内容并入了 lib/ingest.py、lib/solving.py、
  lib/salvage.py、cli/batch_verify.py）
* 6 个因**移动**而改变位置（现在位于 cli/ 或 lib/）

2026-10-09 收口：lib/、cli/、tests/ 的活跃代码已全部改为点分路径导入
（本表右列的名字），本注册的受众只剩**历史侧**——evaluation/ 里冻结批次
的脚本（如 prompt_live1_blind_01/probe_assumption_relief.py）、归档
脚本与未来的离线重放片段。因此这里用 ``sys.meta_path`` finder **延迟**
解析：只有当某个旧名字真的被 import 时，才去加载它指向的模块，不会在
启动时把 16 个模块（含 z3 与 53KB 的 semantic_pipeline）全部拉进来。

为什么必须 ``sys.meta_path.insert(0, ...)`` 而不能 append：删掉旧文件名之后
cli/ 与 lib/ 都在 ``sys.path`` 上，若让 PathFinder 先跑，``import report_only``
会把 ``lib/report_only.py`` 加载成一个名为 ``report_only`` 的**独立模块**，
与 ``lib.report_only`` 变成两份互不相干的对象（模块级状态会分叉）。
插到最前面可保证别名就是真模块本身::

    sys.modules['fidelity'] is sys.modules['lib.salvage']   # True
"""
import importlib
import importlib.abc
import importlib.util
import sys

# 旧名字 -> 现在真正包含该代码的模块（点分全名）。
ALIASES = {
    # 因合并而消失的名字
    'evidence_catalog': 'lib.ingest',
    'report_readiness': 'lib.ingest',
    'review': 'lib.solving',
    'symbolic_queries': 'lib.solving',
    'fidelity': 'lib.salvage',
    'mechanical_salvage': 'lib.salvage',
    'run_semantic_batch': 'cli.batch_verify',
    'verify_semantic': 'cli.batch_verify',
    # 因移动而改变位置的名字
    'semantic_core': 'lib.semantic_core',
    'plan_synthesizer': 'lib.plan_synthesizer',
    # semantic-live-5：cli/ 内的裸名 import（`from stage3_consistency import ...`）
    # 在 `-m cli.<x>` 子进程里没有 lib/ 前置 sys.path，走同一延迟解析路径。
    'stage3_consistency': 'lib.stage3_consistency',
    # DeepSeek 连接唯一定义处：cli/ 对它的裸名 import 同理。
    'deepseek': 'lib.deepseek',
    'report_only': 'lib.report_only',
    'semantic_pipeline': 'cli.semantic_pipeline',
    'preview': 'cli.preview',
    'preconditions': 'cli.preconditions',
}


class _AliasLoader(importlib.abc.Loader):
    """把旧名字绑定到已存在的模块对象（不复制、不重载）。"""

    def __init__(self, target):
        self._target = target

    def is_package(self, fullname):
        return False

    def create_module(self, spec):
        # 直接返回目标模块本身；importlib 会把它放进 sys.modules[spec.name]。
        # 目标模块已有 __name__ / __spec__，_init_module_attrs 不会改写它们。
        return importlib.import_module(self._target)

    def exec_module(self, module):
        pass  # 目标模块早已初始化完毕


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        target = ALIASES.get(fullname)
        if target is None:
            return None
        return importlib.util.spec_from_loader(fullname, _AliasLoader(target))


def install():
    """注册 finder；幂等，重复调用不会装多份。"""
    if not any(isinstance(f, _AliasFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _AliasFinder())


def resolve(name):
    """旧名字对应的点分全名；未知名字返回 None。供 doctor 自检使用。"""
    return ALIASES.get(name)
