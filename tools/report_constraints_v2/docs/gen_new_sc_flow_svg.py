#!/usr/bin/env python3
"""Generate the new-SC injection pipeline flowchart as an SVG.

Companion to gen_stage2_flow_svg.py: that chart ends at the stage-2 run
(stage3-spec.json); this one starts there and follows the new-SC single-file
pipeline (evaluation/new_sc_injection_02/new_sc.py) through merge -> forge ->
four-branch adjudication -> stage-3 ingest.

Stdlib only (no rendering dependencies on this host); the SVG is rendered by
the viewer (VSCode webview / browser), which supplies CJK fonts.

Regenerate: python tools/report_constraints_v2/docs/gen_new_sc_flow_svg.py
"""

from pathlib import Path

W, H = 1000, 1130
MX, MW = 275, 450          # main column x / width
BOX_H, PITCH = 84, 110     # main box height / row pitch
EX, EW = 760, 230          # right column (gate exits / verdict branches)
LX, LW = 20, 200           # left column
FONT = ('Noto Sans CJK SC, PingFang SC, Microsoft YaHei, '
        'Hiragino Sans GB, sans-serif')

STYLE = {
    'input':   {'fill': '#EFF6FF', 'stroke': '#3B82F6'},
    'local':   {'fill': '#F5F7FA', 'stroke': '#94A3B8'},
    'manual':  {'fill': '#EDE9FE', 'stroke': '#7C3AED'},
    'verdict': {'fill': '#FFF7ED', 'stroke': '#F59E0B'},
    'final':   {'fill': '#DCFCE7', 'stroke': '#16A34A'},
    'reject':  {'fill': '#FEE2E2', 'stroke': '#DC2626'},
    'dashed':  {'fill': '#FFFFFF', 'stroke': '#94A3B8'},
}

INPUTS = [
    (20, '阶段二 run（见 stage2_flow.svg）',
     ['constraints.json：P/I/V 表达式', '与 Z3 查询同源 · formal-plan.json',
      'provenance.json（身份核对用）'], 'input'),
    (350, '阶段一切片 · resurrect-v2',
     ['run.sh · 语料 verified_flatten_pass', 'contract.flattened.t.sol',
      '原 PoC 测试通过（冻结语料）'], 'input'),
    (680, '绑定映射 bindings/<case>.json',
     ['唯一人工输入 · --template 预填骨架', '每符号：phase/type/expr/unit/desc',
      '（人只填 TODO，交 schema 门校验）'], 'manual'),
]

MAIN = [
    ('⓪ 来源对齐门（写任何文件之前）',
     ['provenance case_id == case_key · report_path 指向语料 case 目录',
      'report.json sha256 · 切片 declared_code_sha256（任一不符即拒）'],
     'local'),
    ('① 绑定 schema 门 + 覆盖校验',
     ['九顶层键 · 每符号五行（phase/type/expr/unit/desc）精确齐全',
      'type/unit 匹配 formal-plan · 数值换算显式写进 expr',
      'P/I/V 引用符号 ⊆ 绑定映射且无多余（fail-fast）'],
     'local'),
    ('② 合并成单文件新 SC',
     ['new_sc.t.sol = 切片逐字节前缀（只追加绝不编辑）+ 追加 guard',
      'P/I/V 表达式与 constraints.json 逐字节一致，绝不重推',
      'pre 相位符号攻击前快照 <name>__pre（强制语义）'],
     'local'),
    ('③ forge 全量执行',
     ['原 PoC 测试 PASS = 切片完整性现场验证',
      'guard 输出唯一一行 STAGE2_VERDICT {"p":..,"i":..,"v":..}'],
     'local'),
    ('④ 四分支判读（预注册表，运行前冻结）',
     ['guard 只在绑定不可能时硬失败——I 被违反是预期的好消息'],
     'local'),
    ('⑤ 阶段三 ingest（只写 run 副本，冻结 run 永不改写）',
     ['run_copy__<case> · stage3_feedback__<case>.json',
      '→ stage3-feedback 通路 · consistency_verdict 同向校验',
      '（violation 系裁决与 ingest 不一致即 fail）'],
     'local'),
    ('⑥ 判读与证据落盘（逐案例命名，后跑不覆盖先跑）',
     ['verdict__<case>.json · forge__<case>.log',
      'stage3-consistency__<case>.json（不同拒写 · 相同幂等 no-op）',
      '--all 批判读汇总 adjudication_summary__<batch>.json'],
     'final'),
]

