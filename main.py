#!/usr/bin/env python3
"""SC_Slicer 阶段二唯一命令行入口（报告自然语言 → P/I/V 不变量规则化）。

用法
----
    python main.py <command> [参数...]          阶段二 / 工程命令（推荐写法）
    python main.py stage2 <command> [参数...]   同上，显式前缀写法

阶段一（代码切片）不在本入口内，请直接用 `./run.sh`。阶段三尚未实现。

模型
----
阶段二全流程默认使用官方 DeepSeek（`--provider deepseek`、模型 `deepseek-flash`）。
`run` 和 `batch` 会自动注入这两个默认值；显式传入 `--provider` / `--model` 可覆盖
（测试用的离线传输就是通过这种方式显式指定的）。

设计约束
--------
* 本文件只做分发，不实现任何阶段逻辑，也不改写任何脚本行为。
* 阶段二只有两层：入口在 cli/，共享库在 lib/，阶段二根目录不含任何 .py。
* 重构前的 14 个模块名由 lib/compat.py 的 meta path finder 延迟解析；注册点为本文件、
  tests/__init__.py、cli/__init__.py、lib/__init__.py 四处（详见该文件与 STRUCTURE.md）。
* 阶段二脚本不再从根目录直接执行：请用 `python main.py <command>`，或
  `python -m cli.<script>` / `python -m lib.<script>`（cwd 为阶段二目录）。
* 不读取、不打印、不写入任何 API Key；doctor 只检查配置文件是否存在。
* 不创建、不覆盖既有实验产物目录。
* 命令与脚本的对应关系集中在下面的表里，新增脚本只需改表，不要新增入口文件。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE2_DIR = ROOT / 'tools' / 'report_constraints_v2'
STAGE2_ENV = ROOT / 'config' / 'stage2_deepseek.local.env'

# 阶段二分两层：cli/（入口）与 lib/（共享库）。脚本查找顺序为
# cli/ -> lib/ -> 阶段二根目录；根目录只作迁移期兼容，迁移完成后应为空。
STAGE2_CLI_DIR = STAGE2_DIR / 'cli'
STAGE2_LIB_DIR = STAGE2_DIR / 'lib'
STAGE2_SCRIPT_DIRS = (STAGE2_CLI_DIR, STAGE2_LIB_DIR, STAGE2_DIR)

# 冻结资产：阶段一和 v1 一旦定稿不得原地改写，否则历史实验无法重放。
# 原清单在目录迁移中被删除，且没有任何文件引用它；此处恢复并把校验变成
# 可执行命令（python main.py frozen）。
# 注意：`.slicer_cache.json` 是可变的运行缓存，不属于冻结资产，故意不纳入。
FROZEN_MANIFEST = ROOT / 'PROTECTED_HASHES.json'
FROZEN_SCOPES = (
    'src/**/*.rs',                           # 阶段一 Rust 源码
    'run.sh',                                # 阶段一入口
    'archives/report_constraints_v1_*.zip',  # v1 归档
)

# 工程命令：不调用模型，不需要 DeepSeek 配置。两种写法等价。
META_COMMANDS = (
    ('test', '运行阶段二本地回归（可追加 unittest 参数）'),
    ('versions', '列出已冻结的 Prompt 版本与功能开关'),
    ('doctor', '环境与配置自检（只检查私密配置是否存在，不读取内容）'),
    ('status', '阶段二当前进度摘要与权威文档位置'),
    ('frozen', '校验冻结资产哈希清单（--write 可重新生成）'),
)

# 阶段二命令：command -> (脚本, 一句话说明)。脚本保持原样，入口只负责分发。
STAGE2_COMMANDS = {
    'run': ('semantic_pipeline.py',
            '单案例端到端：输入筛选 → 两步模型 → 确定性规则化 → Z3 → 产物'),
    'batch': ('batch_verify.py',
              '批量运行多个真实报告：--reports-root 自动发现，--resume 续跑'),
    'verify': ('batch_verify.py',
               '零模型调用重放候选，校验证据/公式/SMT/接口哈希'),
}

# main.py 会为 run/batch 注入四组默认参数，且只在调用者没有自己指定时生效：
#
# 前置（prepend）：阶段二全流程默认走官方 DeepSeek。只有真的走神经流程时才
# 需要 DeepSeek 传输——纯离线 `run` 只是重放已保存的 candidate，而 deepseek
# 传输会直接拒绝非神经调用（`--provider deepseek requires neural extraction
# or formalization`），导致此前每一次离线 `main.py run` 都以退出码 2 失败。
# 因此 `run` 仅当带 neural_flags 之一（`--extract` / `--formalize-only`）时
# 注入；`batch` 恒为神经流程（其子进程固定带 `--extract`）。
#
# 追加（append）其一：官方 DeepSeek 传输的代理策略。环境里的 HTTPS_PROXY
# 指向一个不响应 HTTP CONNECT 的端口时，urllib 会隐式把请求交给它并立刻被
# 掐断，而报错只有 `DeepSeek network failure; details not saved`——完全看
# 不出是代理干的。因此默认直连；需要代理时显式传 `--deepseek-proxy
# environment`（沿用 *_proxy 变量）或一个 http(s):// URL。仅对
# `--provider deepseek` 有意义。
#
# 追加（append）其二：S12 acceptance-verdict policy。legacy = 历史行为
# （报告歧义 / 非断言实现否决该断言）；signals = 记为信息性字段，使正向判定
# 可达。verify 不注入，保持逐字节重放。
#
# 追加（append）其三：有界修复重试预算。直跑 `run` 的 argparse 默认是 0
# （offline 重放 run 不带 neural 标志，注入非零重试会触发 parser 的
# `--formal-retries requires neural formalization`），而 `batch` 一直给子进程
# 转发 1——两个入口行为不一致，第一次真实冒烟即暴露：同一报告在 batch 预算
# 下能经 field-scoped 修复转为候选，直跑却把可修复错误当终局。故对神经 run
# 注入与 batch 相同的预算；requires 门槛与目标脚本的 parser 守卫逐条对齐
# （`--formal-retries` 要 extract 或 formalize-only，`--element-retries` 只
# 认 `--extract`）。
STAGE2_ARG_DEFAULTS = {
    # command: (前置 flags,
    #           ((追加 flags, 冲突检测 flag, 需任一在场 flag（空=无条件）), ...),
    #           神经标志门槛)
    'run': (('--provider', 'deepseek'),
            ((('--deepseek-proxy', 'direct'), '--deepseek-proxy', ()),
             (('--claim-verdict', 'signals'), '--claim-verdict', ()),
             (('--formal-retries', '1'), '--formal-retries', ('--extract', '--formalize-only')),
             (('--element-retries', '1'), '--element-retries', ('--extract',)),
             # blind-batch_08 attribution: the readiness step had zero retry
             # budget from this entry (argparse default 0) while `batch` runs
             # defaulted to 1 -- a truncated screening response in a DeepSeek
             # outage window then killed an otherwise healthy run.  The budget
             # now matches `batch`.  Injection is skipped when the caller
             # overrides the transport (`--provider`) or sets the budget itself
             # (`--readiness-retries`): the child parser guards
             # "--readiness-retries requires DeepSeek full extraction", so a
             # non-deepseek provider owns its own budget, and an explicit
             # budget must win exactly like the other retry flags.
             (('--readiness-retries', '1'),
              ('--provider', '--readiness-retries'), ('--extract',))),
            ('--extract', '--formalize-only')),
    'batch': (('--provider', 'deepseek', '--model', 'deepseek-flash'),
              ((('--deepseek-proxy', 'direct'), '--deepseek-proxy', ()),
               (('--claim-verdict', 'signals'), '--claim-verdict', ())),
              ()),
}

STAGE2_ARG_PREFIX = {
    'verify': ('verify',),
}

# 不是入口、只作为库被调用的模块。列在这里是为了让分工显式可查。
LIBRARY_MODULES = {
    'semantic_core.py': 'P/I/V schema、类型、编译与基础校验',
    'plan_synthesizer.py': '形式计划校验与确定性 P/I/V 公式合成',
    'ingest.py': '原文片段编号、证据 ID 回填、提取前信息充分性门',
}


def _table(rows, indent='    '):
    if not rows:
        return ''
    width = max(len(name) for name, *_ in rows)
    return '\n'.join(f'{indent}{name.ljust(width)}  {description}'
                     for name, description, *_ in rows)


def _usage() -> str:
    stage2_rows = [(name, STAGE2_COMMANDS[name][1])
                   for name in STAGE2_COMMANDS]
    return (
        'SC_Slicer 唯一入口\n'
        '\n'
        '用法:\n'
        '    python main.py <command> [参数...]        # 阶段二 / 工程命令\n'
        '    python main.py stage2 <command> [参数...] # 同上，显式前缀写法\n'
        '\n'
        '阶段二全流程默认使用 DeepSeek（deepseek-flash）；阶段一请直接用 ./run.sh。\n'
        '\n'
        '工程命令（不调用模型）:\n'
        f'{_table(META_COMMANDS)}\n'
        '\n'
        '阶段二命令:\n'
        f'{_table(stage2_rows)}\n'
        '\n'
        '每个命令的参数原样转发给对应脚本；用 `python main.py <command> --help` 查看该命令自己的选项。\n'
        '相对路径按你调用 main.py 时的当前目录解析。\n'
        '阶段二目录: ' + str(STAGE2_DIR) + '\n')


def _registry():
    """Import prompts.registry without leaving the stage-2 directory on sys.path."""
    stage2 = str(STAGE2_DIR)
    inserted = stage2 not in sys.path
    if inserted:
        sys.path.insert(0, stage2)
    try:
        from prompts import registry  # type: ignore[import-not-found]
    finally:
        if inserted:
            sys.path.remove(stage2)
    return registry


def _script_path(script: str):
    """Locate a stage-2 script: cli/ first, then lib/, then the stage-2 root."""
    for directory in STAGE2_SCRIPT_DIRS:
        candidate = directory / script
        if candidate.is_file():
            return candidate
    return None


def _install_compat():
    """Register the legacy module-name aliases (lib/compat.py) for this process.

    Needed because cli/ and lib/ still import the pre-refactor module names
    (``from fidelity import ...``).  Lazy: the mapping is only resolved when a
    legacy name is actually imported.
    """
    from lib import compat          # needs the stage-2 root on sys.path
    compat.install()


def _delegate(script: str, argv):
    """Run a stage-2 script as __main__, preserving its exit code exactly."""
    path = _script_path(script)
    if path is None:
        searched = ', '.join(str(directory) for directory in STAGE2_SCRIPT_DIRS)
        print(f'missing stage-2 script: {script} (searched {searched})',
              file=sys.stderr)
        return 2
    previous_argv = sys.argv
    previous_path = list(sys.path)
    sys.argv = [str(path)] + list(argv)
    for directory in reversed(STAGE2_SCRIPT_DIRS):
        sys.path.insert(0, str(directory))
    try:
        _install_compat()
        runpy.run_path(str(path), run_name='__main__')
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(str(code), file=sys.stderr)
        return 1
    finally:
        sys.argv = previous_argv
        sys.path[:] = previous_path
    return 0


def _run_tests(argv):
    command = [sys.executable, '-m', 'unittest', 'discover',
               '-s', str(STAGE2_DIR / 'tests'),
               '-t', str(STAGE2_DIR), '-p', 'test_*.py', '-q']
    return subprocess.call(command + list(argv), cwd=str(ROOT))


def _versions(argv=()):
    if argv:
        print('versions takes no arguments', file=sys.stderr)
        return 2
    registry = _registry()
    print(f'默认版本        : {registry.DEFAULT_VERSION}')
    print(f'推荐稳定版      : {getattr(registry, "RECOMMENDED_VERSION", "(未登记)")}')
    print(f'实验版本        : {getattr(registry, "EXPERIMENTAL_VERSION", "(未登记)")}')
    live = getattr(registry, 'LIVE_VERSION', None)
    if live:
        print(f'活版本          : {live}（prompts/current.py，原地维护；运行目录快照保证重放）')
    print(f'已冻结版本({len(registry.VERSIONS)}): ' + ', '.join(registry.VERSIONS))
    print()
    print('功能开关（版本集合）:')
    for name in sorted(vars(registry)):
        value = getattr(registry, name)
        if name.endswith('_VERSIONS') and isinstance(value, frozenset):
            members = ', '.join(sorted(value)) if value else '(空)'
            print(f'  {name} = {members}')
    return 0


def _doctor(argv=()):
    if argv:
        print('doctor takes no arguments', file=sys.stderr)
        return 2
    checks = []

    def add(name, ok, detail):
        checks.append((name, bool(ok), detail))

    add('python >= 3.10', sys.version_info[:2] >= (3, 10), sys.version.split()[0])
    add('阶段二目录存在', STAGE2_DIR.is_dir(), str(STAGE2_DIR))
    add('cli/ 入口层存在', STAGE2_CLI_DIR.is_dir(), str(STAGE2_CLI_DIR))
    add('lib/ 共享库层存在', STAGE2_LIB_DIR.is_dir(), str(STAGE2_LIB_DIR))
    try:
        import z3  # type: ignore[import-not-found]
        add('z3 可用', True, z3.get_version_string())
    except Exception as exc:  # noqa: BLE001 - doctor reports, never raises
        add('z3 可用', False, type(exc).__name__)
    for script in sorted({script for script, _ in STAGE2_COMMANDS.values()}):
        if _script_path(script) is None:
            add(f'缺少脚本 {script}', False, '命令表与 cli/、lib/ 中均不存在')
    missing = [name for name in LIBRARY_MODULES if _script_path(name) is None]
    add('库模块齐备', not missing, ', '.join(missing) or 'ok')
    # 历史模块名兼容层（lib/compat.py）自检：14 个旧名字及其目标都必须可解析。
    # 这一条专门用来发现"某个入口忘了调用 compat.install()"。
    stage2 = str(STAGE2_DIR)
    inserted = stage2 not in sys.path
    if inserted:
        sys.path.insert(0, stage2)
    try:
        from lib import compat  # type: ignore[import-not-found]
        compat.install()
        unresolved = [f'{name}->{target}' for name, target in compat.ALIASES.items()
                      if importlib.util.find_spec(name) is None
                      or importlib.util.find_spec(target) is None]
        add(f'历史模块名兼容层({len(compat.ALIASES)} 个)',
            not unresolved, ', '.join(unresolved) if unresolved else 'ok')
    except Exception as exc:  # noqa: BLE001 - doctor reports, never raises
        add('历史模块名兼容层', False, f'{type(exc).__name__}: {exc}')
    finally:
        if inserted:
            sys.path.remove(stage2)
    tests_dir = STAGE2_DIR / 'tests'
    tests = sorted(tests_dir.glob('test_*.py')) if tests_dir.is_dir() else []
    add('测试文件存在', bool(tests), f'{len(tests)} 个文件')
    # 只检查存在性与权限，绝不读取内容。
    if STAGE2_ENV.is_file():
        mode = oct(STAGE2_ENV.stat().st_mode & 0o777)
        add('DeepSeek 私密配置存在', True, f'权限 {mode}（仅检查存在性，未读取内容）')
    else:
        add('DeepSeek 私密配置存在', False,
            f'未找到 {STAGE2_ENV}；真实模型调用需要它（示例见 '
            'config/stage2_deepseek.local.env.example）')

    for name, ok, detail in checks:
        print(f'[{"PASS" if ok else "FAIL"}] {name}: {detail}')
    failed = [name for name, ok, _ in checks if not ok]
    if failed:
        print(f'\n{len(failed)} 项未通过: ' + ', '.join(failed))
        return 1
    print('\n全部检查通过。')
    return 0


def _status(argv=()):
    if argv:
        print('status takes no arguments', file=sys.stderr)
        return 2
    registry = _registry()
    print(f'阶段二   : {STAGE2_DIR}')
    print(f'           推荐稳定版 {getattr(registry, "RECOMMENDED_VERSION", "(未登记)")}，'
          f'实验版本 {getattr(registry, "EXPERIMENTAL_VERSION", "(未登记)")}')
    print('阶段一   : 不在本入口内，请直接用 ./run.sh')
    print('阶段三   : 尚未实现，consistency_verdict 恒为 not_evaluated')
    print()
    print('权威状态文档（本命令不复制其内容，避免文档漂移）:')
    print('  HANDOFF.md')
    print('  tools/report_constraints_v2/README.md')
    print('  tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md')
    print('  tools/report_constraints_v2/STRUCTURE.md')
    return 0


def _frozen_paths():
    paths = set()
    for scope in FROZEN_SCOPES:
        for candidate in ROOT.glob(scope):
            if not candidate.is_file() or '__pycache__' in candidate.parts:
                continue
            paths.add(candidate.relative_to(ROOT).as_posix())
    return sorted(paths)


def _frozen(argv=()):
    write = False
    for argument in argv:
        if argument == '--write':
            write = True
        else:
            print(f'frozen: unknown argument {argument}', file=sys.stderr)
            return 2
    current = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
               for name in _frozen_paths()}
    if write:
        FROZEN_MANIFEST.write_text(
            json.dumps(current, indent=2, sort_keys=True) + '\n',
            encoding='utf-8')
        print(f'wrote {FROZEN_MANIFEST} ({len(current)} files)')
        return 0
    if not FROZEN_MANIFEST.is_file():
        print(f'missing manifest {FROZEN_MANIFEST}: run python main.py frozen --write',
              file=sys.stderr)
        return 1
    recorded = json.loads(FROZEN_MANIFEST.read_text(encoding='utf-8'))
    changed = sorted(p for p in set(recorded) & set(current) if recorded[p] != current[p])
    missing = sorted(set(recorded) - set(current))
    added = sorted(set(current) - set(recorded))
    for path in changed:
        print(f'[CHANGED] {path}')
    for path in missing:
        print(f'[MISSING] {path}')
    for path in added:
        print(f'[NEW]     {path}')
    if changed or missing or added:
        print(f'\n冻结资产清单共 {len(recorded)} 项：'
              f'{len(changed)} 改动 / {len(missing)} 缺失 / {len(added)} 新增。')
        print('冻结资产不得原地改写；确认是预期变更后再运行: python main.py frozen --write')
        return 1
    print(f'全部 {len(current)} 项冻结资产与 {FROZEN_MANIFEST.name} 一致。')
    return 0


META_HANDLERS = {
    'test': _run_tests,
    'versions': _versions,
    'doctor': _doctor,
    'status': _status,
    'frozen': _frozen,
}


def _with_arg_defaults(command, argv):
    """Apply STAGE2_ARG_DEFAULTS for ``command`` unless the caller set its own.

    Prepend the provider/model default unless the caller set provider/model
    itself (and, for ``run``, unless the invocation is actually neural — an
    offline replay keeps the caller's model-free transport).  Append the
    proxy/verdict defaults unconditionally and the retry-budget defaults only
    when their ``requires`` flags are present, each unless one of its
    ``conflict`` flags (a string or tuple of strings) is already set.
    """
    rule = STAGE2_ARG_DEFAULTS.get(command)
    if not rule:
        return list(argv)
    prepend, appends, neural_flags = rule
    argv = list(argv)
    if neural_flags and not any(flag in argv for flag in neural_flags):
        prepend = ()
    if set(prepend[::2]) & set(argv):
        prepend = ()
    full_argv = [*prepend, *argv]
    for flags, conflict, requires in appends:
        conflicts = conflict if isinstance(conflict, tuple) else (conflict,)
        if any(item in argv for item in conflicts):
            continue
        if requires and not any(flag in full_argv for flag in requires):
            continue
        full_argv = [*full_argv, *flags]
    return full_argv


def _dispatch(argv, prefix=''):
    """Resolve and run one command; ``prefix`` is only for error messages."""
    if not argv:
        print(_usage())
        return 0
    command, rest = argv[0], argv[1:]
    if command in ('-h', '--help', 'help'):
        print(_usage())
        return 0
    if command in META_HANDLERS:
        return META_HANDLERS[command](rest)
    if command in STAGE2_COMMANDS:
        prefix_args = STAGE2_ARG_PREFIX.get(command, ())
        return _delegate(STAGE2_COMMANDS[command][0],
                         [*prefix_args, *_with_arg_defaults(command, rest)])
    print(f'unknown {prefix}command: {command}', file=sys.stderr)
    print(_usage(), file=sys.stderr)
    return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'stage2':
        return _dispatch(argv[1:], prefix='stage2 ')
    return _dispatch(argv)


if __name__ == '__main__':
    raise SystemExit(main())
