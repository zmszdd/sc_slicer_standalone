#!/usr/bin/env python3
"""Generate the current stage-2 pipeline flowchart as an SVG.

Stdlib only (no rendering dependencies on this host); the SVG is rendered by
the viewer (VSCode webview / browser), which supplies CJK fonts.

Regenerate: python tools/report_constraints_v2/docs/gen_stage2_flow_svg.py
"""

from pathlib import Path

W, H = 1000, 1500
MX, MW = 250, 450          # main column x / width
BOX_H, PITCH = 70, 112     # main box height / row pitch
EX, EW = 730, 250          # exit column x / width
LX, LW = 20, 200           # repair-loop box x / width
FONT = ('Noto Sans CJK SC, PingFang SC, Microsoft YaHei, '
        'Hiragino Sans GB, sans-serif')

STYLE = {
    'local':  {'fill': '#F5F7FA', 'stroke': '#94A3B8'},
    'model':  {'fill': '#FFF7ED', 'stroke': '#F59E0B'},
    'final':  {'fill': '#DCFCE7', 'stroke': '#16A34A'},
    'reject': {'fill': '#FEE2E2', 'stroke': '#DC2626'},
    'abstain': {'fill': '#F1F5F9', 'stroke': '#64748B'},
    'dashed': {'fill': '#FFFFFF', 'stroke': '#94A3B8'},
}

MAIN = [
    ('① 载入与身份核对', ['report.json → extraction-input.txt · provenance.json（本地）'], 'local'),
    ('② 证据编号', ['evidence-catalog.json（本地）'], 'local'),
    ('③ 输入筛查', ['DeepSeek【模型调用 1】'], 'model'),
    ('④ P/I/V 要素提取', ['semantic-live 要素 prompt【模型调用 2】', '→ elements-ids.json'], 'model'),
    ('⑤ 机械归一化 + ⑥ 证据落地校验', ['门：未知证据 ID · schema · 角色隔离（本地）'], 'local'),
    ('⑦ 形式计划生成', ['semantic-live 形式 prompt【模型调用 3】', '→ formal-plan.json'], 'model'),
    ('⑧ 保真门检查', ['数值门（hex 修复 / assumption 豁免）· 地址门', '关系对齐 · P 来源本地化（本地）'], 'local'),
    ('⑩ 证据回填 + ⑪ 编译 P/I/V', ['⑫ 可观察性审查（本地）'], 'local'),
    ('⑬ Z3 求解', ['P∧V 可满足 · P∧V∧I 不可满足', '一致性层：P∧I 可满足（本地）'], 'local'),
    ('⑭ 自动分流', ['auto-triage：candidate / needs_review', '（--continue-on-review：次级缺失仅警告）'], 'local'),
    ('⑮ 阶段三交接', ['stage3-spec.json：形式约束 + 求解查询 + 产物哈希'], 'final'),
]

EXITS = [
    (2, '诚实弃权 exit 2', ['excluded_before_extraction', 'needs_input_review'], 'abstain'),
    (4, 'pipeline_failure', ['关键格式 / 证据错误'], 'reject'),
    (6, 'gate 拒绝', ['正确拦截 · 误伤 · 修复纪律失败'], 'reject'),
    (8, 'Z3 一致性拒绝', ['P∧I unsat（过度钉死）', 'P∧V 不可满足（P 自相矛盾）'], 'reject'),
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


def arrow(x1, y1, x2, y2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#475569" stroke-width="1.6" '
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
           '阶段二流程：漏洞报告 → P/I/V → 形式化约束 → 阶段三</text>',
           f'<text x="{W / 2}" y="60" font-size="12" fill="#64748B" '
           f'text-anchor="middle" font-family="{FONT}">'
           'semantic-live prompt · --formal-retries 1 · '
           '--continue-on-review · 单模型 DeepSeek</text>']

    legend = [('本地步骤', 'local'), ('模型调用', 'model'),
              ('拒绝 / 弃权出口', 'reject'), ('阶段三交接', 'final')]
    lx = 250
    for label, kind in legend:
        s = STYLE[kind]
        out.append(f'<rect x="{lx}" y="78" width="16" height="16" rx="3" '
                   f'fill="{s["fill"]}" stroke="{s["stroke"]}"/>')
        out.append(f'<text x="{lx + 22}" y="91" font-size="12" '
                   f'fill="#334155" font-family="{FONT}">{esc(label)}</text>')
        lx += 22 + len(label) * 12 + 40

    ys = [130 + i * PITCH for i in range(len(MAIN))]
    for i, (title, subs, kind) in enumerate(MAIN):
        out.append(box(MX, ys[i], MW, BOX_H, title, subs, kind))
        if i < len(MAIN) - 1:
            out.append(arrow(MX + MW / 2, ys[i] + BOX_H,
                             MX + MW / 2, ys[i + 1]))

    for row, title, subs, kind in EXITS:
        yc = ys[row] + BOX_H / 2
        out.append(box(EX, yc - 35, EW, 70, title, subs, kind,
                       title_size=13, sub_size=10))
        out.append(arrow(MX + MW, yc, EX - 4, yc))

    # ⑨ repair loop, left of ⑧ (row 6): forward defect → repair, back re-check.
    y6 = ys[6]
    yc = y6 + BOX_H / 2
    out.append(box(LX, yc - 45, LW, 90, '⑨ 受约束局部修复',
                   ['【模型调用 4】', '预算 = 1', 'no-change 反馈不可达（已披露）'],
                   'model', title_size=13, sub_size=10))
    out.append(arrow(MX, yc - 15, LX + LW + 4, yc - 15))
    out.append(arrow(LX + LW, yc + 25, MX - 4, yc + 25))
    out.append(f'<text x="{(MX + LX + LW) / 2}" y="{yc - 22}" font-size="10" '
               f'fill="#92400E" text-anchor="middle" font-family="{FONT}">'
               '缺陷可修复</text>')
    out.append(f'<text x="{(MX + LX + LW) / 2}" y="{yc + 43}" font-size="10" '
               f'fill="#92400E" text-anchor="middle" font-family="{FONT}">'
               '重检</text>')

    # Off-flow side panel.
    out.append(box(60, 1400, 880, 72, '流程外（不在 run 主链上）',
                   ['verify：零模型调用，prompt_snapshots 快照重放冻结 run（改动回归保险）',
                    '事后测评：两阶段盲金裁判 accuracy_gold_01（翻译保真测量）'],
                   'dashed', title_size=13, sub_size=11, dashed=True))

    out.append('</svg>')
    svg = '\n'.join(out)
    path = Path(__file__).with_name('stage2_flow.svg')
    path.write_text(svg)
    print(f'wrote {path} ({len(svg)} bytes)')


if __name__ == '__main__':
    main()
