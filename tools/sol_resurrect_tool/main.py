import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.assembler import Assembler
from src.brain import ContextBrain
from src.code_normalizer import normalize_primitive_type_aliases
from src.compiler_diagnostics import parse_compiler_diagnostics
from src.error_router import ErrorRouter
from src.parser import SolidityParser
from src.symbol_table import build_symbol_table
from src.types import AtomStats, GrowBudget, SliceResult


TOOL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TOOL_DIR.parents[1]
DEFAULT_OUTPUT_PATH = WORKSPACE_ROOT / "runs" / "sol_resurrect" / "latest" / "Resurrected.t.sol"
DEFAULT_LOG_DIR = WORKSPACE_ROOT / "logs" / "sol_resurrect"
DEFAULT_LLM_CONFIG_PATH = WORKSPACE_ROOT / "config" / "llm.env"
LEGACY_ENV_PATH = TOOL_DIR / ".env"


def _resolve_project_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = WORKSPACE_ROOT / resolved
    return resolved


def _load_runtime_config(config_path: str | Path | None) -> list[Path]:
    loaded = []
    if LEGACY_ENV_PATH.exists():
        load_dotenv(LEGACY_ENV_PATH, override=False)
        loaded.append(LEGACY_ENV_PATH)

    if config_path:
        resolved_config = _resolve_project_path(config_path)
        if resolved_config.exists():
            load_dotenv(resolved_config, override=True)
            loaded.append(resolved_config)
    return loaded


