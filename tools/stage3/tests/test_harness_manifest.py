import json
import tempfile
import unittest
from pathlib import Path

from lib.harness_manifest import build, write


def _case(root: Path, name: str = 'case') -> Path:
    case = root / name
    (case / 'src').mkdir(parents=True)
    (case / 'foundry.toml').write_text('[profile.default]\n')
    return case


class HarnessManifestTest(unittest.TestCase):
    def test_self_contained_flatten_is_local_runnable(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            source = case / 'src' / 'contract.flattened.t.sol'
            source.write_text(
                'contract PoC { function testExploit() public {} }\n')
            manifest = build(case, compile_status='ok')
            self.assertEqual(manifest['route'], 'self_contained_flatten')
            self.assertTrue(manifest['test_entrypoint'])
            self.assertTrue(manifest['local_runnable'])
            self.assertEqual(manifest['forge_command'],
                             'forge test --root case')
            self.assertEqual(len(manifest['compile_hash']), 64)

    def test_missing_test_entrypoint_is_a_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'A.sol').write_text('contract A {}')
            manifest = build(case)
            self.assertEqual(manifest['route'], 'needs_harness')
            self.assertFalse(manifest['test_entrypoint'])
            self.assertIn('no_test_entrypoint', manifest['blockers'])
            self.assertFalse(manifest['local_runnable'])

    def test_live_rpc_without_fixed_block_is_a_data_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'A.t.sol').write_text(
                'contract A { function testFork() public { '
                'vm.createFork(RPC_URL); } }\n')
            manifest = build(case)
            self.assertEqual(manifest['route'], 'live_rpc_ceiling')
            self.assertIn('live_rpc_no_fixed_block', manifest['blockers'])
            self.assertIn('local differential', manifest['data_ceiling'])

    def test_fixed_block_fork_is_not_live_rpc_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'A.t.sol').write_text(
                'contract A { function testFork() public { '
                'vm.createFork(RPC_URL, 18400000); } }\n')
            manifest = build(case)
            self.assertEqual(manifest['route'], 'fixed_block_anvil')
            self.assertNotIn('live_rpc_no_fixed_block', manifest['blockers'])
            self.assertEqual(manifest['fork_block'], '18400000')

    def test_external_imports_are_recorded_with_vendor_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'A.t.sol').write_text(
                'import "forge-std/Test.sol";\n'
                'contract A is Test { function testOne() public {} }\n')
            manifest = build(case)
        self.assertEqual(manifest['external_imports'], ['forge-std/Test.sol'])
        self.assertFalse(manifest['dependencies_vendored'])
        self.assertEqual(manifest['next_action'], 'vendor_dependencies')

    def test_write_persists_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'A.t.sol').write_text(
                'contract A { function testOne() public {} }\n')
            manifest = write(case)
            stored = json.loads((case / 'harness-manifest.json').read_text())
            self.assertEqual(stored, manifest)

    def test_write_preserves_negative_witness_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'src' / 'contract.flattened.t.sol').write_text(
                'contract NegWitness_x { function test_negative_witness() '
                'public {} }\n')
            (case / 'harness-manifest.json').write_text(json.dumps({
                'route': 'negative_witness',
                'local_runnable': True,
                'exploit_test': 'test_negative_witness',
                'forge_command': 'forge test --match-test test_negative_witness',
            }))
            manifest = write(case)
            self.assertEqual(manifest['route'], 'negative_witness')
            self.assertFalse(manifest['test_entrypoint'])
            self.assertEqual(manifest['exploit_test'],
                             'test_negative_witness')


if __name__ == '__main__':
    unittest.main()