EXITS = [
    (0, '来源对齐拒绝 fail-fast',
     ['case_id / report_path / sha256 任一不符', '（01 原型手选错误的机械化）'],
     'reject'),
    (1, '绑定 schema / 覆盖拒绝',
     ['类型/单位错配曾产出自信但', '错误的裁决 → 现在写文件前拒绝'],
     'reject'),
]

BRANCHES = [
    ('violation_reproduced', 'p∧¬i∧v · 报告主张代码层机械证实', 'final'),
    ('i_too_weak', 'p∧i∧v · I 应违反而未违反 → I 或绑定错', 'verdict'),
    ('precondition_mismatch', '¬p · 阶段二 P 与 PoC 现实不符', 'verdict'),
    ('violation_not_observed', 'p∧¬v · V 观察量未见 → 绑定错', 'verdict'),
]


def esc(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


def box(x, y, w, h, title, subs, kind, title_size=15, sub_size=11,
        dashed=False):
    s = STYLE[kind]
    dash = ' stroke-dasharray="6,4"' if dashed else ''
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{s["fill"]}" stroke="{s["stroke"]}" stroke-width="1.5"{dash}/>',
        f'<text x="{x + w / 2}" y="{y + 26}" font-size="{title_size}" '
        f'font-weight="600" fill="#1E293B" text-anchor="middle" '
        f'font-family="{FONT}">{esc(title)}</text>',
    ]
    for i, line in enumerate(subs):
        parts.append(
            f'<text x="{x + w / 2}" y="{y + 45 + i * 15}" '
            f'font-size="{sub_size}" fill="#475569" text-anchor="middle" '
            f'font-family="{FONT}">{esc(line)}</text>')
    return '\n'.join(parts)


def arrow(x1, y1, x2, y2, dashed=False):
    dash = ' stroke-dasharray="6,4"' if dashed else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#475569" stroke-width="1.6"{dash} '
            f'marker-end="url(#arr)"/>')