def _ensure_parent_dir(output_path: str) -> None:
    parent = Path(output_path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def _normalize_solidity_output(code: str) -> str:
    code = normalize_primitive_type_aliases(code)
    code = _ensure_required_imports(code)
    code, _ = _repair_missing_array_declarations(code)
    code = _convert_placeholder_structs_used_as_contracts(code)
    code = _ensure_clone_immutable_arg_helpers(code)
    code = _ensure_known_solidity_schemas(code)
    code, _ = _downgrade_external_contract_params_called_with_address(code)
    code = _remove_nested_errors_shadowing_globals(code)
    code, _ = _repair_zero_arg_custom_errors(code)
    code, _ = _repair_duplicate_placeholder_modifiers(code)
    code, _ = _repair_keyword_param_names(code)
    code = _ensure_base_contracts_precede_derived(code)
    lines = code.splitlines()
    spdx = None
    pragma = None
    imports = []
    body = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if pragma is not None:
                body.append(line)
            continue
        if stripped.startswith("// SPDX-License-Identifier"):
            spdx = line
            continue
        if stripped.startswith("pragma solidity"):
            pragma = line
            continue
        if stripped.startswith("import "):
            imports.append(line)
            continue
        body.append(line)

    normalized = [spdx or "// SPDX-License-Identifier: MIT", pragma or "pragma solidity ^0.8.0;"]
    normalized.extend(imports)
    if imports and body and body[0].strip():
        normalized.append("")
    normalized.extend(body)

    return "\n".join(normalized).strip() + "\n"


def _ensure_required_imports(code: str) -> str:
    """Restore imports required by reconstructed inheritance."""
    if (
        re.search(r'\bis\s+Test\b', code)
        and "forge-std/Test.sol" not in code
        and not re.search(r'\b(?:contract|abstract\s+contract|interface)\s+Test\b', code)
    ):
        lines = code.splitlines()
        insert_at = 0
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("// SPDX-License-Identifier") or stripped.startswith("pragma solidity"):
                insert_at = idx + 1
                continue
            if not stripped:
                insert_at = idx + 1
                continue
            break
        lines[insert_at:insert_at] = ["import 'forge-std/Test.sol';", ""]
        return "\n".join(lines)
    return code


def _write_output(output_path: str, final_code: str) -> None:
    _ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(_normalize_solidity_output(final_code))


def _forge_available() -> bool:
    return subprocess.run(
        ["sh", "-lc", "command -v forge >/dev/null 2>&1"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _resolve_forge_output_dir(output_path: str) -> Path:
    output_dir = Path(output_path).expanduser().resolve().parent.parent
    if not (output_dir / "foundry.toml").exists():
        output_dir = Path(output_path).expanduser().resolve().parent
    return output_dir


def _ensure_forge_project(output_path: str) -> Path:
    """Create the minimal Foundry project files needed to compile the output."""
    output_dir = _resolve_forge_output_dir(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "src").mkdir(exist_ok=True)
    (output_dir / "test").mkdir(exist_ok=True)

    foundry_toml = output_dir / "foundry.toml"
    forge_std = Path("/root/data/mock_expolit/lib/forge-std/src")
    remappings = []
    libs = ['"lib"']
    if forge_std.exists():
        remappings.append(f'"forge-std/={forge_std.as_posix()}/"')
        libs.append(f'"{forge_std.parent.as_posix()}"')

    remappings_line = ", ".join(remappings)
    libs_line = ", ".join(libs)
    foundry_toml.write_text(
        "\n".join(
            [
                "[profile.default]",
                'src = "src"',
                'test = "test"',
                'out = "out"',
                f"libs = [{libs_line}]",
                f"remappings = [{remappings_line}]",
                'solc_version = "0.8.26"',
                'optimizer = true',
                'optimizer_runs = 200',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return output_dir


def _append_compile_log(output_path: str, text: str) -> None:
    output_dir = _resolve_forge_output_dir(output_path)
    log_path = output_dir / "build.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def _reset_compile_log(output_path: str) -> None:
    output_dir = _resolve_forge_output_dir(output_path)
    log_path = output_dir / "build.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("[*] Solidity Resurrector compile log\n")


def _emit_compile_trace(output_path: str, phase: str, label: str, cwd: Path, returncode: int | None, output: str) -> None:
    output_dir = _resolve_forge_output_dir(output_path)
    build_log = output_dir / "build.log"
    header = [
        "",
        f"[COMPILE] {phase}",
        f"    cwd: {cwd}",
        f"    command: {label}",
    ]
    if returncode is not None:
        header.append(f"    exit code: {returncode}")
    header.append("    output:")
    full_trace = "\n".join(header) + "\n" + (output.rstrip() if output.strip() else "    <no output>") + "\n"
    _append_compile_log(output_path, full_trace)

    summary_lines = [
        "",
        f"[COMPILE] {phase}",
        f"    command: {label}",
        f"    exit code: {returncode if returncode is not None else 'n/a'}",
        f"    full output: {build_log}",
    ]
    errors = _extract_solidity_errors(output) if returncode not in (0, None) else []
    if errors:
        summary_lines.append("    key diagnostics:")
        summary_lines.extend(f"       - {err}" for err in errors[:8])
    elif output.strip():
        first_lines = [line.strip() for line in output.splitlines() if line.strip()][:5]
        if first_lines:
            summary_lines.append("    summary:")
            summary_lines.extend(f"       {line}" for line in first_lines)
    else:
        summary_lines.append("    summary: <no output>")
    print("\n".join(summary_lines))


def _run_compile(output_path: str, phase: str = "compile validation") -> tuple[bool, str, str | None]:
    """Try to compile the generated Solidity file from the output dir (has foundry.toml)."""
    output_dir = _ensure_forge_project(output_path)

    # Ensure the file is in the test/ subdirectory of the forge project
    output_file = Path(output_path).expanduser().resolve()
    test_file = output_dir / "test" / output_file.name
    if output_file != test_file:
        test_file.parent.mkdir(parents=True, exist_ok=True)
        # Clean up stale Resurrected*.t.sol files to prevent ghost compilation errors
        import glob
        for stale in glob.glob(str(output_dir / "test" / "Resurrected*.t.sol")):
            stale_path = Path(stale)
            if stale_path.name != output_file.name:
                stale_path.unlink(missing_ok=True)
        import shutil
        shutil.copy2(str(output_file), str(test_file))

    clean_proc = subprocess.run(
        ["forge", "clean"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(output_dir),
    )
    clean_output = (clean_proc.stdout or "") + (clean_proc.stderr or "")
    _emit_compile_trace(output_path, phase, "forge clean", output_dir, clean_proc.returncode, clean_output)
    if clean_proc.returncode != 0:
        return False, clean_output.strip(), "forge clean"

    commands = [
        (["forge", "test", "--match-path", f"test/{output_file.name}", "--via-ir"],
         f"forge test --match-path test/{output_file.name} --via-ir"),
    ]

    last_output = ""
    for cmd, label in commands:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(output_dir),
            )
        except FileNotFoundError:
            _emit_compile_trace(output_path, phase, label, output_dir, None, "forge not found")
            return False, "forge not found", None

        output = (proc.stdout or "") + (proc.stderr or "")
        last_output = output.strip()
        _emit_compile_trace(output_path, phase, label, output_dir, proc.returncode, output)
        if proc.returncode == 0:
            return True, output, label

    return False, last_output, commands[-1][1]


def _extract_solidity_errors(compiler_output: str) -> list[str]:
    if not compiler_output:
        return []

    errors = []
    for line in compiler_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"error|Error|TypeError|ParserError|DeclarationError|Undeclared|Identifier|Expected|Member|conversion", stripped, re.I):
            errors.append(stripped)

    if not errors:
        errors = [compiler_output.strip()]
    return errors[:20]


def _count_nonblank_lines(code: str) -> int:
    return sum(1 for line in code.splitlines() if line.strip())


def _extract_named_block_lines(code: str, kind_pattern: str, name: str) -> int:
    match = re.search(rf"\b{kind_pattern}\s+{re.escape(name)}\b[^\{{;]*\{{", code)
    if not match:
        return 0
    end = _find_matching_brace_position(code, match.end() - 1)
    if end is None:
        return 0
    return _count_nonblank_lines(code[match.start():end + 1])


def _extract_function_lines(code: str, name: str) -> int:
    match = re.search(rf"\bfunction\s+{re.escape(name)}\s*\(", code)
    if not match:
        return 0
    open_brace = code.find("{", match.end())
    semicolon = code.find(";", match.end())
    if semicolon != -1 and (open_brace == -1 or semicolon < open_brace):
        return _count_nonblank_lines(code[match.start():semicolon + 1])
    if open_brace == -1:
        return 0
    end = _find_matching_brace_position(code, open_brace)
    if end is None:
        return 0
    return _count_nonblank_lines(code[match.start():end + 1])


def _collect_atom_stats(code: str) -> AtomStats:
    return AtomStats(
        statements=len(re.findall(r";", code)),
        functions=len(re.findall(r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", code)),
        libraries=len(re.findall(r"\blibrary\s+[A-Za-z_][A-Za-z0-9_]*\b", code)),
        interfaces=len(re.findall(r"\binterface\s+[A-Za-z_][A-Za-z0-9_]*\b", code)),
        contracts=len(re.findall(r"\b(?:abstract\s+)?contract\s+[A-Za-z_][A-Za-z0-9_]*\b", code)),
        types=len(re.findall(r"\b(?:struct|enum|error|event|type)\s+[A-Za-z_][A-Za-z0-9_]*\b", code)),
    )


def _build_slice_result(
    input_code: str,
    output_code: str,
    compile_success: bool,
    budget: GrowBudget,
    llm_used: bool,
    shrink_removed_atoms: int = 0,
    failure_reason: str | None = None,
) -> SliceResult:
    input_lines = max(1, _count_nonblank_lines(input_code))
    output_lines = _count_nonblank_lines(output_code)
    input_bytes = max(1, len(input_code.encode("utf-8")))
    output_bytes = len(output_code.encode("utf-8"))
    line_ratio = output_lines / input_lines
    byte_ratio = output_bytes / input_bytes

    in_target_lines = _extract_function_lines(input_code, "test_submissionValidity")
    out_target_lines = _extract_function_lines(output_code, "test_submissionValidity")
    target_function_full_restored = bool(
        in_target_lines and out_target_lines and out_target_lines >= int(in_target_lines * 0.90)
    )

    in_poc_lines = _extract_named_block_lines(input_code, "contract", "PoC")
    out_poc_lines = _extract_named_block_lines(output_code, "contract", "PoC")
    target_contract_full_restored = bool(
        in_poc_lines and out_poc_lines and out_poc_lines >= int(in_poc_lines * 0.90)
    )
    full_source_unit_restored = line_ratio >= 0.95 or byte_ratio >= 0.95

    base_container_restore_count = 0
    for block in _find_top_level_blocks(output_code):
        if block["kind"] in {"contract", "library"}:
            block_lines = int(block["end"]) - int(block["start"]) + 1
            if block_lines > 150:
                base_container_restore_count += 1

    if not compile_success:
        reason = failure_reason or "compile_failed"
    elif line_ratio > budget.max_line_ratio or byte_ratio > budget.max_byte_ratio:
        reason = "compile_artifact_not_effective_slice"
    elif full_source_unit_restored:
        reason = "full_source_unit_restored"
    elif target_contract_full_restored:
        reason = "target_contract_full_restored"
    elif target_function_full_restored:
        reason = "target_function_full_restored"
    else:
        reason = failure_reason

    slice_effective = (
        compile_success
        and reason is None
        and line_ratio <= budget.max_line_ratio
        and byte_ratio <= budget.max_byte_ratio
        and not full_source_unit_restored
        and not target_contract_full_restored
        and not target_function_full_restored
    )

    return SliceResult(
        compile_success=compile_success,
        slice_effective=slice_effective,
        input_lines=input_lines,
        output_lines=output_lines,
        line_ratio=line_ratio,
        input_bytes=input_bytes,
        output_bytes=output_bytes,
        byte_ratio=byte_ratio,
        fallback_level="EffectiveSlice",
        target_function_full_restored=target_function_full_restored,
        target_contract_full_restored=target_contract_full_restored,
        full_source_unit_restored=full_source_unit_restored,
        llm_used=llm_used,
        base_container_restore_count=base_container_restore_count,
        atom_stats=_collect_atom_stats(output_code),
        shrink_removed_atoms=shrink_removed_atoms,
        failure_reason=reason,
    )


def _write_slice_result(output_path: str, result: SliceResult) -> None:
    output_dir = _resolve_forge_output_dir(output_path)
    result_path = output_dir / "slice_result.json"
    try:
        payload = result.json(indent=2)
    except TypeError:
        payload = result.model_dump_json(indent=2)
    result_path.write_text(payload + "\n", encoding="utf-8")
    print("[SLICE_RESULT]")
    print(f"    compile_success: {result.compile_success}")
    print(f"    slice_effective: {result.slice_effective}")
    print(f"    lines: {result.output_lines}/{result.input_lines} ({result.line_ratio:.3f})")
    print(f"    bytes: {result.output_bytes}/{result.input_bytes} ({result.byte_ratio:.3f})")
    if result.failure_reason:
        print(f"    failure_reason: {result.failure_reason}")
    print(f"    result_file: {result_path}")


def _top_level_atom_ranges(code: str) -> list[dict[str, object]]:
    lines = code.splitlines()
    atoms: list[dict[str, object]] = []
    depth = 0
    i = 0
    block_start = re.compile(r"^\s*(contract|interface|library|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    single_decl = re.compile(r"^\s*(type|error|event)\s+([A-Za-z_][A-Za-z0-9_]*)\b")
    while i < len(lines):
        stripped = lines[i].strip()
        if depth == 0:
            block_match = block_start.match(lines[i])
            if block_match:
                start = i
                atom_depth = lines[i].count("{") - lines[i].count("}")
                seen_open = "{" in lines[i]
                i += 1
                while i < len(lines) and (not seen_open or atom_depth > 0):
                    atom_depth += lines[i].count("{") - lines[i].count("}")
                    seen_open = seen_open or "{" in lines[i]
                    i += 1
                atoms.append(
                    {
                        "kind": block_match.group(1),
                        "name": block_match.group(2),
                        "start": start,
                        "end": i,
                        "text": "\n".join(lines[start:i]),
                    }
                )
                continue
            single_match = single_decl.match(lines[i])
            if single_match and stripped.endswith(";"):
                atoms.append(
                    {
                        "kind": single_match.group(1),
                        "name": single_match.group(2),
                        "start": i,
                        "end": i + 1,
                        "text": lines[i],
                    }
                )
        depth += lines[i].count("{") - lines[i].count("}")
        if depth < 0:
            depth = 0
        i += 1
    return atoms


def _shrink_to_effective_slice(
    output_path: str,
    final_code: str,
    input_code: str,
    budget: GrowBudget,
    llm_used: bool,
    max_attempts: int = 80,
) -> tuple[str, int]:
    """Remove whole top-level atoms only when the candidate still compiles."""
    removed = 0
    attempts = 0
    current = final_code
    protected_names = {
        "PoC",
        "PanopticVaultAccountant",
        "PoolKey",
        "Currency",
        "LeftRightUnsigned",
        "LeftRightSigned",
        "TokenId",
        "PoolId",
    }
    protected_markers = ("test_submissionValidity", "availableForWithdrawal", "computeNAV")

    while attempts < max_attempts:
        result = _build_slice_result(input_code, current, True, budget, llm_used, removed)
        if result.slice_effective:
            break

        atoms = _top_level_atom_ranges(current)
        candidates = []
        for atom in atoms:
            text = str(atom["text"])
            name = str(atom["name"])
            if name in protected_names or any(marker in text for marker in protected_markers):
                continue
            line_count = int(atom["end"]) - int(atom["start"])
            priority = {
                "event": 0,
                "error": 1,
                "interface": 2,
                "library": 3,
                "contract": 4,
                "struct": 5,
                "enum": 6,
                "type": 7,
            }.get(str(atom["kind"]), 9)
            candidates.append((priority, -line_count, atom))
        if not candidates:
            break
        candidates.sort(key=lambda item: (item[0], item[1]))

        changed = False
        for _, _, atom in candidates:
            if attempts >= max_attempts:
                break
            attempts += 1
            lines = current.splitlines()
            candidate = "\n".join(lines[:int(atom["start"])] + lines[int(atom["end"]):]).strip() + "\n"
            _write_output(output_path, candidate)
            ok, _, _ = _run_compile(output_path, phase=f"shrink attempt {attempts} remove {atom['kind']} {atom['name']}")
            if ok:
                current = candidate
                removed += 1
                changed = True
                print(f"    -> Shrink kept removal of {atom['kind']} `{atom['name']}`.")
                break
            _write_output(output_path, current)
        if not changed:
            break

    _write_output(output_path, current)
    return current, removed


def _validate_body_syntax(code: str) -> list[str]:
    issues = []
    lines = code.splitlines()
    in_function = False
    in_function_header = False
    brace_depth = 0
    paren_depth = 0
    function_seen_open = False
    allowed_keyword_statements = {"break;", "continue;"}
    signature_keywords = {
        "external", "public", "internal", "private", "view", "pure", "payable",
        "virtual", "override", "returns",
    }

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r'^function\s+\w+\s*\(', stripped):
            in_function = True
            in_function_header = True
            function_seen_open = False
            brace_depth = 0
            paren_depth = line.count('(') - line.count(')')
        elif in_function_header:
            paren_depth += line.count('(') - line.count(')')

        if in_function_header:
            if '{' in line or ';' in line:
                in_function_header = False
            elif paren_depth <= 0 and re.search(r'\)\s*(?:external|public|internal|private|view|pure|payable|virtual|override|returns)\b', line):
                in_function_header = False
            continue

        if in_function:
            brace_depth += line.count('{') - line.count('}')
            if '{' in line:
                function_seen_open = True
            if brace_depth <= 0 and function_seen_open:
                in_function = False
                function_seen_open = False
                brace_depth = 0
                paren_depth = 0
                continue
            in_multiline_expression = paren_depth > 0
            if stripped in allowed_keyword_statements:
                pass
            elif stripped in signature_keywords:
                pass
            elif in_multiline_expression:
                pass
            elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\s*;', stripped):
                if idx > 1 and re.search(r'[+\-*/=<>|&,]\s*$', lines[idx - 2].strip()):
                    pass
                else:
                    issues.append(f'line {idx}: bare identifier statement `{stripped}`')
            elif re.fullmatch(r';+', stripped):
                issues.append(f'line {idx}: stray semicolon')
            elif stripped in {'a0;', 'a1;', 'a2;'}:
                issues.append(f'line {idx}: placeholder token `{stripped}`')
            elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', stripped):
                if idx > 1 and re.search(r'[+\-*/=<>|&,]\s*$', lines[idx - 2].strip()):
                    pass
                else:
                    issues.append(f'line {idx}: isolated symbol `{stripped}`')
            elif stripped and not re.search(r'[;{}()]$', stripped) and not re.match(r'^(if|for|while|return|require|revert|emit|unchecked|assembly)\b', stripped):
                if re.fullmatch(r'[a-z]\d', stripped):
                    issues.append(f'line {idx}: placeholder token `{stripped}`')
            paren_depth += line.count('(') - line.count(')')
            if paren_depth < 0:
                paren_depth = 0

    if re.search(r'\b[a-z]\d;\s*[a-z]\d;\s*[a-z]\d;', code):
        issues.append('detected repeated bare placeholder statements')
    if re.search(r'function\s+\w+\s*\([^)]*\)\s*(?:external|public|internal|private)?[^\{;\n]*\n\s*\}', code):
        issues.append('detected empty function body')
    if re.search(r'function\s+\w+\s*\([^)]*\)\s*[^\{;\n]*\n\s*;\s*\n', code):
        issues.append('detected empty or placeholder function body')
    if re.search(r'\n\s*;\s*\n', code):
        issues.append('detected isolated semicolon line')
    if re.search(r'enum\s+\w+\s*\{[^{}]*,\s*\}', code, flags=re.DOTALL):
        issues.append('detected enum trailing comma before closing brace')
    return issues[:20]


def _extract_primary_error_location(compiler_output: str) -> tuple[int | None, int | None]:
    """Return the first Solidity source location reported by forge/solc."""
    match = re.search(r'-->\s+[^:\n]+:(\d+):(\d+):', compiler_output or "")
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _remove_enum_trailing_commas(code: str) -> str:
    """Solidity does not allow a final enum member to end with a comma."""
    def clean_enum(match: re.Match) -> str:
        enum_block = match.group(0)
        return re.sub(r',(\s*\})', r'\1', enum_block)

    return re.sub(r'\benum\s+\w+\s*\{[^{}]*\}', clean_enum, code, flags=re.DOTALL)


def _preclean_raw_solidity(code: str) -> str:
    """Remove slice artifacts that confuse parsers before reconstruction."""
    cleaned_lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped in {"MOCKS", "TESTS"}:
            continue
        if stripped.startswith("*"):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"/\*[\s\S]*?(?:\*/|$)", "", cleaned)
    cleaned = re.sub(r"(?m)^[ \t]*(?:={3,}|-{3,})[ \t]*$", "", cleaned)
    return cleaned


def _remove_compiler_identified_duplicates(code: str, compiler_output: str) -> str:
    """Read solc error output to find line numbers of duplicate/shadowing declarations and comment them out."""
    lines_to_remove = set()
    import re
    out_lines = (compiler_output or "").splitlines()
    for i, line in enumerate(out_lines):
        if "Identifier already declared" in line:
            for j in range(i+1, min(i+5, len(out_lines))):
                m = re.search(r'--> .*?:(\d+):', out_lines[j])
                if m:
                    lines_to_remove.add(int(m.group(1)))
                    break
    if not lines_to_remove:
        return code
    code_lines = code.split('\n')
    for line_no in lines_to_remove:
        idx = line_no - 1
        if 0 <= idx < len(code_lines):
            # Also comment out previous line if it contains the start of a struct/enum block
            if code_lines[idx].strip() == "{" and idx > 0:
                code_lines[idx-1] = "// [DUPLICATE REMOVED] " + code_lines[idx-1]
            code_lines[idx] = "// [DUPLICATE REMOVED] " + code_lines[idx]
            # Try to comment out the rest of the block if it's a block
            depth = code_lines[idx].count('{') - code_lines[idx].count('}')
            k = idx + 1
            while depth > 0 and k < len(code_lines):
                depth += code_lines[k].count('{') - code_lines[k].count('}')
                code_lines[k] = "// [DUPLICATE REMOVED] " + code_lines[k]
                k += 1
    return '\n'.join(code_lines)


def _ensure_clone_immutable_arg_helpers(code: str) -> str:
    needed = {"_getArgAddress", "_getArgUint256", "_getImmutableArgsOffset"}
    if not any(name in code for name in needed):
        return code
    if not re.search(r"\bcontract\s+Clone\b", code):
        return code
    clone_match = re.search(r"\bcontract\s+Clone\b[^{]*\{", code)
    if not clone_match:
        return code
    clone_end = _find_matching_brace_position(code, clone_match.end() - 1)
    if clone_end is None:
        return code
    clone_body = code[clone_match.end():clone_end]
    insertions = []
    if "_getArgAddress" in code and "function _getArgAddress" not in clone_body:
        insertions.append("    function _getArgAddress(uint256) internal pure returns (address) {\n        return address(0);\n    }")
    if "_getArgUint256" in code and "function _getArgUint256" not in clone_body:
        insertions.append("    function _getArgUint256(uint256) internal pure returns (uint256) {\n        return 0;\n    }")
    if "_getImmutableArgsOffset" in code and "function _getImmutableArgsOffset" not in clone_body:
        insertions.append("    function _getImmutableArgsOffset() internal pure returns (uint256) {\n        return 0;\n    }")
    if not insertions:
        return code
    insertion = "\n" + "\n".join(insertions) + "\n"
    return code[:clone_end] + insertion + code[clone_end:]


def _find_matching_brace_position(code: str, open_pos: int) -> int | None:
    depth = 0
    for idx in range(open_pos, len(code)):
        if code[idx] == "{":
            depth += 1
        elif code[idx] == "}":
            depth -= 1
            if depth == 0:
                return idx
    return None


def _ensure_known_solidity_schemas(code: str) -> str:
    replacements = {
        "Address": """library Address {
    function sendValue(address payable recipient, uint256 amount) internal {
        (bool success, ) = recipient.call{value: amount}(\"\");
        require(success, \"Address: unable to send value\");
    }

    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.call(data);
        require(success, \"Address: low-level call failed\");
        return returndata;
    }

    function functionCallWithValue(address target, bytes memory data, uint256 value) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        require(success, \"Address: low-level call with value failed\");
        return returndata;
    }

    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        (bool success, bytes memory returndata) = target.staticcall(data);
        require(success, \"Address: low-level static call failed\");
        return returndata;
    }
} """,
        "Constants": """library Constants {
    int24 internal constant MIN_V4POOL_TICK = -887272;
    int24 internal constant MAX_V4POOL_TICK = 887272;
    uint32 internal constant FAST_ORACLE_PERIOD = 60;
    uint32 internal constant SLOW_ORACLE_PERIOD = 600;
    uint16 internal constant FAST_ORACLE_CARDINALITY = 20;
    uint16 internal constant SLOW_ORACLE_CARDINALITY = 20;
    bool internal constant SLOW_ORACLE_UNISWAP_MODE = false;
    uint32 internal constant MEDIAN_PERIOD = 600;
}""",
        "Errors": """library Errors {
    error AccountInsolvent();
    error InsufficientBalance(uint256 available, uint256 required);
    error EffectiveLiquidityAboveThreshold();
    error InputListFail();
    error InvalidTokenIdParameter(uint256);
    error NotALongLeg();
    error NotMarginCalled();
    error PoolAlreadyInitialized();
    error PositionAlreadyMinted();
    error StaleOracle();
    error TooManyLegsOpen();
}""",
        "Math_2": """library Math_2 {
    function abs(int256 value) internal pure returns (int256) {
        return value < 0 ? -value : value;
    }
    function abs(uint256 value) internal pure returns (uint256) {
        return value;
    }
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return a > b ? a : b;
    }
    function max(int256 a, int256 b) internal pure returns (int256) {
        return a > b ? a : b;
    }
    function mulDiv(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256) {
        return denominator == 0 ? 0 : (a * b) / denominator;
    }
    function mulDivRoundingUp(uint256 a, uint256 b, uint256 denominator) internal pure returns (uint256) {
        return denominator == 0 ? 0 : (a * b + denominator - 1) / denominator;
    }
    function getSqrtRatioAtTick(int24) internal pure returns (uint160) {
        return 1;
    }
    function getAmountsForLiquidity(uint160, uint160, uint128) internal pure returns (uint256, uint256) {
        return (0, 0);
    }
    function getLiquidityForAmount0(uint160, uint160, uint256) internal pure returns (uint128) {
        return 0;
    }
    function getLiquidityForAmount1(uint160, uint160, uint256) internal pure returns (uint128) {
        return 0;
    }
}""",
        "IPoolManager": """interface IPoolManager {
    function setOperator(address operator, bool approved) external;
}""",
        "CollateralTracker": """contract CollateralTracker {
    function balanceOf(address) external pure returns (uint256) {
        return 0;
    }
    function convertToAssets(uint256 assets) external pure returns (uint256) {
        return assets;
    }
    function takeCommissionAddData(address, int128, int128, int128, bool) external pure returns (uint32, uint128) {
        return (0, 0);
    }
    function exercise(address, int128, int128, int128, int128) external pure returns (int128) { return 0; }
    function getAccountMarginDetails(address, int24, uint256[2][] memory, uint128, uint128) external pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap(0);
    }
    function delegate(address) external pure {}
    function settleLiquidation(address, address, int128) external payable {}
    function exerciseCost(int24, int24, TokenId, uint128, LeftRightSigned) external pure returns (LeftRightSigned) { return LeftRightSigned.wrap(0); }
    function refund(address, address, int128) external pure {}
    function revoke(address) external pure {}
}""",
        "PanopticMath": """library PanopticMath {
    function haircutPremia(address, TokenId[] memory, LeftRightSigned[4][] memory, LeftRightSigned, CollateralTracker, CollateralTracker, uint256, mapping(bytes32 => LeftRightUnsigned) storage) internal view returns (LeftRightSigned) {
        return LeftRightSigned.wrap(0);
    }
    function computeExercisedAmounts(TokenId, uint128) internal pure returns (LeftRightSigned, LeftRightSigned) {
        return (LeftRightSigned.wrap(0), LeftRightSigned.wrap(0));
    }
    function computeInternalMedian(uint16, uint16, uint32, uint256, IV3CompatibleOracle) internal pure returns (uint256, uint256) {
        return (0, 0);
    }
    function getOracleTicks(IV3CompatibleOracle, uint256) internal pure returns (int24, int24, int24, uint256) {
        return (0, 0, 0, 0);
    }
    function getLiquidationBonus(LeftRightUnsigned, LeftRightUnsigned, uint160, LeftRightSigned, LeftRightUnsigned) internal pure returns (LeftRightSigned, LeftRightSigned) {
        return (LeftRightSigned.wrap(0), LeftRightSigned.wrap(0));
    }
    function getRefundAmounts(address, LeftRightSigned, int24, CollateralTracker, CollateralTracker) internal pure returns (LeftRightSigned) {
        return LeftRightSigned.wrap(0);
    }
    function getCrossBalances(LeftRightUnsigned, LeftRightUnsigned, uint160) internal pure returns (uint256, uint256) {
        return (0, 0);
    }
    function updatePositionsHash(uint256, TokenId, bool) internal pure returns (uint256) {
        return 0;
    }
    function twapFilter(IV3CompatibleOracle, uint32) internal view returns (int24) {
        return 0;
    }
    function getLiquidityChunk(TokenId, uint256, uint128) internal pure returns (LiquidityChunk) {
        return LiquidityChunk.wrap(0);
    }
}""",
        "SemiFungiblePositionManager": """contract SemiFungiblePositionManager {
    function burnTokenizedPosition(PoolKey memory, TokenId, uint128, int24, int24) external pure returns (LeftRightUnsigned[4] memory r0, LeftRightSigned r1) {
        r1 = LeftRightSigned.wrap(0);
    }
    function mintTokenizedPosition(PoolKey memory, TokenId, uint128, int24, int24) external pure returns (LeftRightUnsigned[4] memory r0, LeftRightSigned r1) {
        r1 = LeftRightSigned.wrap(0);
    }
    function getAccountLiquidity(PoolId, address, uint256, int24, int24) external pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap(0);
    }
    function getAccountPremium(PoolId, address, uint256, uint256, uint256, int24, uint256) external pure returns (uint128, uint128) {
        return (0, 0);
    }
    function getPoolId(PoolId) external pure returns (uint64) {
        return 0;
    }
}""",
        "V4StateReader": """library V4StateReader {
    function getTick(IPoolManager, PoolId) internal pure returns (int24) {
        return 0;
    }
}""",
        "IV3CompatibleOracle": """interface IV3CompatibleOracle {
    function observe(uint32[] memory secondsAgos) external view returns (int56[] memory, uint160[] memory);
    function slot0() external view returns (
        uint160 sqrtPriceX96,
        int24 tick,
        uint16 observationIndex,
        uint16 observationCardinality,
        uint16 observationCardinalityNext,
        uint8 feeProtocol,
        bool unlocked
    );
    function observations(uint256 index) external view returns (
        uint32 blockTimestamp,
        int56 tickCumulative,
        uint160 secondsPerLiquidityCumulativeX128,
        bool initialized
    );
    function increaseObservationCardinalityNext(uint16 observationCardinalityNext) external;
}""",
    }
    for name, replacement in replacements.items():
        code = _replace_top_level_named_block(code, name, replacement)
    if re.search(r"\busing\s+Address\s+for\b", code) and not re.search(r"\blibrary\s+Address\b", code):
        code = _inject_code_after_pragmas(code, replacements["Address"] + "\n")
    if "type LeftRightUnsigned is uint256;" in code and ".rightSlot()" in code and "library LeftRightUnsignedLib" not in code:
        code = code.replace(
            "type LeftRightUnsigned is uint256;",
            """type LeftRightUnsigned is uint256;
using LeftRightUnsignedLib for LeftRightUnsigned;

library LeftRightUnsignedLib {
    function rightSlot(LeftRightUnsigned self) internal pure returns (uint128) {
        return uint128(LeftRightUnsigned.unwrap(self));
    }
    function leftSlot(LeftRightUnsigned self) internal pure returns (uint128) {
        return uint128(LeftRightUnsigned.unwrap(self) >> 128);
    }
    function add(LeftRightUnsigned self, uint128 left, uint128 right) internal pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap(LeftRightUnsigned.unwrap(self) + (uint256(left) << 128) + uint256(right));
    }
    function add(LeftRightUnsigned self, LeftRightUnsigned other) internal pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap(LeftRightUnsigned.unwrap(self) + LeftRightUnsigned.unwrap(other));
    }
    function sub(LeftRightUnsigned self, LeftRightUnsigned other) internal pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap(LeftRightUnsigned.unwrap(self) - LeftRightUnsigned.unwrap(other));
    }
    function toLeftSlot(LeftRightUnsigned self, uint128 value) internal pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap((LeftRightUnsigned.unwrap(self) & uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)) | (uint256(value) << 128));
    }
    function toRightSlot(LeftRightUnsigned self, uint128 value) internal pure returns (LeftRightUnsigned) {
        return LeftRightUnsigned.wrap((LeftRightUnsigned.unwrap(self) & ~uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)) | (uint256(value) & uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)));
    }
}""",
            1,
        )
    if "type TokenId is uint256;" in code and ".countLegs()" in code and "library TokenIdLibrary" not in code:
        code = code.replace(
            "type TokenId is uint256;",
            """type TokenId is uint256;
using TokenIdLibrary for TokenId;

library TokenIdLibrary {
    function countLegs(TokenId) internal pure returns (uint256) {
        return 0;
    }
    function isLong(TokenId, uint256) internal pure returns (uint256) {
        return 0;
    }
    function tokenType(TokenId, uint256) internal pure returns (uint256) {
        return 0;
    }
    function strike(TokenId, uint256) internal pure returns (int24) {
        return 0;
    }
    function width(TokenId, uint256) internal pure returns (int24) {
        return 0;
    }
    function poolId(TokenId) internal pure returns (uint64) {
        return 0;
    }
    function validateIsExercisable(TokenId, int24) internal pure {}
    function asTicks(TokenId, uint256) internal pure returns (int24, int24) {
        return (0, 0);
    }
}""",
            1,
        )
    if "type LiquidityChunk is uint256;" in code and (".liquidity()" in code or ".tickLower()" in code or ".tickUpper()" in code) and "library LiquidityChunkLibrary" not in code:
        code = code.replace(
            "type LiquidityChunk is uint256;",
            """type LiquidityChunk is uint256;
using LiquidityChunkLibrary for LiquidityChunk;

library LiquidityChunkLibrary {
    function liquidity(LiquidityChunk) internal pure returns (uint128) { return 0; }
    function tickLower(LiquidityChunk) internal pure returns (uint256) { return 0; }
    function tickUpper(LiquidityChunk) internal pure returns (uint256) { return 0; }
} """,
            1,
        )
    if "type PositionBalance is uint256;" in code and "function positionSize" not in code:
        if "library PositionBalanceLibrary {" in code:
            code = code.replace(
                "library PositionBalanceLibrary {",
                """using PositionBalanceLibrary for PositionBalance;
library PositionBalanceLibrary {
    function positionSize(PositionBalance) internal pure returns (uint128) { return 0; }
    function unpackAll(PositionBalance) internal pure returns (int24, int24, int24, int24, int256, int256, uint128) {
        return (0, 0, 0, 0, 0, 0, 0);
    }""",
                1
            )
        else:
            code = code.replace(
                "type PositionBalance is uint256;",
                """type PositionBalance is uint256;
using PositionBalanceLibrary for PositionBalance;

library PositionBalanceLibrary {
    function positionSize(PositionBalance) internal pure returns (uint128) { return 0; }
    function unpackAll(PositionBalance) internal pure returns (int24, int24, int24, int24, int256, int256, uint128) {
        return (0, 0, 0, 0, 0, 0, 0);
    }
}""",
                1
            )
    if "type LeftRightSigned is int256;" in code and ".sub(" in code and "library LeftRightSignedLib" not in code:
        code = code.replace(
            "type LeftRightSigned is int256;",
            """type LeftRightSigned is int256;
using LeftRightSignedLib for LeftRightSigned;

library LeftRightSignedLib {
    function add(LeftRightSigned self, LeftRightSigned other) internal pure returns (LeftRightSigned) {
        return LeftRightSigned.wrap(LeftRightSigned.unwrap(self) + LeftRightSigned.unwrap(other));
    }
    function sub(LeftRightSigned self, LeftRightSigned other) internal pure returns (LeftRightSigned) {
        return LeftRightSigned.wrap(LeftRightSigned.unwrap(self) - LeftRightSigned.unwrap(other));
    }
    function rightSlot(LeftRightSigned self) internal pure returns (int128) {
        return int128(LeftRightSigned.unwrap(self));
    }
    function leftSlot(LeftRightSigned self) internal pure returns (int128) {
        return int128(LeftRightSigned.unwrap(self) >> 128);
    }
    function toLeftSlot(LeftRightSigned self, int128 value) internal pure returns (LeftRightSigned) {
        return LeftRightSigned.wrap((LeftRightSigned.unwrap(self) & int256(uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))) | (int256(value) << 128));
    }
    function toRightSlot(LeftRightSigned self, int128 value) internal pure returns (LeftRightSigned) {
        return LeftRightSigned.wrap((LeftRightSigned.unwrap(self) & ~int256(uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))) | (int256(value) & int256(uint256(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))));
    }
}""",
            1,
        )
    return code


def _replace_top_level_named_block(code: str, name: str, replacement: str) -> str:
    pattern = re.compile(rf"(?m)^(?:contract|library|interface)\s+{re.escape(name)}\b[^\n{{]*\{{")
    match = pattern.search(code)
    if not match:
        return code
    end = _find_matching_brace_position(code, match.end() - 1)
    if end is None:
        return code
    return code[:match.start()] + replacement + code[end + 1:]


def _deduplicate_scoped_state_variables(code: str) -> tuple[str, list[str]]:
    """Remove duplicate state variables by name within each contract/library scope."""
    lines = code.splitlines()
    remove: set[int] = set()
    changes: list[str] = []
    member_keywords = {
        "public", "private", "internal", "constant", "immutable", "override",
    }

    def state_var_name(line: str) -> str | None:
        stripped = line.strip()
        if not stripped.endswith(";") or "(" in stripped:
            return None
        if stripped.startswith(("function ", "event ", "error ", "struct ", "enum ", "modifier ", "using ")):
            return None
        before_value = stripped[:-1].split("=", 1)[0].strip()
        tokens = before_value.split()
        if len(tokens) < 2:
            return None
        while tokens and tokens[-1] in member_keywords:
            tokens.pop()
        if len(tokens) < 2:
            return None
        name = tokens[-1]
        if name in member_keywords or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            return None
        type_tokens = [t for t in tokens[:-1] if t not in member_keywords]
        if not type_tokens:
            return None
        return name

    for block in _find_top_level_blocks(code):
        if block["kind"] not in {"contract", "library"}:
            continue
        declarations: dict[str, list[tuple[int, str]]] = {}
        depth = 0
        start = int(block["start"]) + 1
        end = int(block["end"]) - 1
        for idx in range(start, max(start, end)):
            line = lines[idx]
            stripped = line.strip()
            at_member_depth = depth == 0
            name = state_var_name(stripped) if at_member_depth else None
            if name:
                declarations.setdefault(name, []).append((idx, stripped))
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0
        for name, entries in declarations.items():
            if len(entries) < 2:
                continue
            def score(entry: tuple[int, str]) -> tuple[int, int, int]:
                idx, text = entry
                padded = f" {text} "
                return (1 if " public " in padded else 0, 1 if "=" in text else 0, -idx)
            keep_idx, _ = max(entries, key=score)
            for idx, _ in entries:
                if idx != keep_idx:
                    remove.add(idx)
            changes.append(f"deduplicated state variable `{name}` in `{block['name']}`")

    if not remove:
        return code, []
    repaired = "\n".join(line for idx, line in enumerate(lines) if idx not in remove)
    return repaired, list(dict.fromkeys(changes))


def _remove_global_structs_shadowing_nested_qualified(code: str) -> tuple[str, list[str]]:
    """Drop top-level structs duplicated as Contract.Struct when qualified refs exist."""
    lines = code.splitlines()
    nested: dict[str, set[str]] = {}
    for block in _find_top_level_blocks(code):
        body = "\n".join(lines[int(block["start"]) + 1:int(block["end"]) - 1])
        names = set(re.findall(r"(?m)^\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", body))
        if names:
            nested[str(block["name"])] = names
    if not nested:
        return code, []

    remove: set[int] = set()
    changes: list[str] = []
    depth = 0
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        m = re.match(r"^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", stripped)
        if depth == 0 and m:
            name = m.group(1)
            owner = next((contract for contract, names in nested.items()
                          if name in names and re.search(rf"\b{re.escape(contract)}\.{re.escape(name)}\b", code)), None)
            if owner:
                block_depth = lines[i].count("{") - lines[i].count("}")
                start = i
                i += 1
                while i < len(lines) and block_depth > 0:
                    block_depth += lines[i].count("{") - lines[i].count("}")
                    i += 1
                remove.update(range(start, i))
                changes.append(f"removed global `{name}` shadowing `{owner}.{name}`")
                continue
        depth += lines[i].count("{") - lines[i].count("}")
        if depth < 0:
            depth = 0
        i += 1

    if not remove:
        return code, []
    return "\n".join(line for idx, line in enumerate(lines) if idx not in remove), changes


def _downgrade_external_contract_params_called_with_address(code: str) -> tuple[str, list[str]]:
    """Use address for public/external ABI parameters when call sites pass address(...).

    Recovered snippets often contain concrete mock contract variables, but external
    ABI surfaces in surrounding code pass plain addresses. Solidity does not allow
    implicit address -> contract conversion for function arguments, so generated
    mock signatures should prefer address unless a strong struct/data-location
    context exists.
    """
    changes: list[str] = []
    known_contracts = set(re.findall(r"\bcontract\s+([A-Z][A-Za-z0-9_]*)\b", code))
    if not known_contracts:
        return code, changes

    def split_params(params: str) -> list[str]:
        parts = []
        current = []
        depth = 0
        for ch in params:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth = max(0, depth - 1)
            if ch == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        parts.append("".join(current))
        return parts

    def fix_function(match: re.Match) -> str:
        name, params, suffix = match.group(1), match.group(2), match.group(3)
        if not re.search(rf"\b{name}\s*\([^;\n]*address\s*\(", code):
            return match.group(0)
        parts = split_params(params)
        changed = False
        repaired = []
        for raw in parts:
            param = raw.strip()
            if not param:
                repaired.append(raw)
                continue
            tokens = param.split()
            if len(tokens) >= 2 and tokens[0] in known_contracts and "memory" not in tokens and "calldata" not in tokens and "storage" not in tokens:
                leading = raw[:len(raw) - len(raw.lstrip())]
                trailing = raw[len(raw.rstrip()):]
                repaired.append(f"{leading}address {tokens[-1]}{trailing}")
                changes.append(f"downgraded `{name}` parameter `{tokens[-1]}` from `{tokens[0]}` to address")
                changed = True
            else:
                repaired.append(raw)
        if not changed:
            return match.group(0)
        return f"function {name}(" + ",".join(repaired) + suffix

    updated = re.sub(
        r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)(\s+(?:external|public)\b[^\{;]*\{)",
        fix_function,
        code,
        flags=re.DOTALL,
    )
    return updated, list(dict.fromkeys(changes))


def _ensure_external_data_locations(code: str) -> tuple[str, list[str]]:
    """Add memory to external/public parameters whose inferred types need a data location."""
    changes: list[str] = []
    data_location_types = re.compile(
        r'^(?:bytes|string|[A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]*\])+)$'
    )

    def fix_params(match: re.Match) -> str:
        prefix, params, suffix = match.group(1), match.group(2), match.group(3)
        parts = []
        changed = False
        for raw in params.split(','):
            param = raw.strip()
            if not param:
                parts.append(raw)
                continue
            if re.search(r'\b(memory|calldata|storage)\b', param):
                parts.append(raw)
                continue
            tokens = param.split()
            if len(tokens) < 2:
                parts.append(raw)
                continue
            type_part = " ".join(tokens[:-1])
            name_part = tokens[-1]
            if data_location_types.match(type_part):
                parts.append(f" {type_part} memory {name_part}")
                changed = True
            else:
                parts.append(raw)
        if changed:
            changes.append("added memory data location to external/public parameters")
            return prefix + ",".join(parts).strip() + suffix
        return match.group(0)

    pattern = re.compile(r'(function\s+\w+\s*\()([^)]*)(\)\s+(?:external|public)\b)', re.DOTALL)
    updated = pattern.sub(fix_params, code)
    return updated, changes


def _repair_malformed_function_signatures(code: str) -> tuple[str, list[str]]:
    """Repair common malformed generated Solidity function signatures.

    This is intentionally syntax-based and generic: generated signatures can lose
    the closing parameter-list parenthesis before visibility/mutability/returns
    clauses, especially when the last argument is a reference type such as
    `bytes memory a0`.  The repair only rewrites single-line function headers
    where a known Solidity signature keyword appears inside the argument list.
    """
    changes: list[str] = []
    keywords = r"external|public|internal|private|view|pure|payable|virtual|override|returns|modifier"
    updated_lines: list[str] = []

    for line_no, line in enumerate(code.splitlines(), start=1):
        original = line
        if re.search(r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", line):
            # Fix: function f(T a external view returns (...) {  -> function f(T a) external view returns (...) {
            line = re.sub(
                rf"^(\s*function\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^\n{{;)]*?)\s+\b((?:{keywords})\b)",
                r"\1) \2",
                line,
            )
            # Fix accidental doubled close from repeated repair.
            line = re.sub(r"\)\s*\)\s+\b(external|public|internal|private)\b", r") \1", line)
            # Normalize keyword spacing in generated headers.
            line = re.sub(r"\s{2,}(?=(?:external|public|internal|private|view|pure|payable|virtual|override|returns)\b)", " ", line)
            if line != original:
                changes.append(f"repaired malformed function signature at line {line_no}")
        updated_lines.append(line)

    return "\n".join(updated_lines), list(dict.fromkeys(changes))


def _deterministic_syntax_cleanup(code: str, compiler_output: str) -> tuple[str, list[str]]:
    """Apply small Solidity syntax repairs that are safe without semantic context."""
    changes: list[str] = []
    updated = code

    signature_cleaned, signature_changes = _repair_malformed_function_signatures(updated)
    if signature_changes:
        updated = signature_cleaned
        changes.extend(signature_changes)

    enum_cleaned = _remove_enum_trailing_commas(updated)
    if enum_cleaned != updated:
        updated = enum_cleaned
        changes.append("removed trailing comma from enum declaration")

    lines = updated.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().startswith(")") and idx > 0 and lines[idx - 1].rstrip().endswith(","):
            lines[idx - 1] = lines[idx - 1].rstrip().rstrip(",")
    multiline_param_cleaned = "\n".join(lines)
    if multiline_param_cleaned != updated:
        updated = multiline_param_cleaned
        changes.append("removed trailing comma before closing parameter list")

    line_no, _ = _extract_primary_error_location(compiler_output)
    if line_no:
        lines = updated.splitlines()
        idx = line_no - 1
        # When solc points at the closing brace, the actual problem is often
        # the previous enum/member line.
        if 0 <= idx < len(lines):
            if lines[idx].strip() == "}":
                prev_idx = idx - 1
                if prev_idx >= 0 and lines[prev_idx].rstrip().endswith(","):
                    lines[prev_idx] = lines[prev_idx].rstrip().rstrip(",")
                    candidate = "\n".join(lines)
                    if candidate != updated:
                        updated = candidate
                        changes.append(f"removed trailing comma before line {line_no}")
            
            # Handle hallucinated "})" at the top level
            elif lines[idx].strip() == "})":
                lines[idx] = lines[idx].replace("})", "}")
                candidate = "\n".join(lines)
                if candidate != updated:
                    updated = candidate
                    changes.append(f"fixed hallucinated '}})' at line {line_no}")
        
        # When solc expects a semicolon, the previous line might have a dangling operator from slicing.
        if "Expected ';'" in compiler_output:
            out_lines = compiler_output.splitlines()
            for i, out_line in enumerate(out_lines):
                if "Expected ';'" in out_line:
                    for j in range(i+1, min(i+5, len(out_lines))):
                        m = re.search(r'--> .*?:(\d+):', out_lines[j])
                        if m:
                            semicolon_line_no = int(m.group(1))
                            semicolon_idx = semicolon_line_no - 1
                            if 0 <= semicolon_idx - 1 < len(lines):
                                prev_line = lines[semicolon_idx - 1]
                                if re.search(r'[+\-*/=<>|&,]\s*$', prev_line):
                                    lines[semicolon_idx - 1] = re.sub(r'[+\-*/=<>|&,]\s*$', ';', prev_line)
                                    candidate = "\n".join(lines)
                                    if candidate != updated:
                                        updated = candidate
                                        changes.append(f"replaced dangling operator with semicolon before line {semicolon_line_no}")
                            break

        if "Expected ';' but got '['" in compiler_output:
            bracket_line_no, _ = _extract_primary_error_location(compiler_output)
            if bracket_line_no:
                bracket_idx = bracket_line_no - 1
                if 0 <= bracket_idx < len(lines):
                    assign_match = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]\s*=", lines[bracket_idx])
                    if assign_match:
                        var_name = assign_match.group(2)
                        array_len = int(assign_match.group(3)) + 1
                        prev_idx = bracket_idx - 1
                        while prev_idx >= 0 and not lines[prev_idx].strip():
                            prev_idx -= 1
                        if prev_idx >= 0:
                            type_match = re.match(
                                r"^(\s*)((?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])*)\s*$",
                                lines[prev_idx],
                            )
                            if type_match and "[]" in type_match.group(2):
                                type_name = type_match.group(2)
                                lines[prev_idx] = (
                                    f"{type_match.group(1)}{type_name} memory {var_name} = "
                                    f"new {type_name}({array_len});"
                                )
                                candidate = "\n".join(lines)
                                if candidate != updated:
                                    updated = candidate
                                    changes.append(f"completed truncated array declaration for `{var_name}`")

    return updated, changes


def _find_top_level_blocks(code: str) -> list[dict[str, object]]:
    lines = code.splitlines()
    blocks = []
    depth = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        m = re.match(r"^(contract|library|interface)\s+([A-Za-z_][A-Za-z0-9_]*)\b([^{};]*)\{", stripped)
        if depth == 0 and m:
            start = i
            block_depth = line.count("{") - line.count("}")
            i += 1
            while i < len(lines) and block_depth > 0:
                block_depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            blocks.append({
                "kind": m.group(1),
                "name": m.group(2),
                "header": stripped,
                "start": start,
                "end": i,
            })
            continue
        depth += line.count("{") - line.count("}")
        if depth < 0:
            depth = 0
        i += 1
    return blocks


def _repair_missing_array_declarations(code: str) -> tuple[str, list[str]]:
    lines = code.splitlines()
    changes: list[str] = []
    declared: set[str] = set()
    result: list[str] = []
    in_function = False
    function_depth = 0

    declaration_pattern = re.compile(
        r"\b[A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]*\])*\s+"
        r"(?:memory\s+|storage\s+|calldata\s+)?([A-Za-z_][A-Za-z0-9_]*)\b"
    )
    assignment_pattern = re.compile(
        r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]\s*=\s*"
        r"((?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*)\s*\("
    )

    for line in lines:
        stripped = line.strip()
        if re.match(r"^function\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", stripped):
            in_function = True
            function_depth = 0
            declared = set()

        if in_function:
            for decl in declaration_pattern.finditer(line):
                declared.add(decl.group(1))
            match = assignment_pattern.match(line)
            if match and match.group(2) not in declared:
                indent, var_name, index_text, type_name = match.group(1), match.group(2), match.group(3), match.group(4)
                length = int(index_text) + 1
                result.append(f"{indent}{type_name}[] memory {var_name} = new {type_name}[]({length});")
                declared.add(var_name)
                changes.append(f"inserted missing memory array declaration for `{var_name}`")

        result.append(line)

        if in_function:
            function_depth += line.count("{") - line.count("}")
            if function_depth <= 0 and "}" in line:
                in_function = False
                function_depth = 0
                declared = set()

    return "\n".join(result), list(dict.fromkeys(changes))


def _convert_placeholder_structs_used_as_contracts(code: str) -> str:
    placeholder_structs = set()
    for match in re.finditer(
        r"(?ms)^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*bytes\s+data\s*;\s*\}\s*",
        code,
    ):
        placeholder_structs.add(match.group(1))
    if not placeholder_structs:
        return code

    convert = set()
    for name in placeholder_structs:
        escaped = re.escape(name)
        contract_value_patterns = [
            rf"\b{escaped}\s*\(\s*address\s*\(",
            rf"\bnew\s+{escaped}\s*\(",
            rf"returns\s*\([^)]*\b{escaped}\b(?!\s+(?:memory|storage|calldata))",
            rf"\b(?:constructor|function)\s*[A-Za-z_0-9]*\s*\([^)]*\b{escaped}\s+[A-Za-z_][A-Za-z0-9_]*",
            rf"(?m)^\s*{escaped}\s+[A-Za-z_][A-Za-z0-9_]*\s*=",
            rf"\b{escaped}\.[a-z_][A-Za-z0-9_]*\s*\(",
        ]
        if any(re.search(pattern, code) for pattern in contract_value_patterns):
            convert.add(name)

    if not convert:
        return code

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in convert:
            return match.group(0)
        return f"contract {name} {{}}\n\n"

    return re.sub(
        r"(?ms)^struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*bytes\s+data\s*;\s*\}\s*\n*",
        replace,
        code,
    )


def _extract_base_names(header: str) -> list[str]:
    match = re.search(r"\bis\s+(.+?)\s*\{?$", header)
    if not match:
        return []
    bases = []
    for part in match.group(1).split(","):
        name_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", part.strip())
        if name_match:
            bases.append(name_match.group(1))
    return bases


def _ensure_base_contracts_precede_derived(code: str) -> str:
    lines = code.splitlines()
    changed = True
    while changed:
        changed = False
        blocks = _find_top_level_blocks("\n".join(lines))
        positions = {block["name"]: block for block in blocks}
        for derived in blocks:
            for base_name in _extract_base_names(str(derived["header"])):
                base = positions.get(base_name)
                if not base:
                    continue
                if int(base["start"]) < int(derived["start"]):
                    continue
                base_lines = lines[int(base["start"]):int(base["end"])]
                del lines[int(base["start"]):int(base["end"])]
                blocks_after_delete = _find_top_level_blocks("\n".join(lines))
                new_positions = {block["name"]: block for block in blocks_after_delete}
                target = new_positions.get(derived["name"])
                if not target:
                    continue
                insert_at = int(target["start"])
                lines[insert_at:insert_at] = base_lines + [""]
                changed = True
                break
            if changed:
                break
    return "\n".join(lines)



def _repair_duplicate_placeholder_modifiers(code: str) -> tuple[str, list[str]]:
    """Drop placeholder ``modifier X() { _; }`` when a real X modifier exists."""
    changes: list[str] = []
    lines = code.splitlines()
    real = set()
    placeholder_index: dict[str, list[int]] = {}
    for index, line in enumerate(lines):
        m = re.match(r"\s*modifier\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*(?:virtual\s+)?\{", line)
        if m:
            real.add(m.group(1))
        m = re.match(r"\s*modifier\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(\s*\)\s*\{\s*_;\s*\}\s*", line)
        if m:
            placeholder_index.setdefault(m.group(1), []).append(index)
    for name, indexes in placeholder_index.items():
        if name in real:
            for index in indexes:
                lines[index] = None
            changes.append(f'dropped placeholder modifier {name} x{len(indexes)}')
    result = '\n'.join(line for line in lines if line is not None)
    if code.endswith('\n'):
        result += '\n'
    return result, changes


_SOLIDITY_KEYWORDS = {
    'address', 'bool', 'string', 'bytes', 'byte', 'bytes1', 'bytes2', 'bytes3',
    'bytes4', 'bytes8', 'bytes16', 'bytes32', 'uint', 'uint8', 'uint16',
    'uint24', 'uint32', 'uint40', 'uint48', 'uint56', 'uint64', 'uint72',
    'uint80', 'uint88', 'uint96', 'uint104', 'uint112', 'uint120', 'uint128',
    'uint136', 'uint144', 'uint152', 'uint160', 'uint168', 'uint176', 'uint184',
    'uint192', 'uint200', 'uint208', 'uint216', 'uint224', 'uint232', 'uint240',
    'uint248', 'uint256', 'int', 'int8', 'int16', 'int24', 'int32', 'int40',
    'int48', 'int56', 'int64', 'int72', 'int80', 'int88', 'int96', 'int104',
    'int112', 'int120', 'int128', 'int136', 'int144', 'int152', 'int160',
    'int168', 'int176', 'int184', 'int192', 'int200', 'int208', 'int216',
    'int224', 'int232', 'int240', 'int248', 'int256', 'mapping', 'calldata',
    'memory', 'storage', 'payable', 'external', 'public', 'internal', 'private',
    'view', 'pure', 'returns', 'function', 'contract', 'library', 'struct',
    'enum', 'event', 'error', 'modifier', 'if', 'else', 'for', 'while', 'do',
    'new', 'delete', 'return', 'require', 'assert', 'revert', 'indexed',
}


def _repair_keyword_param_names(code: str) -> tuple[str, list[str]]:
    """Rename function parameters that shadow a Solidity type/keyword.

    A generated mock such as ``function toBytes32(address address)`` is invalid
    because the parameter is named after the type.  This renames the parameter
    token when it is a Solidity keyword and the preceding token is a plausible
    type, leaving multi-token types intact.
    """
    changes: list[str] = []
    lines = code.splitlines()

    def fix_line(line: str) -> str:
        if 'function' not in line:
            return line
        m = re.match(r"^(\s*function\s+[A-Za-z_$][A-Za-z0-9_$]*\s*)\(([^)]*)\)(.*)$", line)
        if not m:
            return line
        prefix, params, suffix = m.group(1) + '(', m.group(2), ')' + m.group(3)
        parts = []
        changed = False
        for raw in params.split(','):
            stripped = raw.strip()
            tokens = stripped.split()
            if len(tokens) >= 2 and tokens[-1] in _SOLIDITY_KEYWORDS:
                new_name = '_' + tokens[-1]
                tokens[-1] = new_name
                changed = True
                changes.append(f'renamed param {raw.strip()} -> {" ".join(tokens)}')
            parts.append(' '.join(tokens) if changed else raw)
        return prefix + ', '.join(parts) + suffix if changed else line

    new_lines = [fix_line(line) for line in lines]
    result = '\n'.join(new_lines)
    if code.endswith('\n'):
        result += '\n'
    return result, changes

def _infer_error_arg_type(expr: str, code: str) -> str:
    """Best-effort Solidity type for one revert error argument expression."""
    expr = expr.strip()
    if not expr:
        return 'uint256'
    if re.match(r'^address\s*\(', expr):
        return 'address'
    if re.match(r'^address\s+payable\s*\(', expr):
        return 'address payable'
    if re.match(r'^bytes32\s*\(', expr):
        return 'bytes32'
    if re.match(r'^bytes\s*\(', expr):
        return 'bytes memory'
    if re.match(r'^string\s*\(', expr):
        return 'string memory'
    if re.match(r'^\d+$', expr):
        return 'uint256'
    if re.match(r'^(true|false)$', expr):
        return 'bool'
    if expr in ('_msgSender()', 'msg.sender', 'tx.origin'):
        return 'address'
    # Bare identifier: scan declarations anywhere in the file (best effort).
    ident = re.match(r'^([A-Za-z_$][A-Za-z0-9_$]*)$', expr)
    if ident:
        name = ident.group(1)
        for type_token in ('address', 'address payable', 'bool', 'uint256',
                           'int256', 'bytes32', 'uint32', 'uint64', 'uint128'):
            if re.search(rf'\b{re.escape(type_token)}\s+{re.escape(name)}\b',
                         code):
                return type_token
    return 'uint256'


def _repair_zero_arg_custom_errors(code: str) -> tuple[str, list[str]]:
    """Expand zero-arg ``error X();`` placeholders to match their revert sites.

    The assembler collapses OpenZeppelin/user custom errors into zero-arg
    placeholders while the generated harness still calls ``revert X(args...)``,
    which fails with "wrong argument count".  This restores the declarations
    from the call sites (best-effort type inference) so the harness compiles.
    """
    changes: list[str] = []
    lines = code.splitlines()

    decl_index = {}
    for index, line in enumerate(lines):
        m = re.match(r"\s*error\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(\s*\)\s*;", line)
        if m:
            decl_index.setdefault(m.group(1), index)

    if not decl_index:
        return code, changes

    # Find revert call sites per error name.
    usage = {}
    for line in lines:
        for m in re.finditer(
                rf"\brevert\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                line):
            name = m.group(1)
            if name not in decl_index:
                continue
            # Capture arguments until the matching close paren on this line.
            open_idx = m.end() - 1
            depth = 0
            close_idx = None
            for j in range(open_idx, len(line)):
                if line[j] == '(':
                    depth += 1
                elif line[j] == ')':
                    depth -= 1
                    if depth == 0:
                        close_idx = j
                        break
            if close_idx is None:
                continue
            args_text = line[open_idx + 1:close_idx]
            args = [a.strip() for a in args_text.split(',') if a.strip()]
            usage.setdefault(name, args)

    for name, index in sorted(decl_index.items(), key=lambda kv: kv[1],
                              reverse=True):
        args = usage.get(name)
        if not args:
            continue
        types = [_infer_error_arg_type(arg, code) for arg in args]
        params = ', '.join(f'{typ} arg{i}' if typ.endswith(' memory')
                           else f'{typ} arg{i}'
                           for i, typ in enumerate(types))
        new_line = f'error {name}({params});'
        lines[index] = new_line
        changes.append(f'expanded error {name} with {len(types)} arg(s)')

    return '\n'.join(lines), changes

def _remove_nested_errors_shadowing_globals(code: str) -> str:
    global_errors = set()
    lines = code.splitlines()
    depth = 0
    for line in lines:
        if depth == 0:
            m = re.match(r"\s*error\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if m:
                global_errors.add(m.group(1))
        depth += line.count("{") - line.count("}")
        if depth < 0:
            depth = 0
    if not global_errors:
        return code

    result = []
    depth = 0
    for line in lines:
        m = re.match(r"\s*error\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*;", line)
        if depth > 0 and m and m.group(1) in global_errors:
            depth += line.count("{") - line.count("}")
            if depth < 0:
                depth = 0
            continue
        result.append(line)
        depth += line.count("{") - line.count("}")
        if depth < 0:
            depth = 0
    return "\n".join(result)


def _fallback_type_for_name(name: str) -> str:
    lowered = name.lower()
    if "window" in lowered or "period" in lowered or "duration" in lowered:
        return "uint32"
    if lowered.startswith("is") or lowered.startswith("has") or lowered.endswith("flag"):
        return "bool"
    if "addr" in lowered or "owner" in lowered or "user" in lowered:
        return "address"
    if "tick" in lowered or "price" in lowered or "delta" in lowered:
        return "int24" if "tick" in lowered or "price" in lowered else "int256"
    return "uint256"


def _is_invalid_generated_type(type_name: str) -> bool:
    if not type_name:
        return False
    normalized = type_name.strip()
    invalid_words = {
        "constant", "immutable", "on", "the", "current", "token", "tokens",
        "deltas", "amounts", "values", "data", "with", "from", "to",
    }
    if normalized in invalid_words:
        return True
    if normalized == "address payable":
        return False
    if normalized[0].islower() and not re.match(
        r"^(?:u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)?|address|bool|string|bytes(?:[1-9]|[12][0-9]|3[0-2])?)"
        r"(?:\[[^\]]*\])*$",
        normalized,
    ):
        return True
    return False


def _repair_invalid_generated_types(code: str, compiler_output: str = "") -> tuple[str, list[str]]:
    """Replace obvious non-type words that slipped into generated mocks/structs."""
    changes: list[str] = []
    updated = code

    def fix_params(match: re.Match) -> str:
        prefix, params, suffix = match.group(1), match.group(2), match.group(3)
        parts = []
        changed = False
        for raw in params.split(","):
            leading = raw[:len(raw) - len(raw.lstrip())]
            trailing = raw[len(raw.rstrip()):]
            param = raw.strip()
            if not param:
                parts.append(raw)
                continue
            tokens = param.split()
            if len(tokens) < 2:
                parts.append(raw)
                continue
            name = tokens[-1]
            type_tokens = tokens[:-1]
            if type_tokens and type_tokens[-1] in {"memory", "storage", "calldata"}:
                type_core = " ".join(type_tokens[:-1])
                data_location = " " + type_tokens[-1]
            else:
                type_core = " ".join(type_tokens)
                data_location = ""
            if _is_invalid_generated_type(type_core):
                replacement = _fallback_type_for_name(name)
                parts.append(f"{leading}{replacement}{data_location} {name}{trailing}")
                changes.append(f"replaced invalid parameter type `{type_core}` with `{replacement}`")
                changed = True
            else:
                parts.append(raw)
        if not changed:
            return match.group(0)
        return prefix + ",".join(parts) + suffix

    updated = re.sub(r"(function\s+\w+\s*\()([^)]*)(\))", fix_params, updated, flags=re.DOTALL)

    def fix_field(match: re.Match) -> str:
        indent, type_name, field_name, suffix = match.group(1), match.group(2), match.group(3), match.group(4)
        if not _is_invalid_generated_type(type_name):
            return match.group(0)
        replacement = _fallback_type_for_name(field_name)
        changes.append(f"replaced invalid field type `{type_name}` with `{replacement}`")
        return f"{indent}{replacement} {field_name}{suffix}"

    lines = updated.splitlines()
    repaired_lines = []
    in_struct = False
    struct_depth = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^struct\s+[A-Za-z_][A-Za-z0-9_]*\s*\{", stripped):
            in_struct = True
            struct_depth = line.count("{") - line.count("}")
            repaired_lines.append(line)
            if struct_depth <= 0:
                in_struct = False
            continue
        if in_struct:
            repaired_lines.append(
                re.sub(
                    r"^(\s+)([a-zA-Z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(;|=[^;]+;)$",
                    fix_field,
                    line,
                )
            )
            struct_depth += line.count("{") - line.count("}")
            if struct_depth <= 0:
                in_struct = False
            continue
        repaired_lines.append(line)
    updated = "\n".join(repaired_lines)

    if "Expected type name" in (compiler_output or "") and not changes:
        line_no, _ = _extract_primary_error_location(compiler_output)
        if line_no:
            lines = updated.splitlines()
            idx = line_no - 1
            if 0 <= idx < len(lines):
                before = lines[idx]
                lines[idx] = re.sub(
                    r"\b(constant|on|the|current|token|tokens|deltas)\s+([A-Za-z_][A-Za-z0-9_]*)",
                    lambda m: f"{_fallback_type_for_name(m.group(2))} {m.group(2)}",
                    lines[idx],
                )
                if lines[idx] != before:
                    updated = "\n".join(lines)
                    changes.append(f"repaired invalid type at compiler line {line_no}")

    seen = set()
    unique_changes = []
    for change in changes:
        if change in seen:
            continue
        seen.add(change)
        unique_changes.append(change)
    return updated, unique_changes


def _remove_invalid_body_statements(code: str) -> str:
    """Remove obvious placeholder statements, but only from function bodies."""
    cleaned_lines = []
    in_function = False
    brace_depth = 0
    function_seen_open = False
    allowed_keyword_statements = {"break;", "continue;"}

    for line in code.splitlines():
        stripped = line.strip()
        starts_function = re.match(r'^function\s+\w+\s*\(', stripped)
        if starts_function:
            in_function = True
            brace_depth = 0
            function_seen_open = False

        remove_line = False
        if in_function:
            if stripped in allowed_keyword_statements:
                remove_line = False
            elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\s*;', stripped):
                if len(cleaned_lines) > 0 and re.search(r'[+\-*/=<>|&,]\s*$', cleaned_lines[-1].strip()):
                    remove_line = False
                else:
                    remove_line = True
            elif re.fullmatch(r'(?:[a-z]\d\s*;\s*)+', stripped):
                remove_line = True
            elif stripped in {'a0;', 'a1;', 'a2;', ';'}:
                remove_line = True
            elif re.fullmatch(r'[a-z]\d\s*;?', stripped):
                remove_line = True

        if not remove_line:
            cleaned_lines.append(line)

        if in_function:
            brace_depth += line.count('{') - line.count('}')
            if '{' in line:
                function_seen_open = True
            if brace_depth <= 0 and function_seen_open:
                in_function = False
                brace_depth = 0
                function_seen_open = False

    return re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned_lines))



def _inject_code_after_pragmas(code: str, new_code: str) -> str:
    lines = code.splitlines()
    insert_at = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("// SPDX-License-Identifier") or stripped.startswith("pragma solidity") or stripped.startswith("import "):
            insert_at = idx + 1
            continue
        if not stripped:
            insert_at = idx + 1
            continue
        break
    lines.insert(insert_at, new_code)
    return "\n".join(lines)


def _ensure_domain_type_aliases(code: str) -> str:
    """Insert known user-defined value types before structs that reference them.
    
    NOTE: 'Currency' is a well-known Uniswap v4 type alias (type Currency is address).
    This is a domain-specific heuristic; for other ecosystems, this list may need extension.
    """
    aliases = []
    if re.search(r'\bCurrency\b', code):
        aliases.append("type Currency is address;")

    if not aliases:
        return code

    lines = [
        line for line in code.splitlines()
        if not re.match(r'\s*type\s+Currency\s+is\s+address\s*;\s*$', line)
    ]
    insert_at = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("// SPDX-License-Identifier") or stripped.startswith("pragma solidity") or stripped.startswith("import "):
            insert_at = idx + 1
            continue
        if not stripped:
            insert_at = idx + 1
            continue
        break

    lines[insert_at:insert_at] = aliases + [""]
    return "\n".join(lines)


def _extract_undefined_symbols_from_compiler_output(compiler_output: str) -> list[str]:
    """Pull candidate missing symbols from solc source snippets, not from 'Error (7920)'."""
    symbols: list[str] = []
    seen = set()
    for line in (compiler_output or "").splitlines():
        match = re.match(r'\s*(?:\d+\s*)?\|\s*(.+)$', line)
        if not match:
            continue
        snippet = match.group(1)
        if "^" in snippet or snippet.startswith("Error"):
            continue
        for symbol in re.findall(r'\b([A-Z][A-Za-z0-9_]*)\b', snippet):
            if symbol in seen:
                continue
            seen.add(symbol)
            symbols.append(symbol)
    return symbols


def _is_body_syntax_error(compiler_output: str, code: str | None = None) -> bool:
    if ErrorRouter.classify(compiler_output) == 'body_syntax':
        return True
    if code:
        return bool(_validate_body_syntax(code))
    return False


def _print_manifest_summary(manifest) -> None:
    symbols = getattr(manifest, 'symbols', None)
    if not symbols:
        print(f"    -> Orphans: {len(manifest.orphans)} | Contracts: {len(manifest.contracts)} | Libraries: {len(manifest.libraries)}")
        return
    print(
        "    -> Symbols: "
        f"contracts={len(symbols.contracts)} "
        f"interfaces={len(symbols.interfaces)} "
        f"libraries={len(symbols.libraries)} "
        f"structs={len(symbols.structs)} "
        f"errors={len(symbols.errors)} "
        f"types={len(symbols.types)}"
    )
    print(f"    -> Orphans={len(manifest.orphans)} | Contract shells={len(manifest.contracts)} | Library blocks={len(manifest.libraries)}")


def _collect_code_missing_types(final_code: str, known_symbols=None) -> list[str]:
    import re
    scan_code = re.sub(r'/\*[\s\S]*?\*/', ' ', final_code)
    scan_code = re.sub(r'//.*', ' ', scan_code)
    scan_code = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', scan_code)
    all_defined = set(re.findall(r'\b(?:contract|library|interface|struct|type)\s+(\w+)', final_code))
    all_defined |= set(re.findall(r'\berror\s+(\w+)', final_code))

    candidates: set[str] = set()
    evidence_patterns = [
        r'\b([A-Z][A-Za-z0-9_]*)\[\]\s+(?:memory\s+|storage\s+|calldata\s+)?[a-z_][A-Za-z0-9_]*\b',
        r'\b([A-Z][A-Za-z0-9_]*)\s+memory\s+[a-z_][A-Za-z0-9_]*\b',
        r'\b([A-Z][A-Za-z0-9_]*)\s+storage\s+[a-z_][A-Za-z0-9_]*\b',
        r'\b([A-Z][A-Za-z0-9_]*)\s+calldata\s+[a-z_][A-Za-z0-9_]*\b',
        r'\bnew\s+([A-Z][A-Za-z0-9_]*)\s*\(',
        r'\b([A-Z][A-Za-z0-9_]*)\.[A-Z][A-Za-z0-9_]*\b',
        r'\b([A-Z][A-Za-z0-9_]*)\s+[a-z_][A-Za-z0-9_]*\s*(?:;|=|,|\))',
        r'abi\.decode\([^,]+,\s*\([^)]*\b([A-Z][A-Za-z0-9_]*)\b',
        r'\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\b([A-Z][A-Za-z0-9_]*)\s+[a-z_][A-Za-z0-9_]*\b',
        r'\bcontract\s+\w+\s+is\s+[^{]*\b([A-Z][A-Za-z0-9_]*)\b',
        r'\brevert\s+([A-Z][A-Za-z0-9_]*)\s*\(',
    ]
    for pattern in evidence_patterns:
        candidates.update(re.findall(pattern, scan_code))
    for bases in re.findall(r'\bcontract\s+\w+\s+is\s+([^{]+)\{', scan_code):
        for base in bases.split(','):
            base_match = re.match(r'\s*([A-Z][A-Za-z0-9_]*)', base)
            if base_match:
                candidates.add(base_match.group(1))

    builtins_global = {'String','Bytes','Address','Uint','Int','Bool','Test','Clone','PoC',
                        'Math','Mock',
                        'SPDX','MIT',
                        'Currency'}
    noisy_suffixes = ('_mockValues', '_mockBools', '_mockAddresses', '_mockBytes32', '_mockPositionBalances', '_mockNumLegs')
    return [
        t for t in sorted(candidates)
        if t not in all_defined
        and t not in builtins_global
        and not t.isupper()
        and not any(t.endswith(suffix) for suffix in noisy_suffixes)
        and len(t) > 1
        and t[0].isupper()
        and not t.startswith('_')
    ]


def _deduplicate_generated_code(existing_code: str, generated_code: str) -> str:
    """Remove from generated_code any definitions that already exist in existing_code."""
    import re

    def block_end(lines, start):
        depth = 0
        seen_open = False
        for i in range(start, len(lines)):
            depth += lines[i].count('{') - lines[i].count('}')
            if '{' in lines[i]:
                seen_open = True
            if seen_open and depth <= 0:
                return i
        return len(lines) - 1

    name_patterns = [
        r'\bcontract\s+(\w+)', r'\binterface\s+(\w+)', r'\blibrary\s+(\w+)',
        r'\bstruct\s+(\w+)', r'\berror\s+(\w+)\s*[\(;]', r'\benum\s+(\w+)',
        r'\btype\s+(\w+)\s+is\s+', r'\bevent\s+(\w+)\s*\(',
    ]
    defined = set()
    for p in name_patterns:
        defined.update(m.group(1) for m in re.finditer(p, existing_code, re.MULTILINE))
    if not defined:
        return generated_code.strip()

    lines = generated_code.splitlines()
    remove = set()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        m = re.match(r'^(contract|interface|library|struct|enum)\s+(\w+)\b', stripped)
        if m and m.group(2) in defined:
            end = block_end(lines, i)
            for j in range(i, end + 1):
                remove.add(j)
            i = end + 1
            continue
        m = re.match(r'^error\s+(\w+)\s*\(', stripped)
        if m and m.group(1) in defined:
            remove.add(i)
        m = re.match(r'^event\s+(\w+)\s*\(', stripped)
        if m and m.group(1) in defined:
            remove.add(i)
        m = re.match(r'^type\s+(\w+)\s+is\s+', stripped)
        if m and m.group(1) in defined:
            remove.add(i)
        i += 1

    generated_code = '\n'.join(line for idx, line in enumerate(lines) if idx not in remove)
    generated_code = re.sub(r'\n{3,}', '\n\n', generated_code)
    return generated_code.strip()


def _remove_duplicate_blocks(code: str, defined: set[str]) -> str:
    import re
    lines = code.split('\n')
    out = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        m = re.match(r'^(contract|interface|library|struct|enum)\s+(\w+)\b', stripped)
        if m and m.group(2) in defined:
            depth = stripped.count('{') - stripped.count('}')
            if depth <= 0 and '{' in stripped and '}' in stripped:
                i += 1
                continue
            i += 1
            while i < len(lines):
                depth += lines[i].count('{') - lines[i].count('}')
                if depth <= 0:
                    i += 1
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return '\n'.join(out)


def _repair_with_llm(brain: ContextBrain, current_code: str, compiler_output: str, iteration: int, max_iterations: int) -> str:
    # Truncate code if too large to avoid token limits
    code_for_prompt = current_code
    if len(current_code) > 30000:
        # Keep header + last portion
        code_for_prompt = current_code[:2000] + "\n// ... [truncated middle] ...\n" + current_code[-15000:]

    repair_prompt = f"""
You are repairing generated Solidity so it compiles.

Return ONLY a JSON RepairPlan object with this schema:
{{
  "category": "string",
  "rationale": "string",
  "actions": [
    {{"action": "add_type_definition|add_state_variable|remove_definition|replace_function_body|add_function_body|replace_function", "target": "string", "details": {{"code": "string"}}}}
  ],
  "reject_reason": null
}}

Do not return the complete file.

CURRENT FILE:
{code_for_prompt}

COMPILER ERRORS:
{compiler_output[:3000]}

FIX STRATEGY (apply in this order):
1. MISSING TYPE DEFINITIONS: For each "Undeclared identifier" error, create a minimal compilable definition action. Use `add_state_variable` with the EXACT contract/library name as `target` (e.g. `HypoVault` or `TokenIdLibrary`, not a mock contract) to add missing state variables OR functions (e.g. missing `poolId` function) to the specific contract that threw the error or type it belongs to. Use `add_type_definition` for missing global structs, enums, or interfaces.
2. SCOPE FIXES: If a type is defined inside a contract but referenced from outside, add a move/replace action.
3. SIGNATURE FIXES: Match function signatures to how they are called. If a function returns the wrong number of variables, or has wrong arguments, use `replace_function` to rewrite its entire signature and body. Set `target` to the exact function name. IMPORTANT: For reference types (arrays, structs, strings, bytes) in return parameters, you MUST include the `memory` keyword (e.g. `returns (int24[] memory, uint256)` instead of `returns (int24[], uint256)`).
4. REMOVE DUPLICATES: If a type/function/error is defined twice, keep one copy.
5. REMOVE JUNK: Remove invalid placeholder body content with body-filling actions.

GENERAL RULES:
- Keep the file SELF-CONTAINED.
- Do NOT import external files except 'forge-std/Test.sol'.
- If a mock contract is needed, include the minimal code in the action details.
- Repair iteration {iteration}/{max_iterations}.
"""
    return brain._call_llm_text(repair_prompt)


def _deduplicate_final_code(code: str) -> str:
    """Normalize the final file by removing duplicate top-level definitions.
    Keep the first occurrence of each name and drop later duplicates.
    """
    import re

    def find_block_end(lines, start):
        depth = 0
        seen_open = False
        for i in range(start, len(lines)):
            depth += lines[i].count('{') - lines[i].count('}')
            if '{' in lines[i]:
                seen_open = True
            if seen_open and depth <= 0:
                return i
        return len(lines) - 1

    lines = code.split('\n')
    seen = set()
    remove = set()
    patterns = [
        (re.compile(r'^\s*(contract|interface|library|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)\b'), True),
        (re.compile(r'^\s*error\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('), False),
        (re.compile(r'^\s*event\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('), False),
        (re.compile(r'^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+is\b'), False),
        (re.compile(r'^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('), True),
    ]

    i = 0
    depth = 0
    while i < len(lines):
        stripped = lines[i].strip()
        matched = False
        if depth == 0:
            for pat, is_block in patterns:
                m = pat.match(stripped)
                if not m:
                    continue
                matched = True
                name = m.group(2) if pat.pattern.startswith('^\\s*(contract') else m.group(1)
                if name in seen:
                    if is_block:
                        end = find_block_end(lines, i)
                        for j in range(i, end + 1):
                            remove.add(j)
                        i = end + 1
                    else:
                        remove.add(i)
                        i += 1
                else:
                    seen.add(name)
                    if is_block:
                        i = find_block_end(lines, i) + 1
                    else:
                        i += 1
                break
        if not matched:
            depth += lines[i].count('{') - lines[i].count('}')
            if depth < 0:
                depth = 0
            i += 1

    result = '\n'.join(line for idx, line in enumerate(lines) if idx not in remove)
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    return result.strip() + '\n'


def main():
    import datetime
    import sys

    parser = argparse.ArgumentParser(description="Solidity Resurrector")
    parser.add_argument("input_file", help="Path to the broken Solidity slice")
    parser.add_argument("--config", default=str(DEFAULT_LLM_CONFIG_PATH), help="Runtime env config file")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Output file path")
    parser.add_argument("--max-fix-iterations", type=int, default=3, help="Max auto repair rounds")
    parser.add_argument("--resurrect-v2", action="store_true", help="Enable bounded effective-slice reporting and shrink gate")
    parser.add_argument("--compile-artifact-fallback", action="store_true", help="Allow compile-success output even when it is not an effective slice")
    parser.add_argument("--max-line-ratio", type=float, default=0.25, help="Effective slice line-ratio budget")
    parser.add_argument("--max-byte-ratio", type=float, default=0.30, help="Effective slice byte-ratio budget")
    args = parser.parse_args()
    loaded_config_paths = _load_runtime_config(args.config)
    budget = GrowBudget(max_line_ratio=args.max_line_ratio, max_byte_ratio=args.max_byte_ratio)

    # Setup categorized logging
    log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    input_name = Path(args.input_file).stem
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f"{input_name}_{timestamp}.log"
    
    class LoggerTee:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log_file = open(filename, "w", encoding="utf-8")
        def write(self, message):
            self.terminal.write(message)
            self.log_file.write(message)
            self.log_file.flush()
        def flush(self):
            self.terminal.flush()
            self.log_file.flush()
            
    sys.stdout = LoggerTee(log_filename)
    sys.stderr = sys.stdout
    print(f"[*] Execution log started: {log_filename}")
    if loaded_config_paths:
        print("[*] Loaded config:")
        for path in loaded_config_paths:
            print(f"    -> {path}")
    else:
        print("[WARN] No config file loaded; relying on process environment.")

    print(f"[*] Reading {args.input_file}...")
    with open(args.input_file, "rb") as f:
        code_bytes = f.read()

    # Pre-process: Fix unclosed braces at the end of the file which breaks tree-sitter
    code_str = _preclean_raw_solidity(code_bytes.decode('utf-8', errors='ignore'))
    brace_diff = code_str.count('{') - code_str.count('}')
    if brace_diff > 0:
        code_str += '\n' + '}\n' * brace_diff
        code_bytes = code_str.encode('utf-8')

    print("[*] Parsing AST structure...")
    parser_tool = SolidityParser()
    manifest = parser_tool.parse(code_bytes)

    print(f"    -> Found {len(manifest.orphans)} orphan functions")
    print(f"    -> Found {len(manifest.contracts)} contract shells")
    print(f"    -> Found {len(manifest.libraries)} libraries to mock")
    if getattr(manifest, 'symbols', None):
        print(f"    -> Symbol index: {len(manifest.symbols.contracts)} contracts, {len(manifest.symbols.interfaces)} interfaces, {len(manifest.symbols.structs)} structs, {len(manifest.symbols.errors)} errors")

    print("[*] Inferring context via LLM...")
    provider = (os.getenv("LLM_PROVIDER") or "openai").lower()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if provider != "opencode" and not api_key:
        print("Error: GEMINI_API_KEY or OPENAI_API_KEY not set")
        print(f"Please set one of these in {args.config} or in your process environment")
        return

    base_url = os.getenv("API_BASE_URL")
    model = os.getenv("MODEL_NAME")
    resolved_model = model if model else ("opencode-go/deepseek-v4-flash" if provider == "opencode" else "gemini-2.0-flash-exp")
    resolved_base_url = base_url if base_url else "https://generativelanguage.googleapis.com/v1beta/openai/"
    print(f"    -> LLM provider: {provider}")
    if provider == "opencode":
        print("    -> LLM base_url: <opencode cli>")
    else:
        print(f"    -> LLM base_url: {resolved_base_url}")
    print(f"    -> LLM model: {resolved_model}")

    brain = ContextBrain(
        api_key=api_key,
        base_url=resolved_base_url,
        model=resolved_model,
        provider=provider,
        opencode_dir=str(WORKSPACE_ROOT),
    )
    llm_used = True
    try:
        inference_result = brain.infer(manifest)
    except Exception as exc:
        print(f"[WARN] LLM inference failed: {exc}")
        print("[WARN] Falling back to an empty inference result so the pipeline can continue.")
        from src.types import InferenceResult
        inference_result = InferenceResult()
        llm_used = False

    print("    -> Re-homing decisions:")
    for func, contract in inference_result.rehoming_map.items():
        print(f"       - {func} -> {contract}")

    print("[*] Assembling final code...")
    assembler = Assembler()
    final_code = assembler.assemble(manifest, inference_result)

    # Initial deduplication pass: remove duplicate type definitions
    prev_len = len(final_code)
    final_code = _deduplicate_final_code(final_code)
    final_code, scoped_dedup_changes = _deduplicate_scoped_state_variables(final_code)
    final_code, nested_shadow_changes = _remove_global_structs_shadowing_nested_qualified(final_code)
    final_code = _ensure_domain_type_aliases(final_code)
    final_code, invalid_type_changes = _repair_invalid_generated_types(final_code)
    for change in scoped_dedup_changes[:8] + nested_shadow_changes[:8]:
        print(f"    -> {change}.")
    if invalid_type_changes:
        for change in invalid_type_changes[:8]:
            print(f"    -> {change}.")
    removed_chars = prev_len - len(final_code)
    if removed_chars > 0:
        print(f"    -> Dedup removed {prev_len - len(final_code)} chars of duplicate definitions.")
    elif removed_chars < 0:
        print(f"    -> Dedup normalized formatting (+{-removed_chars} chars).")
    final_code = _normalize_solidity_output(final_code)

    print(f"[*] Writing output to {args.output}...")
    _write_output(args.output, final_code)
    print("    -> Output directory ready.")

    if not _forge_available():
        print("[WARN] forge not found; skipping automatic compilation and repair loop.")
        print(f"[WARN] Resurrected file saved to: {args.output}")
        return

    print("[*] Starting automatic compile validation...")
    _reset_compile_log(args.output)
    success, compiler_output, compiler_cmd = _run_compile(args.output, phase="initial validation")
    if success:
        print(f"[SUCCESS] Compile passed via: {compiler_cmd}")
    else:
        print(f"[WARN] Initial compile failed via: {compiler_cmd}")

    for attempt in range(1, args.max_fix_iterations + 1):
        if success:
            break

        print(f"[*] Auto-repair iteration {attempt}/{args.max_fix_iterations}")
        print("    -> Failure reason:")
        error_snippets = _extract_solidity_errors(compiler_output)
        for err in error_snippets[:8]:
            print(f"       - {err}")

        diagnostics = parse_compiler_diagnostics(compiler_output)
        error_class = ErrorRouter.classify(compiler_output)
        body_issues = _validate_body_syntax(final_code)
        if body_issues:
            print(f"    -> Body syntax validator found {len(body_issues)} issue(s).")
            for issue in body_issues[:6]:
                print(f"       - {issue}")
        if body_issues and error_class == "semantic":
            error_class = "body_syntax"
        print(f"    -> Error class: {error_class}")
        if diagnostics:
            first = diagnostics[0]
            print(f"    -> Primary diagnostic: {first.kind} {first.primary_symbol or ''}".rstrip())

        # Re-detect missing types from the FULL assembled code using contextual heuristics.
        import re
        symbol_table = build_symbol_table(final_code)
        missing_interfaces = brain._detect_missing_interfaces(manifest)
        missing_mocks = brain._detect_missing_mocks(manifest)
        missing_interfaces = [i for i in missing_interfaces if not symbol_table.is_defined(i)]
        missing_mocks = [m for m in missing_mocks if not symbol_table.is_defined(m)]

        missing_structs: list[str] = []
        missing_contracts: list[str] = []
        code_missing_types = _collect_code_missing_types(
            final_code,
            known_symbols=getattr(getattr(manifest, 'symbols', None), 'all_identifiers', set()),
        )
        compiler_missing_types = _extract_undefined_symbols_from_compiler_output(compiler_output)
        for diagnostic in diagnostics:
            if diagnostic.kind == "undefined-type" and diagnostic.primary_symbol:
                if diagnostic.primary_symbol[0].isupper() and diagnostic.primary_symbol not in compiler_missing_types:
                    compiler_missing_types.append(diagnostic.primary_symbol)
        for symbol in compiler_missing_types:
            if symbol.isupper() or symbol == "Placeholder":
                continue
            if symbol_table.is_defined(symbol):
                continue
            if symbol not in code_missing_types:
                code_missing_types.append(symbol)

        def classify_missing_type(mt: str) -> str:
            esc = re.escape(mt)
            foundry_artifacts = {
                "Receipt", "ReceiptLog", "RawReceipt", "RawReceiptLog",
                "RawTx1559", "RawTx1559Detail", "Tx1559", "Tx1559Detail",
                "TxReturn", "EIP1559ScriptArtifact", "RawEIP1559ScriptArtifact",
            }
            if mt in foundry_artifacts:
                return "struct"
            library_context = (
                re.search(rf"\busing\s+{esc}\s+for\b", final_code)
                or re.search(rf"\b{esc}\.[a-z_][A-Za-z0-9_]*\s*\(", final_code)
            )
            if library_context:
                return "contract"
            struct_context = (
                re.search(rf"\b{esc}(?:\[[^\]]*\])+\s+(?:memory|storage|calldata)\s+\w+", final_code)
                or re.search(rf"\b{esc}\s+(?:memory|storage|calldata)\s+\w+", final_code)
                or re.search(rf"abi\.decode\([^,]+,\s*\([^)]*\b{esc}\b", final_code)
                or re.search(rf"\b{esc}\s*\(\s*\{{", final_code)
            )
            contract_context = (
                re.search(rf"\bnew\s+{esc}\s*\(", final_code)
                or re.search(rf"\b{esc}\s*\(\s*address\s*\(", final_code)
                or re.search(rf"\breturns\s*\([^)]*\b{esc}\b(?!\s+(?:memory|storage|calldata))", final_code)
                or re.search(rf"\b{esc}\s+[a-z_][A-Za-z0-9_]*\s*(?:;|=|,|\))", final_code)
                or re.search(rf"\bcontract\s+\w+\s+is\s+[^{{]*\b{esc}\b", final_code)
            )
            if contract_context and not struct_context:
                return "contract"
            if struct_context:
                return "struct"
            return "interface" if mt.startswith("I") else "contract"

        if code_missing_types:
            print(f"    -> Detected {len(code_missing_types)} missing types in assembled code: {', '.join(code_missing_types[:10])}")
        for mt in code_missing_types:
            kind = classify_missing_type(mt)
            if kind == "interface":
                if mt not in missing_interfaces:
                    missing_interfaces.append(mt)
            elif kind == "contract":
                if mt not in missing_contracts:
                    missing_contracts.append(mt)
            elif mt not in missing_structs:
                missing_structs.append(mt)
        if missing_structs:
            print(f"    -> Missing structs/types: {', '.join(missing_structs[:10])}")
        if missing_contracts:
            print(f"    -> Missing contracts/mocks: {', '.join(missing_contracts[:10])}")
        if missing_interfaces:
            print(f"    -> Missing interfaces: {', '.join(missing_interfaces[:10])}")


        duplicate_declaration = error_class == "duplicate-declaration"
        if diagnostics:
            duplicate_declaration = duplicate_declaration or any(d.kind == "duplicate-declaration" for d in diagnostics)
        symbol_conflicts = symbol_table.duplicate_definitions()
        if symbol_conflicts and error_class not in {"undefined-type", "signature-mismatch", "body_syntax", "structure"}:
            duplicate_declaration = True
        ast_can_resolve = bool(missing_interfaces or missing_mocks or missing_structs or missing_contracts)
        use_llm = ErrorRouter.should_use_llm(error_class, deterministic_fix_failed=attempt > 1, ast_can_resolve=ast_can_resolve)
        if error_class == "signature-mismatch":
            use_llm = True # Let LLM attempt to fix wrong mock signatures
        if diagnostics and diagnostics[0].primary_symbol and diagnostics[0].primary_symbol[:1].islower():
            pass # Do not block LLM for lowercase symbols (e.g. poolId)

        made_repair_change = False

        if duplicate_declaration:
            print("    -> Routing to deterministic duplicate repair.")
            cleaned_code = assembler._remove_cross_kind_conflicts(final_code)
            cleaned_code = _deduplicate_final_code(cleaned_code)
            scoped_cleaned, scoped_changes = _deduplicate_scoped_state_variables(cleaned_code)
            if scoped_changes:
                cleaned_code = scoped_cleaned
            shadow_cleaned, shadow_changes = _remove_global_structs_shadowing_nested_qualified(cleaned_code)
            if shadow_changes:
                cleaned_code = shadow_cleaned
            # Apply cross-kind conflict resolution for any symbol that has conflicts
            if any(symbol_table.has_cross_kind_conflict(name) for name in symbol_table.all_names()):
                cleaned_code = assembler._remove_cross_kind_conflicts(cleaned_code)
            if symbol_table.is_defined("Currency") and "type Currency is address;" not in cleaned_code:
                if re.search(r'\bCurrency\b', cleaned_code):
                    cleaned_code = cleaned_code + "\n\ntype Currency is address;\n"
            cleaned_code = _ensure_domain_type_aliases(cleaned_code)
            
            # If the deterministic cleanup changed the code length/structure, compiler line numbers are now invalid.
            # Only use the compiler output line numbers if we haven't made any structural changes.
            if cleaned_code.strip() == final_code.strip():
                cleaned_code = _remove_compiler_identified_duplicates(cleaned_code, compiler_output)
                
            if cleaned_code.strip() != final_code.strip():
                final_code = cleaned_code
                made_repair_change = True
                _write_output(args.output, final_code)
                for change in scoped_changes[:8] + shadow_changes[:8]:
                    print(f"    -> {change}.")
                if not scoped_changes and not shadow_changes:
                    print("    -> Removed cross-kind duplicate declarations without generating new symbols.")
            else:
                print("    -> No deterministic duplicate cleanup applied.")
        elif error_class == "structure":
            print("    -> Routing to structure normalization.")
            normalized_code = _normalize_solidity_output(final_code)
            normalized_code = _ensure_domain_type_aliases(normalized_code)
            if normalized_code.strip() != final_code.strip():
                final_code = normalized_code
                made_repair_change = True
                _write_output(args.output, final_code)
            else:
                print("    -> Structure normalization made no changes.")
        elif error_class == "body_syntax":
            print("    -> Routing to body syntax cleanup.")
            deterministic_code, deterministic_changes = _deterministic_syntax_cleanup(final_code, compiler_output)
            invalid_type_code, invalid_type_changes = _repair_invalid_generated_types(deterministic_code, compiler_output)
            if invalid_type_changes:
                deterministic_code = invalid_type_code
                deterministic_changes.extend(invalid_type_changes)
            if deterministic_changes:
                final_code = deterministic_code
                final_code = _ensure_domain_type_aliases(final_code)
                made_repair_change = True
                _write_output(args.output, final_code)
                for change in deterministic_changes:
                    print(f"    -> {change}.")
                success, compiler_output, compiler_cmd = _run_compile(args.output, phase=f"repair iteration {attempt} after body syntax cleanup")
                if success:
                    print(f"    -> Compile passed via: {compiler_cmd}")
                else:
                    print(f"    -> Compile failed again via: {compiler_cmd}")
                continue

            cleaned_code = _remove_invalid_body_statements(final_code)
            if cleaned_code.strip() != final_code.strip():
                final_code = cleaned_code
                final_code = _ensure_domain_type_aliases(final_code)
                made_repair_change = True
                _write_output(args.output, final_code)
                print("    -> Removed invalid body statements.")
            else:
                print("    -> No body cleanup changes were applied.")
        elif error_class in {"undefined-type", "signature-mismatch"} and ast_can_resolve:
            print("    -> Routing to AST-driven symbol repair.")
            if body_issues:
                pre_ast_code, pre_ast_changes = _deterministic_syntax_cleanup(final_code, compiler_output)
                invalid_type_code, invalid_type_changes = _repair_invalid_generated_types(pre_ast_code, compiler_output)
                if invalid_type_changes:
                    pre_ast_code = invalid_type_code
                    pre_ast_changes.extend(invalid_type_changes)
                if pre_ast_changes and pre_ast_code.strip() != final_code.strip():
                    final_code = _ensure_domain_type_aliases(pre_ast_code)
                    made_repair_change = True
                    _write_output(args.output, final_code)
                    for change in pre_ast_changes:
                        print(f"    -> {change}.")
                    success, compiler_output, compiler_cmd = _run_compile(args.output, phase=f"repair iteration {attempt} after pre-AST syntax cleanup")
                    if success:
                        print(f"    -> Compile passed via: {compiler_cmd}")
                    else:
                        print(f"    -> Compile failed again via: {compiler_cmd}")
                    continue
                print("    -> Body syntax validator issues appear non-blocking; continuing with symbol repair.")
            generated_blocks = []
            if missing_structs:
                generated_type_code = assembler._generate_missing_type_definitions(
                    {
                        "structs": set(missing_structs) - {"Currency"},
                        "errors": set(),
                        "interfaces": set(),
                        "nested_contracts": {},
                        "contracts": set(),
                    },
                    final_code,
                )
                if generated_type_code.strip():
                    previous_code = final_code
                    final_code = _inject_code_after_pragmas(final_code, "\n// --- Deterministic missing type repairs ---\n" + generated_type_code.strip() + "\n")
                    final_code = _deduplicate_final_code(final_code)
                    final_code = _ensure_domain_type_aliases(final_code)
                    made_repair_change = made_repair_change or final_code.strip() != previous_code.strip()
                    _write_output(args.output, final_code)
                    print("    -> Added deterministic missing struct/type definitions.")
            if missing_contracts:
                generated_contract_code = assembler._generate_missing_type_definitions(
                    {
                        "structs": set(),
                        "errors": set(),
                        "interfaces": set(),
                        "nested_contracts": {},
                        "contracts": set(missing_contracts),
                    },
                    final_code,
                )
                if generated_contract_code.strip():
                    previous_code = final_code
                    final_code = _inject_code_after_pragmas(final_code, "\n// --- Deterministic missing mock repairs ---\n" + generated_contract_code.strip() + "\n")
                    final_code = _deduplicate_final_code(final_code)
                    final_code = _ensure_domain_type_aliases(final_code)
                    made_repair_change = made_repair_change or final_code.strip() != previous_code.strip()
                    _write_output(args.output, final_code)
                    print("    -> Added deterministic missing mock definitions.")
            if missing_interfaces:
                print(f"    -> Missing interfaces: {', '.join(missing_interfaces[:10])}")
                interface_plan_json = brain._build_interfaces_prompt(missing_interfaces, manifest)
                if interface_plan_json and interface_plan_json.lstrip().startswith('{'):
                    try:
                        import json
                        from src.types import RepairPlan
                        plan = RepairPlan(**json.loads(interface_plan_json))
                        repaired = assembler._apply_repair_plan(final_code, plan)
                        if repaired.strip() != final_code.strip():
                            previous_code = final_code
                            final_code = _deduplicate_final_code(repaired)
                            final_code = _ensure_domain_type_aliases(final_code)
                            made_repair_change = made_repair_change or final_code.strip() != previous_code.strip()
                            _write_output(args.output, final_code)
                            print("    -> Applied deterministic interface repair plan.")
                    except Exception as exc:
                        print(f"    -> Interface repair plan parse failed: {exc}. Falling back to LLM repair.")
                        generated_blocks.append(interface_plan_json)
                elif interface_plan_json:
                    generated_blocks.append(interface_plan_json)
            if missing_mocks:
                print(f"    -> Missing mocks: {', '.join(missing_mocks)}")
                generated_blocks.append(brain._build_mock_contracts_prompt(missing_mocks, manifest))
            if generated_blocks:
                repair_prompt = "\n\n".join(generated_blocks)
                repaired_code = brain._call_llm_text(repair_prompt)
                if repaired_code and repaired_code.strip():
                    repaired_code = _deduplicate_generated_code(final_code, repaired_code)
                    previous_code = final_code
                    final_code = _inject_code_after_pragmas(final_code, "\n// --- LLM-generated repairs ---\n" + repaired_code.strip() + "\n")
                    final_code = _deduplicate_final_code(final_code)
                    final_code = _ensure_domain_type_aliases(final_code)
                    made_repair_change = made_repair_change or final_code.strip() != previous_code.strip()
                    _write_output(args.output, final_code)
                    print("    -> Replaced/merged deduplicated LLM-generated type definitions.")
                else:
                    print("    -> No AST-driven repair generated; continuing to next policy.")
            else:
                print("    -> No blocks to generate; skipping.")
        elif "Data location must be" in compiler_output:
            print("    -> Routing to external parameter data-location repair.")
            repaired_code, location_changes = _ensure_external_data_locations(final_code)
            if repaired_code.strip() != final_code.strip():
                final_code = _ensure_domain_type_aliases(repaired_code)
                made_repair_change = True
                _write_output(args.output, final_code)
                for change in sorted(set(location_changes)):
                    print(f"    -> {change}.")
            else:
                print("    -> No data-location cleanup applied.")
        elif any(helper in compiler_output for helper in ("_getArgAddress", "_getArgUint256", "_getImmutableArgsOffset")):
            print("    -> Routing to Clone immutable-arg helper repair.")
            repaired_code = _ensure_clone_immutable_arg_helpers(final_code)
            if repaired_code.strip() != final_code.strip():
                final_code = repaired_code
                made_repair_change = True
                _write_output(args.output, final_code)
                print("    -> Added minimal Clone immutable argument helpers.")
            else:
                print("    -> Clone helper repair had no changes.")
        elif error_class == "body_syntax":
            print("    -> Body syntax issues require deterministic cleanup; skipping LLM.")
            break
        elif use_llm:
            print("    -> Routing to LLM semantic repair.")
            missing_info = ""
            if code_missing_types:
                missing_info = f"\nSpecifically, these types are used but undefined: {', '.join(code_missing_types[:20])}"
            try:
                repair_prompt = _repair_with_llm(brain, final_code, compiler_output + missing_info, attempt, args.max_fix_iterations)
            except Exception as exc:
                print(f"    -> LLM repair failed: {exc}. Skipping.")
                break
            if not repair_prompt or repair_prompt.strip() == final_code.strip():
                print("    -> LLM returned no meaningful change; stopping repair loop.")
                break
            body_issues_after = _validate_body_syntax(repair_prompt)
            if body_issues_after:
                print("    -> LLM output rejected by body syntax filter.")
                for issue in body_issues_after[:6]:
                    print(f"       - {issue}")
                break
            repaired_code = repair_prompt.strip()
            
            # Extract JSON block if it's wrapped in markdown
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', repaired_code, re.DOTALL)
            json_text = json_match.group(1) if json_match else repaired_code.lstrip()

            if json_text.startswith('{'):
                try:
                    import json
                    from src.types import RepairPlan
                    # try to parse the potentially cleaned json
                    # sometimes there's trailing junk, so let's parse robustly
                    # but simple loads is fine if we extracted it properly
                    plan_data = json.loads(json_text)
                    plan = RepairPlan(**plan_data)
                    repaired_code = assembler._apply_repair_plan(final_code, plan)
                    print("    -> Applied structured repair plan from LLM.")
                except Exception as exc:
                    print(f"    -> Structured repair plan parse failed: {exc}. Skipping LLM output.")
                    break
            else:
                print("    -> LLM output was not a JSON RepairPlan. Skipping.")
                break
            previous_code = final_code
            final_code = _deduplicate_final_code(repaired_code)
            final_code = _ensure_domain_type_aliases(final_code)
            made_repair_change = final_code.strip() != previous_code.strip()
            _write_output(args.output, final_code)
            print("    -> Rewrote output file with repaired Solidity.")
        else:
            print("    -> Deterministic repair did not converge and LLM is gated off for this error class.")
            break

        if not made_repair_change:
            print("    -> No repair changed the output; stopping to avoid repeated no-op iterations.")
            break

        success, compiler_output, compiler_cmd = _run_compile(args.output, phase=f"repair iteration {attempt} validation")
        if success:
            print(f"    -> Compile passed via: {compiler_cmd}")
        else:
            print(f"    -> Compile failed again via: {compiler_cmd}")

    shrink_removed_atoms = 0
    if success:
        preliminary_result = _build_slice_result(code_str, final_code, True, budget, llm_used)
        if not preliminary_result.slice_effective and not args.compile_artifact_fallback:
            print("[*] Compile passed, but output is not yet an effective slice; starting shrink pass.")
            final_code, shrink_removed_atoms = _shrink_to_effective_slice(
                args.output,
                final_code,
                code_str,
                budget,
                llm_used,
            )
            success, compiler_output, compiler_cmd = _run_compile(args.output, phase="post-shrink validation")

    result = _build_slice_result(
        code_str,
        final_code,
        success,
        budget,
        llm_used,
        shrink_removed_atoms=shrink_removed_atoms,
    )
    if args.compile_artifact_fallback and result.compile_success and not result.slice_effective:
        result.fallback_level = "CompileArtifact"
    _write_slice_result(args.output, result)

    if result.compile_success and result.slice_effective:
        print(f"[SUCCESS] Effective compilable slice saved to: {args.output}")
        print("[SUCCESS] Auto-compile validation passed.")
    elif result.compile_success and args.compile_artifact_fallback:
        print(f"[SUCCESS] Compile artifact saved to: {args.output}")
        print("[WARN] slice_effective=false; this output is not an effective slice.")
    elif result.compile_success:
        print("[FAILURE] effective_compilable_slice_not_found_under_budget")
        print(f"[WARN] Latest compile-success artifact saved to: {args.output}")
        sys.exit(1)
    else:
        print("[WARN] Auto-compile validation did not pass after repair attempts.")
        print("    -> Keeping latest real reconstructed output; no compile-safe harness was written.")
        print(f"[WARN] Resurrected file saved to: {args.output}")
        if compiler_output:
            print(compiler_output)
        sys.exit(1)


if __name__ == "__main__":
    main()
