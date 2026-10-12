#!/usr/bin/env python3
"""Generate the whole-pipeline overview flowchart as an SVG.

The highest-altitude chart: stage 1 (Rust slicing) and stage 2 (report ->
P/I/V) run in parallel, converge with the human binding map into the new-SC
single-file pipeline, and hand the four-branch verdict to stage 3.  Per-step
detail lives in stage2_flow.svg (stage-2 main chain) and new_sc_flow.svg
(new-SC internals); this one shows how the stages connect.

Stdlib only (no rendering dependencies on this host); the SVG is rendered by
the viewer (VSCode webview / browser), which supplies CJK fonts.

Regenerate: python tools/report_constraints_v2/docs/gen_pipeline_overview_svg.py
"""

from pathlib import Path

W, H = 1150, 1070
FONT = ('Noto Sans CJK SC, PingFang SC, Microsoft YaHei, '
        'Hiragino Sans GB, sans-serif')

STYLE = {
    'stage1':  {'fill': '#EFF6FF', 'stroke': '#3B82F6'},
    'stage2':  {'fill': '#FFF7ED', 'stroke': '#F59E0B'},
    'newsc':   {'fill': '#F0FDFA', 'stroke': '#14B8A6'},
    'stage3':  {'fill': '#DCFCE7', 'stroke': '#16A34A'},
    'input':   {'fill': '#FFFFFF', 'stroke': '#94A3B8'},
    'manual':  {'fill': '#EDE9FE', 'stroke': '#7C3AED'},
    'white':   {'fill': '#FFFFFF', 'stroke': '#94A3B8'},
    'model':   {'fill': '#FFFFFF', 'stroke': '#F59E0B'},
    'green':   {'fill': '#DCFCE7', 'stroke': '#16A34A'},
    'amber':   {'fill': '#FFFFFF', 'stroke': '#F59E0B'},
    'dashed':  {'fill': '#FFFFFF', 'stroke': '#94A3B8'},
}


def esc(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


def rect(x, y, w, h, kind, dashed=False, rx=8):
    s = STYLE[kind]
    dash = ' stroke-dasharray="6,4"' if dashed else ''
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{s["fill"]}" stroke="{s["stroke"]}" '
            f'stroke-width="1.5"{dash}/>')


def text(x, y, s, size=11, fill='#475569', weight=None, anchor='middle'):
    bold = f' font-weight="{weight}"' if weight else ''
    return (f'<text x="{x}" y="{y}" font-size="{size}"{bold} fill="{fill}" '
            f'text-anchor="{anchor}" font-family="{FONT}">{esc(s)}</text>')


def arrow(x1, y1, x2, y2, dashed=False):
    dash = ' stroke-dasharray="6,4"' if dashed else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#475569" stroke-width="1.6"{dash} '
            f'marker-end="url(#arr)"/>')


def panel(x, y, w, h, kind, title, chip):
    """Stage container: colored frame, title line, divider, right chip."""
    s = STYLE[kind]
    parts = [rect(x, y, w, h, kind),
             text(x + 18, y + 27, title, size=15, fill='#1E293B',
                  weight='600', anchor='start'),
             text(x + w - 16, y + 27, chip, size=10, fill=s['stroke'],
                  anchor='end'),
             f'<line x1="{x + 15}" y1="{y + 40}" x2="{x + w - 15}" '
             f'y2="{y + 40}" stroke="{s["stroke"]}" stroke-width="1" '
             f'stroke-dasharray="4,4" opacity="0.6"/>']
    return parts


def minibox(x, y, w, h, title, subs, kind='white', t_size=11, s_size=9):
    s = STYLE[kind]
    parts = [rect(x, y, w, h, kind, rx=6),
             text(x + w / 2, y + 20, title, size=t_size, fill='#1E293B',
                  weight='600')]
    for i, line in enumerate(subs):
        parts.append(text(x + w / 2, y + 36 + i * 13, line, size=s_size))
    return parts


