"""main.py 单一入口的阶段三闭环命令分发回归。

背景：`_delegate_stage3` 对未登记子命令一律兜底到 `stage3_pipeline`，
曾导致 ``python main.py stage3 autorun`` 等闭环命令被静默误路由。
本测试锁定四个闭环命令的登记与路由，防止端到端闭环从入口处再次断开。
"""
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

LOOP_SUBCOMMANDS = {
    'autorun': 'stage3_autorun.py',
    'verdict-loop': 'stage3_verdict_loop.py',
    'acceptance': 'stage3_acceptance.py',
    'metrics-sync': 'stage3_metrics_sync.py',
}


class MainStage3DispatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT))
        cls.main = importlib.import_module('main')

    def test_loop_subcommands_registered(self):
        for name, module in LOOP_SUBCOMMANDS.items():
            with self.subTest(command=name):
                self.assertEqual(self.main.STAGE3_SUBCOMMANDS.get(name), module)

    def test_loop_modules_exist(self):
        cli_dir = ROOT / 'tools' / 'stage3' / 'cli'
        for module in LOOP_SUBCOMMANDS.values():
            with self.subTest(module=module):
                self.assertTrue((cli_dir / module).is_file(), module)

    def test_delegate_routes_to_loop_modules(self):
        calls = []
        original = self.main._run_stage3_module
        self.main._run_stage3_module = (
            lambda module, argv: calls.append((module, list(argv))) or 0)
        try:
            for name in LOOP_SUBCOMMANDS:
                self.main._delegate_stage3([name, '--help'])
        finally:
            self.main._run_stage3_module = original
        self.assertEqual([call[0] for call in calls],
                         list(LOOP_SUBCOMMANDS.values()))
        self.assertTrue(all(call[1] == ['--help'] for call in calls))


if __name__ == '__main__':
    unittest.main()