def main():
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
           f'height="{H}" viewBox="0 0 {W} {H}">',
           '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
           'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="{W / 2}" y="38" font-size="21" font-weight="700" '
           f'fill="#0F172A" text-anchor="middle" font-family="{FONT}">'
           '新 SC 生成流程：P/I/V 约束 + 阶一切片 → 单文件新 SC → '
           'forge → 四分支判读 → 阶段三</text>',
           f'<text x="{W / 2}" y="60" font-size="12" fill="#64748B" '
           f'text-anchor="middle" font-family="{FONT}">'
           'new_sc.py 单文件管线（evaluation/new_sc_injection_02）· '
           '一条命令合并→执行→判读→ingest · 零模型调用</text>',
           f'<text x="{W / 2}" y="78" font-size="12" fill="#64748B" '
           f'text-anchor="middle" font-family="{FONT}">'
           'new_sc.py &lt;case_key&gt; · --all --batch &lt;批次&gt; · '
           '--template &lt;case_key&gt;（语料根可用 STAGE2_CORPUS 覆盖）</text>']

    legend = [('上游产物', 'input'), ('人工输入', 'manual'), ('本地机械步骤', 'local'),
              ('判读分支', 'verdict'), ('拒绝出口', 'reject'), ('阶段三交接', 'final')]
    lx = 130
    for label, kind in legend:
        s = STYLE[kind]
        out.append(f'<rect x="{lx}" y="92" width="16" height="16" rx="3" '
                   f'fill="{s["fill"]}" stroke="{s["stroke"]}"/>')
        out.append(f'<text x="{lx + 22}" y="105" font-size="12" '
                   f'fill="#334155" font-family="{FONT}">{esc(label)}</text>')
        lx += 22 + len(label) * 12 + 40

    # Three upstream inputs converge into gate ⓪.
    for x, title, subs, kind in INPUTS:
        out.append(box(x, 120, 300, 96, title, subs, kind))
    out.append(arrow(170, 216, 430, 236))
    out.append(arrow(500, 216, 500, 236))
    out.append(arrow(830, 216, 570, 236))

    ys = [240 + i * PITCH for i in range(len(MAIN))]
    for i, (title, subs, kind) in enumerate(MAIN):
        out.append(box(MX, ys[i], MW, BOX_H, title, subs, kind))
        if i < len(MAIN) - 1:
            out.append(arrow(MX + MW / 2, ys[i] + BOX_H,
                             MX + MW / 2, ys[i + 1]))

    for row, title, subs, kind in EXITS:
        yc = ys[row] + BOX_H / 2
        out.append(box(EX, yc - 35, EW, 70, title, subs, kind,
                       title_size=13, sub_size=10))
        out.append(arrow(MX + MW, yc, EX - 6, yc))

    # Four pre-registered verdict branches fan out from ④ (row 4).
    y4 = ys[4]
    for j, (title, sub, kind) in enumerate(BRANCHES):
        by = 560 + j * 66
        out.append(box(EX, by, EW, 60, title, [sub], kind,
                       title_size=13, sub_size=10))
        out.append(arrow(MX + MW, y4 + BOX_H / 2, EX - 6, by + 30))
    out.append(f'<text x="{EX + EW / 2}" y="548" font-size="11" '
               f'fill="#92400E" text-anchor="middle" font-family="{FONT}">'
               'guard 唯一输出 STAGE2_VERDICT → 查预注册表</text>')

    # Left column: forge-execution rejection (row 3) and the discipline panel.
    y3 = ys[3]
    yc = y3 + BOX_H / 2
    out.append(box(LX, yc - 38, LW, 76, '执行拒绝',
                   ['PoC 测试未 PASS（切片完整性）', '无 STAGE2_VERDICT 行'],
                   'reject', title_size=13, sub_size=10))
    out.append(arrow(MX, yc, LX + LW + 4, yc))
    out.append(box(LX, 795, LW, 160, '预注册与健全性',
                   ['判读表运行前冻结于 README', '绑定健全性断言记录 PoC',
                    '实际观察量（Merkl：bal=1980', '＜2000 资不抵债在案）',
                    'P 常量 vs PoC 场景的对齐', '由四分支机械分辨'],
                   'dashed', title_size=13, sub_size=10, dashed=True))

    # Off-flow side panel.
    out.append(box(60, 1010, 880, 100, '流程外（不在单案例主链上）',
                   ['单元测试钉死：翻译器 / 绑定 schema / 四分支表'
                    '（test_new_sc_injection.py 17 例 · RealBindingsConformTests 守护入库绑定）',
                    '语义单源：算子词汇表 lib/dsl.py 与 Z3 后端共享 · '
                    'p/i/v→查询映射与判读端同文件（stage3_consistency.queries_from_piv）',
                    '批模式：逐案例 CaseError 隔离，缺绑定如实报错绝不静默跳过'
                    '（批判读入口即 --all --batch）'],
                   'dashed', title_size=13, sub_size=11, dashed=True))

    out.append('</svg>')
    svg = '\n'.join(out)
    path = Path(__file__).with_name('new_sc_flow.svg')
    path.write_text(svg)
    print(f'wrote {path} ({len(svg)} bytes)')


if __name__ == '__main__':
    main()