def main():
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
           f'height="{H}" viewBox="0 0 {W} {H}">',
           '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
           'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#475569"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           text(W / 2, 34,
                'SC_Slicer 整体流程：阶段一 / 阶段二 → 新 SC 生成 → '
                '阶段三反馈闭环', size=20, fill='#0F172A', weight='700'),
           text(W / 2, 58,
                '报告→P/I/V（模型）与 PoC→切片（Rust）并行 · 三输入汇成'
                '单文件新 SC · forge 判读零模型 · 四分支闭环回阶段二/三',
                size=12, fill='#64748B')]

    legend = [('阶段一（冻结）', 'stage1'), ('阶段二（模型参与）', 'stage2'),
              ('新 SC（零模型）', 'newsc'), ('阶段三', 'stage3'),
              ('人工输入', 'manual'), ('诊断反馈（虚线）', 'dashed')]
    lx = 105
    for label, kind in legend:
        s = STYLE[kind]
        dashed = ' stroke-dasharray="4,3"' if kind == 'dashed' else ''
        out.append(f'<rect x="{lx}" y="76" width="14" height="14" rx="3" '
                   f'fill="{s["fill"]}" stroke="{s["stroke"]}"{dashed}/>')
        out.append(text(lx + 20, 88, label, size=11, fill='#334155',
                        anchor='start'))
        lx += 20 + len(label) * 11 + 30

    # ---- inputs (one corpus case: report + PoC share finding_uid) ----
    out.append(rect(70, 104, 470, 76, 'input', dashed=True))
    out.append(text(305, 130, '漏洞报告 report.json', size=14,
                    fill='#1E293B', weight='600'))
    out.append(text(305, 148, '自然语言安全主张（P/I/V 之源）', size=10))
    out.append(text(305, 163, '与 PoC 同属一个语料 case（finding_uid）',
                    size=10))
    out.append(rect(620, 104, 470, 76, 'input', dashed=True))
    out.append(text(855, 130, 'PoC 测试 + 合约仓库', size=14, fill='#1E293B',
                    weight='600'))
    out.append(text(855, 148, '目标合约 / 目标测试 / 目标变量', size=10))
    out.append(text(855, 163, 'verified_flatten_pass 冻结语料', size=10))
    out.append(arrow(305, 180, 305, 208))
    out.append(arrow(855, 180, 855, 208))

    # ---- stage 2 panel (left): report -> P/I/V ----
    out += panel(70, 208, 470, 210, 'stage2', '阶段二 · 报告 → P/I/V 形式化',
                 'DeepSeek×4 · 零人评')
    s2 = [('①要素提取', ['【模型】', 'elements-ids'], 'model'),
          ('②形式计划', ['【模型】', 'formal-plan'], 'model'),
          ('③保真门', ['数值·地址·关系', '（本地机械）'], 'white'),
          ('④Z3 求解+分流', ['constraints.json', '（本地引擎）'], 'white')]
    for i, (title, subs, kind) in enumerate(s2):
        out += minibox(85 + i * 110, 256, 100, 58, title, subs, kind)
        if i:
            out.append(arrow(85 + i * 110 - 10, 285, 85 + i * 110, 285))
    out.append(text(305, 344,
                    '提示词层 / 机械层 / 引擎三层分离（冻结 run 携带各自快照）',
                    size=10))
    out.append(text(305, 362, 'auto-triage：candidate / needs_review · 产物 = 冻结 run',
                    size=10))
    out.append(text(305, 380, 'verify：零模型离线重放（改动回归保险）', size=10))
    out.append(text(305, 398, '逐批留出盲测：prompt_live* · final_holdout*',
                    size=10))

    # ---- stage 1 panel (right): PoC -> slice ----
    out += panel(620, 208, 470, 210, 'stage1', '阶段一 · 代码切片（Rust run.sh）',
                 '冻结 · PROTECTED_HASHES')
    out += minibox(690, 256, 330, 58, '切片 contract.flattened.t.sol',
                   ['resurrect-v2 · aggressive-cleanup · --max-level 0',
                    '原 PoC 测试通过（冻结语料）'])
    out.append(text(855, 344, '输入：目标合约 / 测试 / 变量 → 最小自包含切片',
                    size=10))
    out.append(text(855, 362, '切片完整性由新 SC 的 forge 全量现场复证', size=10))
    out.append(text(855, 380, '阶段一与阶段三代码不改（保护层哈希守护）', size=10))
    out.append(text(855, 398, '语料：verified_flatten_pass_1568_exact_cases',
                    size=10))

    # ---- convergence into the new-SC panel ----
    out.append(arrow(305, 418, 305, 466))
    out.append(text(316, 444, 'constraints.json · formal-plan.json',
                    size=10, anchor='start'))
    out.append(arrow(855, 418, 855, 466))
    out.append(text(844, 444, '切片（逐字节前缀，只追加绝不编辑）',
                    size=10, anchor='end'))

    # ---- new-SC panel (center, the star) ----
    out += panel(230, 470, 640, 250, 'newsc',
                 '新 SC 生成（new_sc.py 单文件管线）',
                 '零模型调用 · 判读表预注册')
    g = [('来源对齐门 + 绑定 schema 门',
          ['四项 sha256 来源对齐', '类型/单位/覆盖 fail-fast']),
         ('合并：切片前缀 + 追加 guard',
          ['表达式与 constraints.json', '逐字节一致 · 绝不重推']),
         ('forge 全量执行',
          ['PoC PASS = 切片完整性', '输出 STAGE2_VERDICT {p,i,v}'])]
    for i, (title, subs) in enumerate(g):
        out += minibox(250 + i * 207, 518, 186, 60, title, subs)
        if i:
            out.append(arrow(250 + i * 207 - 21, 548, 250 + i * 207, 548))
    verdicts = [('violation_reproduced', 'p∧¬i∧v · 代码层证实', 'green'),
                ('i_too_weak', 'p∧i∧v · I 未违反', 'amber'),
                ('precondition_mismatch', '¬p · P 与 PoC 不符', 'amber'),
                ('violation_not_observed', 'p∧¬v · V 未见', 'amber')]
    for j, (title, sub, kind) in enumerate(verdicts):
        out += minibox(250 + j * 154, 600, 138, 48, title, [sub], kind,
                       t_size=9, s_size=8)
        out.append(arrow(757, 578, 319 + j * 154, 600))
    out.append(text(550, 668, '逐案例落盘：verdict__<case> · forge 日志 · '
                    'ingest 留档（不同拒写 · 相同幂等）', size=10))

    # ---- human binding input (right of the new-SC panel) ----
    out.append(rect(900, 560, 190, 90, 'manual'))
    out.append(text(995, 586, '绑定映射（人工）', size=13, fill='#1E293B',
                    weight='600'))
    out.append(text(995, 604, 'bindings/<case>.json', size=9))
    out.append(text(995, 618, '唯一人工输入（人只填 TODO）', size=9))
    out.append(text(995, 632, '--template 预填 + schema 门校验', size=9))
    out.append(arrow(900, 605, 872, 605))

    # ---- new SC -> stage 3 ----
    out.append(arrow(550, 720, 550, 766))
    out.append(text(560, 746, '四分支裁决 + stage3_feedback__<case>.json',
                    size=10, anchor='start'))

    # ---- stage 3 panel ----
    out += panel(230, 766, 640, 140, 'stage3',
                 '阶段三 · 一致性验证与复活（sol_resurrect）', '反馈闭环')
    out.append(text(550, 800, 'stage3-feedback ingest（只写 run 副本）→ '
                    'stage3-consistency.json', size=10))
    out.append(text(550, 818, 'consistency_verdict 与四分支同向校验 · '
                    'violation 系不一致即 fail', size=10))
    out.append(text(550, 836, '主交接：stage3-spec.json（阶段二 run 直达，'
                    '见左侧箭头）', size=10))
    out.append(text(550, 854, '阶段三本体（验证 / 复活回路）在此之后接手',
                    size=10))
    out.append(text(550, 876, '裁决证据回流：喂下一轮 prompt 泛化与自动绑定',
                    size=10, fill='#166534'))

    # ---- stage 2 -> stage 3 direct handoff (far-left elbow) ----
    out.append(f'<path d="M 70 313 L 34 313 L 34 836 L 228 836" '
               f'fill="none" stroke="#475569" stroke-width="1.6" '
               f'marker-end="url(#arr)"/>')
    out.append(text(129, 826, 'stage3-spec.json（主交接）', size=10))

    # ---- diagnostic feedback loop (dashed, new SC -> stage 2) ----
    out.append(f'<path d="M 230 655 L 160 655 L 160 420" fill="none" '
               f'stroke="#475569" stroke-width="1.6" '
               f'stroke-dasharray="6,4" marker-end="url(#arr)"/>')
    out.append(text(105, 528, '诊断反馈（虚线）', size=9, fill='#92400E'))
    out.append(text(105, 542, '三诊断分支 → 阶段二', size=9, fill='#92400E'))

    # ---- off-flow discipline panel ----
    out.append(rect(70, 950, 1010, 100, 'dashed', dashed=True))
    out.append(text(575, 976, '流程外与纪律（不在单案例主链上）', size=13,
                    fill='#1E293B', weight='600'))
    out.append(text(575, 996, '冻结纪律：run 冻结永不改写（新 SC ingest 只写'
                    '副本）· 判读表预注册于 README · 阶段一/三代码不动',
                    size=11))
    out.append(text(575, 1014, '回归保险：阶段二 verify 零模型重放 · 翻译器 / '
                    'schema 门 / 四分支表单元测试钉死', size=11))
    out.append(text(575, 1032, '测评：accuracy_gold_01 两阶段盲金裁判（翻译保真）'
                    '· 批判读 --all 逐案例隔离汇总', size=11))

    out.append('</svg>')
    svg = '\n'.join(out)
    path = Path(__file__).with_name('pipeline_overview.svg')
    path.write_text(svg)
    print(f'wrote {path} ({len(svg)} bytes)')


if __name__ == '__main__':
    main()
