from .types import SymbolManifest, InferenceResult, SymbolIndex, RepairAction, RepairPlan
from .code_normalizer import normalize_primitive_type_aliases
import re

class Assembler:
    def _build_symbol_index(self, manifest: SymbolManifest) -> SymbolIndex:
        symbols = manifest.symbols if hasattr(manifest, 'symbols') else SymbolIndex()
        return symbols

    def _normalize_repair_plan(self, plan) -> RepairPlan:
        if isinstance(plan, RepairPlan):
            return plan
        if isinstance(plan, dict):
            actions = [RepairAction(**a) if not isinstance(a, RepairAction) else a for a in plan.get('actions', [])]
            return RepairPlan(category=plan.get('category', 'semantic'), rationale=plan.get('rationale', ''), actions=actions, reject_reason=plan.get('reject_reason'))
        return RepairPlan(category='semantic', reject_reason='unsupported repair plan payload')

    def _apply_repair_plan(self, code: str, plan: RepairPlan) -> str:
        import json
        try:
            print("PLAN ACTIONS:", json.dumps([{"action": a.action, "target": a.target} for a in plan.actions]))
        except Exception as e:
            print("PLAN PRINT ERROR:", e)
        plan = self._normalize_repair_plan(plan)
        if plan.reject_reason:
            return code
        updated = code
        for action in plan.actions:
            if action.action == 'remove_definition':
                # Catastrophic bug fix: avoid greedy `(?s).*` which wipes the whole file
                # Instead, just remove the line containing the exact target if it's a simple declaration,
                # and rely on `_deduplicate_final_code` for larger blocks.
                updated = re.sub(rf'(?m)^[ \t]*.*\b{re.escape(action.target)}\b.*?;[ \t]*$', '', updated)
            elif action.action == 'add_type_definition':
                updated = updated.rstrip() + '\n\n' + action.details.get('code', '') + '\n'
            elif action.action == 'replace_function_body':
                target = action.target
                body = action.details.get('code', 'revert("repair plan applied");')
                pattern = r'(function\s+' + re.escape(target) + r'\s*\([^)]*\)\s*[^\{;]*\{)(.*?)(\n\s*\})'
                updated = re.sub(
                    pattern,
                    lambda m: m.group(1) + "\n        " + body + "\n" + m.group(3),
                    updated,
                    flags=re.DOTALL,
                )
            elif action.action == 'replace_function':
                target = action.target
                code_to_insert = action.details.get('code', '')
                
                # Manual replacement using depth counting
                lines = updated.split('\n')
                out = []
                i = 0
                replaced = False
                while i < len(lines):
                    m = re.search(r'\bfunction\s+' + re.escape(target) + r'\s*\(', lines[i])
                    if m:
                        replaced = True
                        depth = lines[i].count('{') - lines[i].count('}')
                        if '{' in lines[i] and depth <= 0:
                            # Single line function or interface signature
                            out.append(code_to_insert)
                            i += 1
                            continue
                            
                        # Multiline function
                        has_brace = '{' in lines[i]
                        i += 1
                        while i < len(lines):
                            if not has_brace and '{' in lines[i]:
                                has_brace = True
                            depth += lines[i].count('{') - lines[i].count('}')
                            if has_brace and depth <= 0:
                                i += 1
                                break
                            elif not has_brace and ';' in lines[i]:
                                i += 1
                                break
                            i += 1
                        out.append(code_to_insert)
                    else:
                        out.append(lines[i])
                        i += 1
                updated = '\n'.join(out)
                if replaced:
                    print(f"    -> Applied action `replace_function` to `{target}`.")
            elif action.action == 'add_function_body':
                target = action.target
                body = action.details.get('code', 'revert("repair plan applied");')
                pattern = r'(function\s+' + re.escape(target) + r'\s*\([^)]*\)\s*[^\{;]*)(;|\n\s*\{\s*\})'
                updated = re.sub(
                    pattern,
                    lambda m: m.group(1) + " {\n        " + body + "\n    }",
                    updated,
                    count=1,
                    flags=re.DOTALL,
                )
            elif action.action == 'add_state_variable':
                target = action.target
                code = action.details.get('code', '')
                pattern = r'(\b(?:contract|interface|library)\s+' + re.escape(target) + r'(?:\s+is\s+[^\{]+)?\s*\{)'
                updated = re.sub(
                    pattern,
                    lambda m: m.group(1) + "\n    " + code,
                    updated,
                    count=1,
                    flags=re.DOTALL,
                )
        return updated

    def _normalize_symbol_name(self, name: str) -> str:
        return name.strip()

    def _type_name_conflicts(self, name: str, symbol_index: SymbolIndex) -> bool:
        normalized = self._normalize_symbol_name(name)
        return normalized in symbol_index.all_identifiers or normalized in symbol_index.conflicts

    def _register_identifier(self, symbol_index: SymbolIndex, name: str, kind: str) -> None:
        normalized = self._normalize_symbol_name(name)
        symbol_index.all_identifiers.add(normalized)
        symbol_index.conflicts.setdefault(normalized, set()).add(kind)

    def _collect_defined_names(self, code: str) -> set[str]:
        import re
        names = set()
        patterns = [
            r'\bcontract\s+(\w+)',
            r'\binterface\s+(\w+)',
            r'\blibrary\s+(\w+)',
            r'\bstruct\s+(\w+)',
            r'\benum\s+(\w+)',
            r'\berror\s+(\w+)\s*[\(;]',
            r'\btype\s+(\w+)\s+is\s+',
            r'\bevent\s+(\w+)\s*\(',
            r'\bfunction\s+(\w+)\s*\(',
        ]
        for pattern in patterns:
            names.update(re.findall(pattern, code))
        return {self._normalize_symbol_name(name) for name in names}

    def _split_top_level_blocks(self, code: str) -> list[tuple[str, str]]:
        import re
        blocks = []
        lines = code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            m = re.match(r'^(contract|interface|library|struct|enum)\s+(\w+)\b', stripped)
            if not m:
                i += 1
                continue
            start = i
            depth = line.count('{') - line.count('}')
            i += 1
            seen_open = '{' in line
            while i < len(lines):
                depth += lines[i].count('{') - lines[i].count('}')
                seen_open = seen_open or ('{' in lines[i])
                if seen_open and depth <= 0:
                    i += 1
                    break
                i += 1
            blocks.append((m.group(2), '\n'.join(lines[start:i])))
        return blocks

    def _sanitize_identifier(self, name: str, symbol_index: SymbolIndex, prefix: str = "_") -> str:
        if not self._type_name_conflicts(name, symbol_index):
            self._register_identifier(symbol_index, name, "generated")
            return name
        candidate = f"{prefix}{name}"
        suffix = 1
        while self._type_name_conflicts(candidate, symbol_index):
            candidate = f"{prefix}{name}_{suffix}"
            suffix += 1
        self._register_identifier(symbol_index, candidate, "generated")
        return candidate

    def _rewrite_variable_declarations(self, code: str, symbol_index: SymbolIndex) -> str:
        """Preserve source identifiers.

        This used to rewrite every declaration-like line using the global symbol
        table. That is unsafe for Solidity because multiline function parameters
        look exactly like variable declarations, e.g. `address target,`. Renaming
        such parameters without rewriting all references in the function body
        creates undeclared identifiers (`target` vs `_target`). Name repair must
        be driven by a scoped AST or by compiler diagnostics, not by a global
        regex sweep.
        """
        return code

    def _filter_candidate_types(self, code: str, candidates: set[str], symbol_index: SymbolIndex) -> set[str]:
        import re
        filtered = set()
        allowed_contexts = [
            r'new\s+{name}\s*\(',
            r'\b{name}\[\]\s+(?:memory|storage|calldata)?\s+\w+',
            r'abi\.decode\([^,]+,\s*\([^)]*\b{name}\b',
            r'\b(?:contract|interface|struct|error|type|library|enum)\s+{name}\b',
            r'\b{name}\s+(?:memory|storage|calldata)\s+\w+',
            r'\b{name}\.[A-Za-z_][A-Za-z0-9_]*\b',
            r'\b{name}\s+\w+\s*(?:;|=|,|\))',
        ]
        noisy_text_tokens = {
            'Error', 'Test', 'Clone', 'PoC', 'Call', 'StaticCall',
            'Token', 'Tokens', 'Mock', 'Mocks', 'Data', 'Info', 'State',
            'Address', 'Context', 'Transaction', 'Transactions',
        }
        noisy_suffixes = (
            '_mockValues', '_mockBools', '_mockAddresses', '_mockBytes32',
            '_mockPositionBalances', '_mockNumLegs',
        )
        defined_names = set(re.findall(r'\b(?:contract|interface|library|struct|enum|error|type)\s+(\w+)\b', code))
        function_names = set(re.findall(r'\bfunction\s+(\w+)\s*\(', code))
        for candidate in candidates:
            name = self._normalize_symbol_name(candidate)
            if name in symbol_index.all_identifiers or name in symbol_index.conflicts:
                continue
            if name in defined_names or name in function_names:
                continue
            if name.startswith('_') or name.isupper() or len(name) <= 1:
                continue
            if any(name.endswith(suffix) for suffix in noisy_suffixes):
                continue
            if not name[0].isupper():
                continue
            if name in noisy_text_tokens:
                continue
            for pattern in allowed_contexts:
                if re.search(pattern.format(name=re.escape(name)), code):
                    filtered.add(name)
                    break
        return filtered

    def _resolve_currency_type(self, code_context: str) -> str:
        import re
        if re.search(r'\bCurrency\b\s+\w+\s*(?:;|=|,|\))', code_context):
            return 'type Currency is address;'
        return ''

    def _remove_cross_kind_conflicts(self, code: str) -> str:
        import re
        defined_types = set(re.findall(r'\b(?:contract|interface|library|struct|enum|error|type)\s+(\w+)\b', code))
        lines = code.split('\n')
        filtered = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r'^(\s*function\s+)(\w+)(\s*\()', line)
            if m and m.group(2) in defined_types:
                depth = line.count('{') - line.count('}')
                seen_open = '{' in line
                i += 1
                while i < len(lines) and (not seen_open or depth > 0):
                    depth += lines[i].count('{') - lines[i].count('}')
                    seen_open = seen_open or ('{' in lines[i])
                    i += 1
                continue
            filtered.append(line)
            i += 1
        return '\n'.join(filtered)

    def _strip_headers(self, code: str) -> str:
        """移除代码中的 SPDX license、pragma 语句和所有注释"""
        import re
        
        # 首先移除所有多行注释 (/* ... */)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code, flags=re.MULTILINE)
        
        # 移除所有 import 语句
        code = re.sub(r'import\s+[^;]+;', '', code)
        
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过 SPDX 和 pragma 行
            if stripped.startswith('// SPDX-License-Identifier') or stripped.startswith('pragma '):
                continue
            
            # 跳过单行注释
            if stripped.startswith('//'):
                continue
            
            # 跳过以 * 开头的行（注释残留，包括 "* @dev" 等）
            if stripped.startswith('*'):
                continue
            
            # 移除行尾注释
            line = re.sub(r'//.*$', '', line)
            
            # 如果处理后的行不为空或只是空白，保留它
            if line.strip():
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _fix_function_visibility(self, code: str) -> str:
        """
        为缺少 visibility 的函数添加 internal 修饰符
        顶层函数移动到合约中时需要显式 visibility
        """
        lines = code.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 检查是否是函数声明行
            if stripped.startswith('function '):
                # 检查是否已有 visibility 关键字
                has_visibility = any(vis in stripped for vis in ['public', 'private', 'internal', 'external'])
                
                # 如果没有 visibility，添加 internal
                if not has_visibility:
                    # 在 function 关键字后插入 visibility
                    # 需要小心处理多行函数签名
                    if 'pure' in stripped or 'view' in stripped or 'returns' in stripped or '(' in stripped:
                        # 这是函数签名行，在适当位置插入 internal
                        # 简化处理：在函数签名后、第一个修饰符前添加
                        result_lines.append(line)  # 先保留原样
                        # 在下一行或当前行的合适位置添加 internal
                        # 为了简化，我们在函数声明后立即添加一个带 internal 的修改版本
                        # 实际应该更智能地处理
                        continue
                    
            result_lines.append(line)
        
        # 更简单的方法：使用正则表达式
        # 匹配 function xxx(...) 后面没有 visibility 关键字的情况
        code = '\n'.join(result_lines)
        
        # 正则：function name(...) 后跟 pure/view/returns，但之前没有 public/private/internal/external
        # 这是一个简化的实现
        pattern = r'(\s*function\s+\w+\s*\([^)]*\))\s+(pure|view|returns|payable|\{)'
        
        def add_internal(match):
            func_sig = match.group(1)
            next_keyword = match.group(2)
            # 检查 func_sig 中是否已有 visibility
            if not any(vis in func_sig for vis in ['public', 'private', 'internal', 'external']):
                return f'{func_sig} internal {next_keyword}'
            return match.group(0)
        
        code = re.sub(pattern, add_internal, code)
        
        return code
    
    def _extract_undeclared_variables(self, code: str) -> list[tuple[str, str]]:
        """Infer state variables from strong constructor-assignment evidence.
        
        Returns:
            List of (variable_name, type_name) tuples
        """
        import re
        results = []
        for var_name, type_name in re.findall(r'\b([a-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Z][A-Za-z0-9_]*)\s*\(', code):
            results.append((var_name, type_name))
        return results

    def _state_var_name_conflicts_with_type(self, name: str, symbol_index: SymbolIndex) -> bool:
        """Only type-level names are unsafe for generated state variables."""
        type_names = (
            symbol_index.contracts
            | symbol_index.interfaces
            | symbol_index.libraries
            | symbol_index.structs
            | symbol_index.errors
            | symbol_index.enums
            | symbol_index.types
        )
        return name in type_names
    
    def _extract_used_state_variables(self, code: str, existing_vars: set) -> list[tuple[str, str]]:
        """Do not infer state from arbitrary identifier usage.

        Previous logic treated `users[i]`, `defaultTicks[i]`, `_array[i]`, and
        local `.push()` calls as undeclared storage, then injected mappings into
        the contract. That creates shadowing and changes test semantics. State
        synthesis must be driven by declarations/assignments with strong
        evidence or compiler diagnostics, not by every indexed local variable.
        """
        return []

    def _remove_unindented_function_blocks(self, code: str) -> str:
        """Drop orphan functions accidentally swallowed into a contract shell."""
        lines = code.split('\n')
        filtered = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r'^function\s+\w+\s*\(', line):
                depth = line.count('{') - line.count('}')
                seen_open = '{' in line
                i += 1
                while i < len(lines):
                    depth += lines[i].count('{') - lines[i].count('}')
                    seen_open = seen_open or ('{' in lines[i])
                    i += 1
                    if seen_open and depth <= 0:
                        break
                continue
            filtered.append(line)
            i += 1
        return '\n'.join(filtered)

    def _extract_function_signatures(self, code: str) -> set:
        """从代码中提取所有函数签名（函数名）"""
        import re
        pattern = r'function\s+(\w+)\s*\('
        names = set(re.findall(pattern, code))
        struct_names = set(re.findall(r'\bstruct\s+(\w+)\s*\{', code))
        error_names = set(re.findall(r'\berror\s+(\w+)\s*\(', code))
        type_names = set(re.findall(r'\btype\s+(\w+)\s+is\s+', code))
        return {name for name in names if name not in struct_names and name not in error_names and name not in type_names}
    
    def _extract_referenced_types(self, code: str) -> dict:
        """提取代码中引用但可能未定义的类型"""
        import re
        from .symbol_table import build_symbol_table

        code_for_scan = self._strip_comments_for_inference(code)
        code_for_scan = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', code_for_scan)
        referenced = {'structs': set(), 'errors': set(), 'interfaces': set(),
                      'nested': {}, 'contracts': set(), 'enums': set(), 'types': set()}
        defined_names = build_symbol_table(code_for_scan).all_names()

        for contract_name, type_name in re.findall(r'\b([A-Z][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b', code_for_scan):
            if contract_name not in ['abi', 'msg', 'block', 'tx', 'type', 'vm', 'console', 'console2', 'super']:
                if type_name[0].isupper():
                    referenced['nested'].setdefault(contract_name, set()).add(type_name)
                else:
                    referenced['contracts'].add(contract_name)

        referenced['contracts'].update(re.findall(r'\bnew\s+([A-Z]\w+)', code_for_scan))
        referenced['contracts'].update(re.findall(r'\b([A-Z][A-Za-z0-9_]*)\s*\(\s*address\s*\(', code_for_scan))
        referenced['contracts'].update(re.findall(r'\breturns\s*\([^)]*\b([A-Z][A-Za-z0-9_]*)\b(?!\s+(?:memory|storage|calldata))', code_for_scan))
        for bases in re.findall(r'\bcontract\s+\w+\s+is\s+([^{]+)\{', code_for_scan):
            for base in bases.split(','):
                base_match = re.match(r'\s*([A-Z][A-Za-z0-9_]*)', base)
                if base_match:
                    referenced['contracts'].add(base_match.group(1))
        referenced['contracts'].update(referenced['nested'].keys())
        referenced['errors'].update(re.findall(r'revert\s+([A-Z]\w+)\s*\(', code_for_scan))
        referenced['interfaces'].update(re.findall(r'\b(I[A-Z][A-Za-z0-9_]*)\s*\(', code_for_scan))

        struct_patterns = [
            r'\b([A-Z][A-Za-z0-9_]*)(?:\[[^\]]*\])+\s+(?:memory|storage|calldata)\s+\w+',
            r'\b([A-Z][A-Za-z0-9_]*)\s+(?:memory|storage|calldata)\s+\w+',
            r'abi\.decode\([^,]+,\s*\([^)]*\b([A-Z][A-Za-z0-9_]*)\b',
            r'\b([A-Z][A-Za-z0-9_]*)\s*\(\s*\{',
        ]
        for pattern in struct_patterns:
            referenced['structs'].update(re.findall(pattern, code_for_scan))

        value_type_patterns = [
            r'\b([A-Z][A-Za-z0-9_]*)\s+[a-z_][A-Za-z0-9_]*\s*(?:;|=|,|\))',
            r'\bfunction\s+\w+\s*\([^)]*\b([A-Z][A-Za-z0-9_]*)\s+[a-z_][A-Za-z0-9_]*',
        ]
        for pattern in value_type_patterns:
            for name in re.findall(pattern, code_for_scan):
                if name not in referenced['structs']:
                    referenced['contracts'].add(name)

        referenced['structs'] -= referenced['contracts']
        referenced['interfaces'] -= defined_names
        referenced['errors'] -= defined_names
        referenced['contracts'] -= defined_names
        referenced['structs'] -= defined_names
        return referenced
    
    def _extract_defined_types(self, code: str) -> dict:
        """提取代码中已定义的所有类型"""
        import re
        from .symbol_table import build_symbol_table

        defined = {'structs': set(), 'errors': set(), 'interfaces': set(), 'contracts': set(), 'types': set(), 'enums': set(), 'libraries': set()}
        table = build_symbol_table(code)
        for record in table.records:
            if record.kind == 'struct':
                defined['structs'].add(record.name)
            elif record.kind == 'error':
                defined['errors'].add(record.name)
            elif record.kind == 'interface':
                defined['interfaces'].add(record.name)
            elif record.kind == 'contract':
                defined['contracts'].add(record.name)
            elif record.kind == 'library':
                defined['libraries'].add(record.name)
            elif record.kind == 'enum':
                defined['enums'].add(record.name)
            elif record.kind == 'type':
                defined['types'].add(record.name)
        return defined
    
    def _generate_missing_type_definitions(self, missing_types: dict, code_context: str = "") -> str:
        """为缺失的类型生成完整定义 —— mock contracts/interfaces/structs/errors"""
        import re
        lines = []
        
        # --- 1. 生成缺失的 struct 定义（从上下文推断字段）---
        missing_structs = set(missing_types.get('structs', set()))
        defined_in_context = set(re.findall(r'\b(?:contract|interface|library|struct|enum|error|type)\s+(\w+)\b', code_context))
        # Known schemas may reference other known schemas (e.g. Receipt -> ReceiptLog,
        # RawTx1559 -> RawTx1559Detail -> AccessList).  Close over those dependencies
        # before generating, otherwise the first deterministic injection can still
        # leave immediately undefined nested artifact types behind.
        changed = True
        while changed:
            changed = False
            for struct_name in list(missing_structs):
                schema = self._known_struct_schema(struct_name)
                if not schema:
                    continue
                for dep in re.findall(r'\b([A-Z][A-Za-z0-9_]*)\b', schema):
                    if dep in {struct_name, 'String', 'Bytes'} or dep in defined_in_context:
                        continue
                    if self._known_struct_schema(dep) and dep not in missing_structs:
                        missing_structs.add(dep)
                        changed = True

        for struct_name in sorted(missing_structs):
            if re.match(r'^I[A-Z][A-Za-z0-9_]*$', struct_name):
                continue
            struct_def = self._synthesize_struct(struct_name, code_context)
            if struct_def:
                lines.append(struct_def)
                lines.append('')
        
        # --- 2. 生成缺失的 error 定义 ---
        if missing_types.get('errors'):
            lines.append('// Auto-generated error definitions')
            for error_name in sorted(missing_types['errors']):
                lines.append(f'error {error_name}();')
            lines.append('')
        
        # --- 3. 生成缺失的 interface 定义（从调用上下文推导方法）---
        for interface_name in sorted(missing_types.get('interfaces', set())):
            iface = self._synthesize_minimal_interface(interface_name, code_context)
            if iface:
                lines.append(iface)
                lines.append('')
        
        # --- 4. 为缺失的合约/接口类型生成 mock contracts ---
        # 收集所有缺失的非结构体类型（它们需要 mock contracts）
        missing_contracts = set(missing_types.get('contracts', set()))
        
        # 合约类型：从 interfaces 集合中挑出那些更像合约名的符号
        for name in sorted(missing_types.get('interfaces', set())):
            if name not in missing_types.get('structs', set()) and not re.match(r'^I[A-Z][A-Za-z0-9_]*$', name):
                missing_contracts.add(name)
        
        # 嵌套类型中的合约也需要生成
        nested_contracts = missing_types.get('nested_contracts', {})
        for contract_name in sorted(nested_contracts.keys()):
            missing_contracts.add(contract_name)
        
        if missing_contracts:
            lines.append('// Auto-generated mock contracts for missing types')
            for contract_name in sorted(missing_contracts):
                mock = self._synthesize_mock_contract(contract_name, code_context,
                                                      nested_contracts.get(contract_name, set()))
                if mock:
                    lines.append(mock)
                    lines.append('')
        
        return '\n'.join(lines)

    def _synthesize_struct(self, struct_name: str, code_context: str) -> str:
        """从上下文推断 struct 字段"""
        import re
        known = self._known_struct_schema(struct_name)
        if known:
            return known
        var_types = self._infer_variable_types(code_context)
        # Look for struct construction patterns: StructName({field1: val1, field2: val2})
        esc = re.escape(struct_name)
        pattern = r'\b(?:[A-Za-z0-9_]+\.)?' + esc + r'\s*\(\{\s*([^}]*)\}\s*\)'
        match = re.search(pattern, code_context, re.DOTALL)
        if match:
            fields_str = match.group(1)
            # Parse field:value pairs
            field_parts = re.findall(r'(\w+)\s*:\s*([^,]+(?:\([^)]*\))?)', fields_str)
            if field_parts:
                fields = []
                for fname, fval in field_parts:
                    ftype = self._infer_expression_type(fval, var_types)
                    fields.append(f'    {ftype} {fname};')
                if fields:
                    return f'struct {struct_name} {{\n' + '\n'.join(fields) + '\n}'
        # Fallback: single placeholder field
        return f'struct {struct_name} {{\n    bytes data;\n}}'

    def _known_struct_schema(self, struct_name: str) -> str:
        schemas = {
            "AccessList": [
                "address accessAddress;",
                "bytes32[] storageKeys;",
            ],
            "RawTx1559Detail": [
                "AccessList[] accessList;",
                "bytes data;",
                "address from;",
                "bytes gas;",
                "bytes nonce;",
                "address to;",
                "bytes txType;",
                "bytes value;",
            ],
            "Tx1559Detail": [
                "AccessList[] accessList;",
                "bytes data;",
                "address from;",
                "uint256 gas;",
                "uint256 nonce;",
                "address to;",
                "uint256 txType;",
                "uint256 value;",
            ],
            "RawTx1559": [
                "string[] arguments;",
                "address contractAddress;",
                "string contractName;",
                "string functionSig;",
                "bytes32 hash;",
                "RawTx1559Detail txDetail;",
                "string opcode;",
            ],
            "Tx1559": [
                "string[] arguments;",
                "address contractAddress;",
                "string contractName;",
                "string functionSig;",
                "bytes32 hash;",
                "Tx1559Detail txDetail;",
                "string opcode;",
            ],
            "RawReceiptLog": [
                "address logAddress;",
                "bytes32 blockHash;",
                "bytes blockNumber;",
                "bytes data;",
                "bytes logIndex;",
                "bool removed;",
                "bytes32[] topics;",
                "bytes32 transactionHash;",
                "bytes transactionIndex;",
                "bytes transactionLogIndex;",
            ],
            "ReceiptLog": [
                "address logAddress;",
                "bytes32 blockHash;",
                "uint256 blockNumber;",
                "bytes data;",
                "uint256 logIndex;",
                "bytes32[] topics;",
                "uint256 transactionIndex;",
                "uint256 transactionLogIndex;",
                "bool removed;",
            ],
            "RawReceipt": [
                "bytes32 blockHash;",
                "bytes blockNumber;",
                "address contractAddress;",
                "bytes cumulativeGasUsed;",
                "bytes effectiveGasPrice;",
                "address from;",
                "bytes gasUsed;",
                "RawReceiptLog[] logs;",
                "bytes logsBloom;",
                "bytes status;",
                "address to;",
                "bytes32 transactionHash;",
                "bytes transactionIndex;",
            ],
            "Receipt": [
                "bytes32 blockHash;",
                "uint256 blockNumber;",
                "address contractAddress;",
                "uint256 cumulativeGasUsed;",
                "uint256 effectiveGasPrice;",
                "address from;",
                "uint256 gasUsed;",
                "ReceiptLog[] logs;",
                "bytes logsBloom;",
                "uint256 status;",
                "address to;",
                "bytes32 transactionHash;",
                "uint256 transactionIndex;",
            ],
            "TxReturn": [
                "string internalType;",
                "string value;",
            ],
            "EIP1559ScriptArtifact": [
                "string[] libraries;",
                "string path;",
                "string[] pending;",
                "Receipt[] receipts;",
                "uint256 timestamp;",
                "Tx1559[] transactions;",
                "TxReturn[] txReturns;",
            ],
            "RawEIP1559ScriptArtifact": [
                "string[] libraries;",
                "string path;",
                "string[] pending;",
                "RawReceipt[] receipts;",
                "TxReturn[] txReturns;",
                "uint256 timestamp;",
                "RawTx1559[] transactions;",
            ],
        }
        fields = schemas.get(struct_name)
        if not fields:
            return ""
        return f"struct {struct_name} {{\n" + "\n".join(f"    {field}" for field in fields) + "\n}"

    def _split_call_args(self, raw_args: str) -> list[str]:
        args = []
        current = []
        depth = 0
        quote = None
        i = 0
        while i < len(raw_args):
            ch = raw_args[i]
            if quote:
                current.append(ch)
                if ch == quote and (i == 0 or raw_args[i - 1] != '\\'):
                    quote = None
            else:
                if ch in ("'", '"'):
                    quote = ch
                    current.append(ch)
                elif ch in "([{":
                    depth += 1
                    current.append(ch)
                elif ch in ")]}":
                    depth = max(0, depth - 1)
                    current.append(ch)
                elif ch == "," and depth == 0:
                    arg = "".join(current).strip()
                    if arg:
                        args.append(arg)
                    current = []
                else:
                    current.append(ch)
            i += 1
        arg = "".join(current).strip()
        if arg:
            args.append(arg)
        return args

    def _find_balanced_calls(self, code: str, receiver: str | None = None, contract_name: str | None = None) -> list[tuple[str, list[str], int, int]]:
        import re
        if receiver:
            pattern = re.compile(r'\b' + re.escape(receiver) + r'\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(')
        elif contract_name:
            pattern = re.compile(r'\bnew\s+' + re.escape(contract_name) + r'\s*\(')
        else:
            return []
        calls = []
        for match in pattern.finditer(code):
            depth = 1
            quote = None
            i = match.end()
            while i < len(code):
                ch = code[i]
                if quote:
                    if ch == quote and code[i - 1] != '\\':
                        quote = None
                else:
                    if ch in ("'", '"'):
                        quote = ch
                    elif ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            raw_args = code[match.end():i]
                            fn_name = match.group(1) if receiver else "__constructor__"
                            calls.append((fn_name, self._split_call_args(raw_args), match.start(), i + 1))
                            break
                i += 1
        return calls

    def _infer_variable_types(self, code_context: str) -> dict[str, str]:
        import re
        var_types: dict[str, str] = {}
        code_context = self._strip_comments_for_inference(code_context)
        type_pattern = r'(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])*'
        for type_name, var_name in re.findall(
            rf'\b({type_pattern}|address|bool|string|bytes(?:\d+)?|u?int\d*)\s+(?:constant\s+|immutable\s+)?(?:memory\s+|storage\s+|calldata\s+)?([A-Za-z_][A-Za-z0-9_]*)\b',
            code_context,
        ):
            if not self._is_usable_solidity_type(type_name):
                continue
            var_types[var_name] = type_name
        for var_name, type_name in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', code_context):
            var_types[var_name] = type_name
        for var_name, type_name in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*address\s*\(', code_context):
            var_types[var_name] = type_name
        return var_types

    def _strip_comments_for_inference(self, code_context: str) -> str:
        import re
        code_context = re.sub(r'/\*[\s\S]*?\*/', ' ', code_context)
        code_context = re.sub(r'//.*', ' ', code_context)
        return code_context

    def _is_usable_solidity_type(self, type_name: str) -> bool:
        import re
        if not type_name:
            return False
        normalized = type_name.strip()
        invalid_words = {
            'function', 'contract', 'struct', 'event', 'error', 'return',
            'memory', 'storage', 'calldata', 'constant', 'immutable',
            'public', 'private', 'internal', 'external', 'view', 'pure',
            'on', 'the', 'current', 'token', 'tokens', 'deltas',
        }
        if normalized in invalid_words:
            return False
        if normalized == 'address payable':
            return True
        if re.match(r'^(?:u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)?|address|bool|string|bytes(?:[1-9]|[12][0-9]|3[0-2])?)(?:\[[^\]]*\])*$', normalized):
            return True
        if re.match(r'^[A-Z][A-Za-z0-9_]*(?:\.[A-Z][A-Za-z0-9_]*)?(?:\[[^\]]*\])*$', normalized):
            return True
        return False

    def _infer_expression_type(self, expr: str, var_types: dict[str, str]) -> str:
        import re
        value = expr.strip()
        if value in var_types and self._is_usable_solidity_type(var_types[value]):
            return var_types[value]
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\[[^\]]+\]$', value):
            base = value.split('[', 1)[0]
            base_type = var_types.get(base)
            if base_type and base_type.endswith('[]'):
                return base_type[:-2]
            if base_type and re.match(r'^[A-Za-z_][A-Za-z0-9_]*\[\d+\]$', base_type):
                return base_type.rsplit('[', 1)[0]
        if re.match(r'^address\s*\(', value) or re.match(r'^payable\s*\(', value) or re.match(r'^0x[a-fA-F0-9]{40}$', value):
            return 'address'
        if re.match(r'^(true|false)$', value, re.I):
            return 'bool'
        if value.startswith(('"', "'")):
            return 'string memory'
        if re.match(r'^bytes\d*\s*\(', value) or re.match(r'^hex["\']', value):
            return 'bytes memory'
        if re.match(r'^bytes32\s*\(', value) or re.match(r'^(keccak256|sha256)\s*\(', value):
            return 'bytes32'
        if re.match(r'^int(?:8|16|24|32|64|128|256)?\s*\(', value):
            m = re.match(r'^(int(?:8|16|24|32|64|128|256)?)', value)
            return m.group(1)
        if re.match(r'^uint(?:8|16|24|32|64|128|256)?\s*\(', value):
            m = re.match(r'^(uint(?:8|16|24|32|64|128|256)?)', value)
            return m.group(1)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*\(', value):
            fn_name = value.split('(')[0].strip()
            if fn_name == 'oracleContract':
                return 'IV3CompatibleOracle'
            if fn_name == '_V4PoolId':
                return 'PoolId'
            if fn_name == 'poolKey':
                return 'PoolKey'
        wrap_match = re.match(r'^([A-Z][A-Za-z0-9_]*)\.wrap\s*\(', value)
        if wrap_match:
            return wrap_match.group(1)
        if re.match(r'^[A-Z][A-Za-z0-9_]*\.[a-z_][A-Za-z0-9_]*\s*\(', value):
            if '.getTick(' in value.replace(' ', ''):
                return 'int24'
            return 'uint256'
        if re.match(r'^[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(', value):
            m = re.match(r'^([A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)', value)
            return m.group(1)
        if re.match(r'^\d', value) or 'ether' in value:
            return 'uint256'
        if re.match(r'^[A-Z0-9_]+$', value):
            if 'TICK' in value or 'DEVIATION' in value or 'PRICE' in value:
                return 'int24'
            if 'WINDOW' in value:
                return 'uint32'
            return 'uint256'
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\(', value):
            fn_name = value.split('(')[0].strip()
            # If we know the var_type of fn_name, that's wrong because it's a function.
            # We can search the current file for `function fn_name(...) ... returns (X)`
            # We don't have full code here, only what's in var_types? Wait, var_types only has variables.
            # But we can just add a hardcoded fallback for common names.
            if fn_name == 'oracleContract':
                return 'IV3CompatibleOracle'
            if fn_name == '_V4PoolId':
                return 'PoolId'
        return 'uint256'

    def _call_result_is_used(self, code_context: str, call_start: int) -> bool:
        prefix = code_context[max(0, call_start - 120):call_start]
        prefix = prefix.rstrip()
        if re.search(r'(?:=|return)\s*$', prefix):
            return True
        line_prefix = prefix[prefix.rfind('\n') + 1:]
        return bool(re.search(r'\b(?:uint\d*|int\d*|bool|address|bytes\d*|[A-Z][A-Za-z0-9_\.]*)\s+\w+\s*=\s*$', line_prefix))

    def _infer_return_type_from_assignment(self, code_context: str, fn_name: str, var_types: dict) -> str:
        import re
        # Pattern 1: Type varName = fn(...)
        decl_pattern = r'\b(uint\d*|int\d*|bool|address|bytes\d*|[A-Z][A-Za-z0-9_\.]*)\s+(?:memory\s+)?\w+\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)?' + re.escape(fn_name) + r'\s*\('
        m = re.search(decl_pattern, code_context)
        if m:
            return m.group(1)
        # Pattern 2: varName = fn(...)
        assign_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\.)?' + re.escape(fn_name) + r'\s*\('
        m = re.search(assign_pattern, code_context)
        if m:
            var_name = m.group(1)
            return var_types.get(var_name, "uint256")
        return "uint256"

    def _mock_return_statement(self, returns_sig: str, contract_name: str, kind: str) -> str:
        if not returns_sig:
            return ''
        import re
        m = re.search(r'returns\s*\(([^)]+)\)', returns_sig)
        if not m:
            return 'return 0;'
        if re.search(r'\br0\b', returns_sig):
            return ''
        
        types = m.group(1).split(',')
        vals = []
        for t in types:
            t = t.strip()
            if 'bool' in t: vals.append('true')
            elif 'address' in t: vals.append('address(0)')
            elif 'bytes32' in t: vals.append('bytes32(0)')
            elif 'bytes memory' in t: vals.append('""')
            elif t.startswith('int') or t.startswith('uint'): vals.append('0')
            elif 'LeftRightSigned' in t: vals.append('LeftRightSigned.wrap(0)')
            elif 'LeftRightUnsigned' in t: vals.append('LeftRightUnsigned.wrap(0)')
            elif 'TokenId' in t: vals.append('TokenId.wrap(0)')
            elif 'PoolId' in t: vals.append('PoolId.wrap(bytes32(0))')
            elif 'LiquidityChunk' in t: vals.append('LiquidityChunk.wrap(0)')
            elif 'PositionBalance' in t: vals.append('PositionBalance.wrap(0)')
            else:
                base = t.split()[0]
                if base[0].isupper() and not base.endswith('[]'):
                    vals.append(f'{base}()')
                else:
                    vals.append(f'{base}()')
        
        if len(vals) == 1:
            return f'return {vals[0]};'
        return f'return ({", ".join(vals)});'

    def _external_param_type(self, type_name: str) -> str:
        import re
        if not self._is_usable_solidity_type(type_name):
            return 'uint256'
            
        struct_names = {'PendingWithdrawal', 'DepositEpochState', 'WithdrawalEpochState', 'FindData', 'PoolKey', 'State', 'ChainData', 'RawTx1559Detail', 'Tx1559', 'Tx1559Detail', 'TxDetailLegacy', 'AccessList', 'RawReceipt', 'EIP1559ScriptArtifact', 'RawEIP1559ScriptArtifact', 'RawReceiptLog', 'ReceiptLog', 'TxReturn', 'Account', 'FuzzArtifactSelector', 'PoolIdData', 'PoolInfo', 'ManagerPrices'}
        base_type = type_name.split('[')[0].strip()
        
        if re.match(r'^(?:bytes|string|[A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]*\])+)$', type_name) or base_type in struct_names:
            if not re.search(r'\b(memory|calldata|storage)\b', type_name):
                return f'{type_name} memory'
        return type_name

    def _synthesize_mock_contract(self, contract_name: str, code_context: str, nested_types: set = None) -> str:
        """从上下文生成完整的 mock contract"""
        import re
        if nested_types is None:
            nested_types = set()
        var_types = self._infer_variable_types(code_context)

        # Skip forge-std / test framework contracts
        if contract_name in ("Test", "PoC"):
            return ""
        if contract_name in {"ERC20", "ERC20Minimal", "ERC20SLike"}:
            return f'''contract {contract_name} {{
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function approve(address spender, uint256 amount) public virtual returns (bool) {{
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }}

    function transfer(address to, uint256 amount) public virtual returns (bool) {{
        balanceOf[msg.sender] -= amount;
        unchecked {{ balanceOf[to] += amount; }}
        emit Transfer(msg.sender, to, amount);
        return true;
    }}

    function transferFrom(address from, address to, uint256 amount) public virtual returns (bool) {{
        uint256 allowed = allowance[from][msg.sender];
        if (allowed != type(uint256).max) allowance[from][msg.sender] = allowed - amount;
        balanceOf[from] -= amount;
        unchecked {{ balanceOf[to] += amount; }}
        emit Transfer(from, to, amount);
        return true;
    }}
}}'''
        if contract_name == "Ownable":
            return '''contract Ownable {
    address public owner = msg.sender;
    function transferOwnership(address newOwner) external virtual {
        owner = newOwner;
    }
}'''
        if contract_name == "Multicall":
            return '''contract Multicall {
    function multicall(bytes[] calldata data) external virtual returns (bytes[] memory results) {
        results = new bytes[](data.length);
        for (uint256 i; i < data.length; i++) {
            (bool ok, bytes memory result) = address(this).delegatecall(data[i]);
            require(ok);
            results[i] = result;
        }
    }
}'''
        if contract_name == "Address":
            return '''library Address {
    function sendValue(address payable recipient, uint256 amount) internal {
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value");
    }

    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.call(data);
        require(success, "Address: low-level call failed");
        return returndata;
    }

    function functionCallWithValue(address target, bytes memory data, uint256 value) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        require(success, "Address: low-level call with value failed");
        return returndata;
    }

    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        (bool success, bytes memory returndata) = target.staticcall(data);
        require(success, "Address: low-level static call failed");
        return returndata;
    }
}'''
        if contract_name == "SafeTransferLib":
            return '''library SafeTransferLib {
    function safeTransfer(address token, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = token.call(abi.encodeWithSignature("transfer(address,uint256)", to, amount));
        require(ok && (data.length == 0 || abi.decode(data, (bool))));
    }

    function safeTransferFrom(address token, address from, address to, uint256 amount) internal {
        (bool ok, bytes memory data) = token.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", from, to, amount));
        require(ok && (data.length == 0 || abi.decode(data, (bool))));
    }
}'''
        if contract_name == "Constants":
            return '''library Constants {
    int24 internal constant MIN_V4POOL_TICK = -887272;
    int24 internal constant MAX_V4POOL_TICK = 887272;
    uint32 internal constant FAST_ORACLE_PERIOD = 60;
    uint32 internal constant SLOW_ORACLE_PERIOD = 600;
    uint16 internal constant FAST_ORACLE_CARDINALITY = 20;
    uint16 internal constant SLOW_ORACLE_CARDINALITY = 20;
    bool internal constant SLOW_ORACLE_UNISWAP_MODE = false;
    uint32 internal constant MEDIAN_PERIOD = 600;
}'''
        if contract_name == "Errors":
            return '''library Errors {
    error AccountInsolvent();
    error EffectiveLiquidityAboveThreshold();
    error InputListFail();
    error InvalidTokenIdParameter();
    error NotALongLeg();
    error NotMarginCalled();
    error PoolAlreadyInitialized();
    error PositionAlreadyMinted();
    error StaleOracle();
    error TooManyLegsOpen();
}'''
        if contract_name == "Math_2":
            return '''library Math_2 {
    function abs(int256 value) internal pure returns (uint256) {
        return uint256(value < 0 ? -value : value);
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
}'''
        if contract_name == "CollateralTracker":
            return '''contract CollateralTracker {
    function balanceOf(address) external pure returns (uint256) {
        return 0;
    }
    function convertToAssets(uint256 assets) external pure returns (uint256) {
        return assets;
    }
    function takeCommissionAddData(address, int128, int128, int128, bool) external pure returns (uint32, uint128) {
        return (0, 0);
    }
}'''

        if contract_name == "V4StateReader":
            return '''library V4StateReader {
    function getTick(IPoolManager, PoolId) internal pure returns (int24) {
        return 0;
    }
}'''

        # Extract method calls on this contract type
        methods = {}
        events = set()
        errors = set()
        structs = set(nested_types)

        # Pattern 1: ContractName.method(...)
        for fn_name, args, start_pos, _ in self._find_balanced_calls(code_context, receiver=contract_name):
            if fn_name in methods:
                continue
            arg_types = [self._infer_expression_type(arg, var_types) for arg in args]

            # Infer return type from context
            returns = ' returns (uint256)'
            if fn_name.startswith('get') or fn_name.startswith('is') or fn_name.startswith('has'):
                if 'address' in fn_name or 'addr' in fn_name:
                    returns = ' returns (address)'
                elif 'bool' in fn_name or 'Locked' in fn_name or 'Initialized' in fn_name:
                    returns = ' returns (bool)'
            if 'balanceOf' in fn_name or 'Balance' in fn_name:
                returns = ' returns (uint256)'
            if 'previewRedeem' in fn_name:
                returns = ' returns (uint256)'
            if self._call_result_is_used(code_context, start_pos):
                returns = ' returns (' + self._infer_return_type_from_assignment(code_context, fn_name, var_types) + ')'
            
            # --- NEW TUPLE HEURISTIC ---
            tuple_assign_pattern = r'\(([^)]+)\)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\.\s*)?' + re.escape(fn_name) + r'\s*\('
            tuple_match = re.search(tuple_assign_pattern, code_context)
            if tuple_match:
                tuple_vars = tuple_match.group(1).split(',')
                ret_types = []
                for var in tuple_vars:
                    var = var.strip()
                    if not var:
                        ret_types.append("uint256")
                    else:
                        tokens = var.split()
                        if len(tokens) >= 2:
                            ret_types.append(tokens[0])
                        else:
                            ret_types.append(var_types.get(tokens[0], "uint256"))
                ret_types_with_memory = [self._external_param_type(t) for t in ret_types]
                returns = ' returns (' + ', '.join([f'{t} r{i}' for i, t in enumerate(ret_types_with_memory)]) + ')'
            # ---------------------------

            methods[fn_name] = (arg_types, returns)

        # Pattern 2: variable.method(...) where variable is typed as, or assigned from, this contract.
        var_names = set()
        typed_var_pattern = rf'\b{re.escape(contract_name)}\s+(?:[a-z]+\s+)*(\w+)'
        var_names.update(m.group(1) for m in re.finditer(typed_var_pattern, code_context))
        assigned_var_pattern = rf'\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+{re.escape(contract_name)}\s*\('
        var_names.update(m.group(1) for m in re.finditer(assigned_var_pattern, code_context))
        for var_name in sorted(var_names):
            for fn_name, args, start_pos, _ in self._find_balanced_calls(code_context, receiver=var_name):
                if fn_name in methods:
                    continue
                arg_types = [self._infer_expression_type(arg, var_types) for arg in args]
                returns = ''
                if 'balanceOf' in fn_name:
                    returns = ' returns (uint256)'
                if 'previewRedeem' in fn_name:
                    returns = ' returns (uint256)'
                if self._call_result_is_used(code_context, start_pos):
                    returns = ' returns (' + self._infer_return_type_from_assignment(code_context, fn_name, var_types) + ')'
                
                # --- NEW TUPLE HEURISTIC ---
                tuple_assign_pattern = r'\(([^)]+)\)\s*=\s*(?:[A-Za-z_][A-Za-z0-9_]*\s*\.\s*)?' + re.escape(fn_name) + r'\s*\('
                tuple_match = re.search(tuple_assign_pattern, code_context)
                if tuple_match:
                    tuple_vars = tuple_match.group(1).split(',')
                    ret_types = []
                    for var in tuple_vars:
                        var = var.strip()
                        if not var:
                            ret_types.append("uint256")
                        else:
                            tokens = var.split()
                            if len(tokens) >= 2:
                                ret_types.append(tokens[0])
                            else:
                                ret_types.append(var_types.get(tokens[0], "uint256"))
                    ret_types_with_memory = [self._external_param_type(t) for t in ret_types]
                    returns = ' returns (' + ', '.join([f'{t} r{i}' for i, t in enumerate(ret_types_with_memory)]) + ')'
                # ---------------------------
                
                methods[fn_name] = (arg_types, returns)

        # Do not copy unrelated file-wide errors/events into generated mocks.
        # User-defined errors share the type namespace, so adding them to every
        # placeholder contract causes duplicate declarations.

        # Extract constructor arguments from `new ContractName(...)`
        esc_contract = re.escape(contract_name)
        constructor_calls = self._find_balanced_calls(code_context, contract_name=contract_name)
        constructor_match = constructor_calls[0] if constructor_calls else None
        constructor_args = []
        if constructor_match:
            for i, a in enumerate(constructor_match[1]):
                constructor_args.append(f'{self._infer_expression_type(a, var_types)} arg{i}')

        # If empty, generate a minimal placeholder
        if not methods and not structs and not errors and not events and not constructor_match:
            return f'contract {contract_name} {{}}'

        # Generate the contract or library
        kind = 'library' if 'Lib' in contract_name or 'Math' in contract_name else 'contract'
        result = [f'{kind} {contract_name} {{']

        # Struct definitions
        if structs:
            result.append('    // Nested type definitions')
            for s in sorted(structs):
                nested_struct = self._synthesize_struct(s, code_context)
                for line in nested_struct.split('\n'):
                    result.append('    ' + line)

        # Error definitions
        if errors:
            import re
            result.append('    // Error definitions')
            for e in sorted(errors):
                # find arguments for this error
                arg_types = []
                error_pattern = r'\brevert\s+(?:[A-Za-z_][A-Za-z0-9_]*\.)?' + re.escape(e) + r'\s*\(([^)]*)\)'
                m = re.search(error_pattern, code_context)
                if m and m.group(1).strip():
                    args = [a.strip() for a in m.group(1).split(',')]
                    arg_types = [self._infer_expression_type(a, var_types) for a in args]
                if arg_types:
                    result.append(f'    error {e}({", ".join(arg_types)});')
                else:
                    result.append(f'    error {e}();')

        # Event definitions
        if events:
            result.append('    // Event definitions')
            for e in sorted(events):
                if e == 'Transfer':
                    result.append('    event Transfer(address indexed from, address indexed to, uint256 value);')
                else:
                    result.append(f'    event {e}(bytes data);')

        # Constructor definition
        if constructor_match:
            result.append('    // Constructor')
            args_joined = ", ".join(constructor_args)
            result.append(f'    constructor({args_joined}) {{}}')

        # Storage for mock values (only for contracts)
        if kind == 'contract':
            result.append('    // Mock storage')
            result.append('    mapping(address => uint256) internal ' + contract_name + '_mockValues;')
            result.append('    mapping(address => bool) internal ' + contract_name + '_mockBools;')
            result.append('    mapping(address => address) internal ' + contract_name + '_mockAddresses;')
            result.append('    mapping(address => bytes32) internal ' + contract_name + '_mockBytes32;')
            result.append('    uint256[2][] internal ' + contract_name + '_mockPositionBalances;')
            result.append('    uint256 internal ' + contract_name + '_mockNumLegs;')
            
            # Setter functions
            result.append('')
            result.append('    // Mock setters')
            result.append('    function ' + contract_name + '_setMockValue(address target, uint256 value) external { ' + contract_name + '_mockValues[target] = value; }')
            result.append('    function ' + contract_name + '_setMockBool(address target, bool value) external { ' + contract_name + '_mockBools[target] = value; }')
            result.append('    function ' + contract_name + '_setMockAddress(address target, address value) external { ' + contract_name + '_mockAddresses[target] = value; }')
            result.append('    function ' + contract_name + '_setMockPositionBalanceArray(uint256[2][] memory _array) external {')
            result.append('        delete ' + contract_name + '_mockPositionBalances;')
            result.append('        for (uint i = 0; i < _array.length; i++) {')
            result.append('            ' + contract_name + '_mockPositionBalances.push(_array[i]);')
            result.append('        }')
            result.append('    }')
            result.append('    function ' + contract_name + '_setNumberOfLegs(address, uint256 legs) external { ' + contract_name + '_mockNumLegs = legs; }')

        # Generated methods
        if methods:
            result.append('')
            result.append('    // Context-inferred methods')
            for fn_name, (arg_types, returns_sig) in sorted(methods.items()):
                args_str = ', '.join(f'{self._external_param_type(t)} a{i}' for i, t in enumerate(arg_types))
                mutability = 'view ' if returns_sig and not fn_name.startswith(('set', 'mint', 'approve', 'update')) else ''
                result.append(f'    function {fn_name}({args_str}) external {mutability}{returns_sig} {{')
                return_stmt = self._mock_return_statement(returns_sig, contract_name, kind)
                if return_stmt:
                    result.append('        ' + return_stmt)
                result.append('    }')

        result.append('}')
        return '\n'.join(result)



    def _synthesize_minimal_interface(self, interface_name: str, code_context: str) -> str:
        import re
        methods = []
        pattern = rf'\b{re.escape(interface_name)}\.(\w+)\s*\(([^)]*)\)'
        for fn_name, raw_args in re.findall(pattern, code_context):
            arg_list = [a.strip() for a in raw_args.split(',') if a.strip()]
            arg_types = []
            for arg in arg_list:
                if re.search(r'\b(address|msg\.sender|this)\b', arg):
                    arg_types.append('address')
                elif re.search(r'\b(true|false)\b', arg):
                    arg_types.append('bool')
                elif re.search(r'\bbytes(\d+)?\b', arg):
                    arg_types.append('bytes')
                else:
                    arg_types.append('uint256')
            returns = ''
            if re.search(rf'\b(?:=|return\s+){re.escape(interface_name)}\.{fn_name}\b', code_context):
                returns = ' returns (uint256)'
            methods.append(f'function {fn_name}({", ".join(arg_types)}) external{returns};')
        if not methods:
            if re.match(r'^I[A-Z][A-Za-z0-9_]*$', interface_name):
                return f'interface {interface_name} {{}}'
            return ''
        uniq = []
        seen = set()
        for m in methods:
            if m in seen:
                continue
            seen.add(m)
            uniq.append(m)
        return 'interface ' + interface_name + ' {\n    ' + '\n    '.join(uniq) + '\n}'
    
    def _inject_nested_types_into_contracts(self, contract_code: str, contract_name: str, nested_types: set) -> str:
        """将缺失的嵌套类型定义注入到合约中"""
        import re
        if not nested_types:
            return contract_code

        contract_pattern = rf'(contract\s+{re.escape(contract_name)}\s*\{{)'
        match = re.search(contract_pattern, contract_code)
        if not match:
            return contract_code

        type_definitions = []
        for type_name in sorted(nested_types):
            type_definitions.append(f'    struct {type_name} {{')
            type_definitions.append('        bytes data;  // Placeholder')
            type_definitions.append('    }')
        nested_code = '\n'.join(type_definitions) + '\n'
        insert_pos = match.end()
        return contract_code[:insert_pos] + '\n' + nested_code + contract_code[insert_pos:]
    
    def _detect_naming_conflicts(self, code: str) -> list:
        """检测字段和函数/类型的命名冲突"""
        import re
        conflicts = []
        
        contract_pattern = r'contract\s+(\w+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*?)\}'
        for match in re.finditer(contract_pattern, code, re.DOTALL):
            contract_name = match.group(1)
            contract_body = match.group(2)
            fields = set(re.findall(r'\b(?:public|private|internal)?\s+(?:immutable\s+)?(?:address|uint\d*|int\d*|bool|string|bytes\d*|[A-Z][A-Za-z0-9_]*)\s+(\w+)\s*;', contract_body))
            functions = set(re.findall(r'function\s+(\w+)\s*\(', contract_body))
            types = set(re.findall(r'\b(?:struct|error|event|enum)\s+(\w+)', contract_body))
            conflicting = (fields | types) & functions
            if conflicting:
                conflicts.append((contract_name, conflicting))
        
        return conflicts
    
    def _postprocess_contract(
        self,
        contract_code: str
    ) -> tuple:
        """提取嵌套的interface定义"""
        import re
        extracted_interfaces = []
        
        # 0. 提取嵌套的interface定义（Solidity不允许interface在contract内部）
        lines = contract_code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'^\s*interface\s+\w+', line)
            if match:
                start_line = i
                brace_count = line.count('{') - line.count('}')
                i += 1
                while i < len(lines) and brace_count > 0:
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                end_line = i
                
                interface_lines = lines[start_line:end_line]
                cleaned_interface = '\n'.join(l.lstrip() for l in interface_lines)
                extracted_interfaces.append(cleaned_interface)
                del lines[start_line:end_line]
                i = start_line # Reset i since we deleted lines
            else:
                i += 1
                
        contract_code = '\n'.join(lines)
        
        # 修复常见的重复标识符（例如 _account accountant -> _accountant）
        processed_code = re.sub(r'_(\w+)\s+\1', r'_\1', contract_code)
        return processed_code, extracted_interfaces

    def _qualify_external_error_usage(self, code: str, current_contract: str, nested_error_owners: dict, global_errors: set) -> str:
        """将引用其他合约内部声明 error 的 revert 改为 Contract.Error 形式"""
        import re
        if not nested_error_owners:
            return code
        pattern = r'revert\s+([A-Z]\w+)\s*\('

        def replace(match):
            error_name = match.group(1)
            owners = nested_error_owners.get(error_name)
            if not owners:
                return match.group(0)
            if error_name in global_errors:
                return match.group(0)
            if current_contract in owners:
                return match.group(0)
            if len(owners) != 1:
                return match.group(0)
            owner = next(iter(owners))
            return f'revert {owner}.{error_name}('

        return re.sub(pattern, replace, code)

    def _generate_placeholder_mock(self, name: str) -> str:
        if name.startswith('I'):
            return f"interface {name} {{}}\n"
        return f"contract {name} {{}}\n"
    
    def _extract_nested_types(self, code: str) -> dict:
        """提取合约/library中定义的嵌套类型（struct/error）"""
        import re
        nested = {}
        lines = code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'^\s*(contract|library|interface)\s+(\w+)', line)
            if match:
                container_name = match.group(2)
                container_body = [line]
                i += 1
                brace_count = line.count('{') - line.count('}')
                while i < len(lines) and brace_count > 0:
                    container_body.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1

                body_str = '\n'.join(container_body)
                struct_pattern = r'\bstruct\s+(\w+)\s*\{'
                error_pattern = r'\berror\s+(\w+)\s*\('
                structs = set(re.findall(struct_pattern, body_str))
                errors = set(re.findall(error_pattern, body_str))
                nested[container_name] = {'structs': structs, 'errors': errors}
            else:
                i += 1
        return nested
    
    def _remove_duplicate_definitions(self, code: str, seen_types: set) -> str:
        """移除 code 字符串中已出现过的类型/接口/合约定义"""
        import re
        lines = code.split('\n')
        filtered = []
        skip_depth = 0
        for line in lines:
            stripped = line.strip()
            if skip_depth > 0:
                skip_depth += line.count('{') - line.count('}')
                if skip_depth <= 0:
                    skip_depth = 0
                continue
            type_decl = re.match(r'(contract|library|interface|struct|enum)\s+(\w+)', stripped)
            if type_decl:
                type_name = type_decl.group(2)
                if type_name in seen_types:
                    depth_delta = line.count('{') - line.count('}')
                    skip_depth = depth_delta if depth_delta > 0 else 1
                    continue
                seen_types.add(type_name)
            type_alias = re.match(r'type\s+(\w+)\s+is\s+[^;]+;', stripped)
            if type_alias:
                type_name = type_alias.group(1)
                if type_name in seen_types:
                    continue
                seen_types.add(type_name)
            error_decl = re.match(r'error\s+(\w+)\s*\(', stripped)
            if error_decl:
                error_name = error_decl.group(1)
                if error_name in seen_types:
                    continue
                seen_types.add(error_name)
            filtered.append(line)
        return '\n'.join(filtered)

    def _dedupe_by_ownership(self, code: str) -> str:
        import re
        lines = code.split('\n')
        block_spans = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            m = re.match(r'^(contract|interface|library|struct|enum)\s+(\w+)\b', stripped)
            if not m:
                i += 1
                continue
            start = i
            depth = lines[i].count('{') - lines[i].count('}')
            seen_open = '{' in lines[i]
            i += 1
            while i < len(lines):
                depth += lines[i].count('{') - lines[i].count('}')
                seen_open = seen_open or ('{' in lines[i])
                if seen_open and depth <= 0:
                    i += 1
                    break
                i += 1
            block_spans.append((start, i, m.group(1), m.group(2), '\n'.join(lines[start:i])))

        blocks = [(name, block) for _, _, _, name, block in block_spans]
        if not blocks:
            return code.strip()

        priority = {
            'interface': 5,
            'library': 4,
            'contract': 3,
            'struct': 2,
            'enum': 2,
            'unknown': 1,
        }
        seen: dict[str, tuple[int, int, str]] = {}

        for index, (_, _, kind, name, block) in enumerate(block_spans):
            score = priority.get(kind, 1) * 1000 + len(block)
            existing = seen.get(name)
            if existing is None or score > existing[0] or (score == existing[0] and index < existing[1]):
                seen[name] = (score, index, block)

        keep_indices = {entry[1] for entry in seen.values()}
        remove_lines = set()
        for index, (start, end, _, _, _) in enumerate(block_spans):
            if index not in keep_indices:
                remove_lines.update(range(start, end))

        result = '\n'.join(line for idx, line in enumerate(lines) if idx not in remove_lines)
        return re.sub(r'\n{4,}', '\n\n\n', result).strip()

    def _inject_missing_errors_into_contracts(self, code: str, nested_types_for_injection: dict = None, nested_error_owners: dict = None, global_errors: set = None) -> str:
        import re
        if nested_types_for_injection is None:
            nested_types_for_injection = {}
        if nested_error_owners is None:
            nested_error_owners = {}
        if global_errors is None:
            global_errors = set()

        result = []
        lines = code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            contract_match = re.match(r'^\s*(contract|interface|library)\s+(\w+)', line)
            if contract_match:
                contract_name = contract_match.group(2)
                contract_lines = [line]
                i += 1
                brace_count = line.count('{') - line.count('}')
                while i < len(lines) and brace_count > 0:
                    contract_lines.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1

                contract_code = '\n'.join(contract_lines)
                existing_errors = set(re.findall(r'\berror\s+(\w+)\s*\(', contract_code))
                referenced_errors = set(re.findall(r'revert\s+([A-Z]\w+)\s*\(', contract_code))
                missing_errors = [err for err in sorted(referenced_errors) if err not in existing_errors and err not in global_errors]

                nested_types = nested_types_for_injection.get(contract_name, set())
                existing_structs = set(re.findall(r'\bstruct\s+(\w+)\s*\{', contract_code))
                missing_nested_types = [t for t in sorted(nested_types) if t not in existing_structs]

                public_fields = set(re.findall(r'\bpublic\s+(\w+)\s*;', contract_code))
                filtered_lines = []
                skip_until_brace = False
                for cline in contract_lines[1:]:
                    getter_match = re.match(r'\s*function\s+(\w+)\s*\([^)]*\)\s*(?:external|public)\s+view\s+returns', cline)
                    if getter_match and getter_match.group(1) in public_fields:
                        skip_until_brace = True
                        continue
                    if skip_until_brace:
                        if '}' in cline and '{' not in cline:
                            skip_until_brace = False
                        continue
                    filtered_lines.append(cline)

                contract_lines = [contract_lines[0]] + filtered_lines if filtered_lines else contract_lines

                if missing_nested_types or missing_errors:
                    injections = []
                    if missing_nested_types:
                        injections.append("    // Auto-generated nested type definitions")
                        for type_name in missing_nested_types:
                            nested_struct = self._synthesize_struct(type_name, contract_code)
                            injections.extend("    " + line for line in nested_struct.split('\n'))
                    if missing_errors:
                        injections.append("    // Auto-generated error definitions")
                        injections.extend(f"    error {err}();" for err in missing_errors)
                    contract_lines.insert(1, '\n'.join(injections))

                processed_code = '\n'.join(contract_lines)
                processed_code = self._qualify_external_error_usage(processed_code, contract_name, nested_error_owners, global_errors)
                result.append(processed_code)
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)
    
    def _ensure_nested_types_exist(self, code: str) -> str:
        """Ensure Contract.Type references have placeholder definitions inside the contract."""
        referenced = self._extract_referenced_types(code)
        nested_defs = self._extract_nested_types(code)
        for contract_name, type_names in referenced.get('nested', {}).items():
            existing = nested_defs.get(contract_name, {}).get('structs', set())
            missing = type_names - existing
            if not missing:
                continue
            code = self._inject_structs_into_code(code, contract_name, missing)
            nested_defs = self._extract_nested_types(code)
        return code

    def _inject_structs_into_code(self, code: str, contract_name: str, struct_names: set) -> str:
        import re
        if not struct_names:
            return code
        pattern = rf'(contract\s+{re.escape(contract_name)}\s*\{{)'
        match = re.search(pattern, code)
        if not match:
            return code
        insertion_lines = ['\n    // Auto-generated nested type definitions']
        for type_name in sorted(struct_names):
            inferred_struct = self._synthesize_struct(type_name, code)
            # Indent the struct definition
            for line in inferred_struct.split('\n'):
                insertion_lines.append('    ' + line)
        insertion_lines.append('')
        insertion = '\n'.join(insertion_lines)
        insert_pos = match.end()
        return code[:insert_pos] + '\n' + insertion + code[insert_pos:]

    def _remove_duplicate_interfaces(self, code: str) -> tuple[str, set]:
        """Keep the richest interface definition per name and drop placeholders."""
        import re
        lines = code.split('\n')
        keep: dict[str, dict] = {}
        interfaces = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'^\s*interface\s+(\w+)', line)
            if match:
                start_line = i
                name = match.group(1)
                brace_count = line.count('{') - line.count('}')
                i += 1
                while i < len(lines) and brace_count > 0:
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                end_line = i
                
                body_lines = lines[start_line:end_line]
                body_str = '\n'.join(body_lines)
                body_clean = body_str[body_str.find('{') + 1 : body_str.rfind('}')].strip()
                placeholder = len(body_clean) == 0
                score = (0 if placeholder else 1, len(body_clean))
                
                interfaces.append({
                    'name': name,
                    'start_line': start_line,
                    'end_line': end_line,
                    'score': score,
                    'order': len(interfaces)
                })
            else:
                i += 1
                
        for entry in interfaces:
            name = entry['name']
            existing = keep.get(name)
            if existing is None:
                keep[name] = entry
            elif entry['score'] > existing['score'] or (entry['score'] == existing['score'] and entry['order'] > existing['order']):
                keep[name] = entry
                
        remove_intervals = []
        for entry in interfaces:
            if keep.get(entry['name']) != entry:
                remove_intervals.append((entry['start_line'], entry['end_line']))
                
        for start, end in sorted(remove_intervals, reverse=True):
            del lines[start:end]
            
        return '\n'.join(lines), set(keep.keys())

    def _remove_empty_contracts_for_interfaces(self, code: str, interface_names: set) -> str:
        """Drop empty contract stubs when a matching interface exists."""
        import re
        if not interface_names:
            return code
        spans_to_remove: list[tuple[int, int]] = []
        for name in interface_names:
            pattern = re.compile(r'(contract\s+' + re.escape(name) + r'\s*\{(.*?)\})', re.DOTALL)
            for match in pattern.finditer(code):
                body = match.group(2)
                stripped = re.sub(r'/\*[\s\S]*?\*/', '', body)
                stripped = re.sub(r'//.*', '', stripped)
                if stripped.strip():
                    continue
                spans_to_remove.append(match.span(1))
        for start, end in sorted(spans_to_remove, reverse=True):
            code = code[:start] + code[end:]
        return code

    def assemble(self, manifest: SymbolManifest, inference: InferenceResult) -> str:
        lines = []
        
        # 1. Header
        lines.append("// SPDX-License-Identifier: MIT")
        lines.append("pragma solidity ^0.8.0;")
        lines.append("import 'forge-std/Test.sol';")
        lines.append("")
        
        # 收集所有已定义的类型和函数
        all_code = '\n'.join(manifest.global_types)
        for contract in manifest.contracts.values():
            all_code += '\n' + contract.code
        for lib_code in inference.mock_libraries.values():
            all_code += '\n' + lib_code
        
        # 提取嵌套类型（合约内部定义的 struct/error）
        nested_types_map = self._extract_nested_types(all_code)
        nested_error_owners = {}
        for container, types in nested_types_map.items():
            for error_name in types.get('errors', set()):
                nested_error_owners.setdefault(error_name, set()).add(container)
        import re
        combined_global_types = '\n'.join(manifest.global_types)
        global_error_names = set(re.findall(r'\berror\s+(\w+)\s*\(', combined_global_types))
        
        # 2. Global Types (去重)
        seen_types = set()
        
        for g_type in manifest.global_types:
            clean_type = self._strip_headers(g_type)
            deduped = self._remove_duplicate_definitions(clean_type, seen_types).strip()
            if deduped:
                lines.append(deduped)
                lines.append("")
        
        # 2.5 预先计算嵌套类型注入需求（在处理mock之前）
        # 收集所有代码用于类型分析
        all_code_for_analysis = '\n'.join(manifest.global_types)
        for contract in manifest.contracts.values():
            all_code_for_analysis += '\n' + contract.code
        for lib_code in inference.mock_libraries.values():
            all_code_for_analysis += '\n' + lib_code
        for orphan in manifest.orphans:
            all_code_for_analysis += '\n' + orphan.code
        
        # 提取所有被引用和已定义的类型
        referenced = self._extract_referenced_types(all_code_for_analysis)
        referenced['contracts'].update(
            type_name for _, type_name in self._extract_undeclared_variables(all_code_for_analysis)
        )
        defined = self._extract_defined_types(all_code_for_analysis)
        symbol_index = self._build_symbol_index(manifest)
        
        # 计算缺失的类型
        all_defined_type_names = (defined['structs'] | defined['contracts'] | 
                                   defined['interfaces'] | defined['types'] | defined['enums'])
        all_defined_type_names |= symbol_index.contracts | symbol_index.interfaces | symbol_index.structs | symbol_index.errors | symbol_index.enums | symbol_index.types
        
        # 处理嵌套类型：区分需要创建的合约和需要注入的现有合约
        nested_contracts_to_create = {}
        nested_types_to_inject = {}
        for contract_name, type_names in referenced.get('nested', {}).items():
            existing_nested = nested_types_map.get(contract_name, {}).get('structs', set())
            missing_nested = type_names - existing_nested
            if contract_name not in all_defined_type_names:
                nested_contracts_to_create[contract_name] = type_names
            elif missing_nested:
                # 合约存在但缺少部分嵌套类型，注入缺失的部分
                nested_types_to_inject[contract_name] = missing_nested
            
        missing_global_errors = referenced['errors'] - defined['errors']
        global_errors_available = defined['errors'] | missing_global_errors
        
        # 3. Generated Libraries & Mocks (去除其中的类型定义，避免重复，并注入缺失的错误定义和嵌套类型)
        extracted_global_interfaces = []  # 收集从contract中提取的interface
        for lib_name, lib_code in inference.mock_libraries.items():
            lines.append(f"// Mock Implementation for {lib_name}")
            
            # 提取 mock 库中的 interface 并移动到全局作用域
            lib_interfaces = re.findall(r'\binterface\s+\w+\s*\{[^}]*\}', lib_code)
            extracted_global_interfaces.extend(lib_interfaces)
            clean_lib = re.sub(r'\binterface\s+\w+\s*\{[^}]*\}', '', lib_code)
            
            clean_lib = self._strip_headers(clean_lib)
            clean_lib = self._remove_duplicate_definitions(clean_lib, seen_types)
            
            # 提取 interface 并在最后统一下一步处理
            clean_lib, extracted_interfaces = self._postprocess_contract(clean_lib)
            extracted_global_interfaces.extend(extracted_interfaces)

            if not clean_lib.strip():
                clean_lib = self._generate_placeholder_mock(lib_name)
            
            # 清理：如果代码以缩进的 orphan 声明（function/error/event 无包裹容器）开头，扔掉
            if clean_lib.strip():
                first_real_line = None
                for ln in clean_lib.split('\n'):
                    s = ln.strip()
                    if s and not s.startswith('//') and not s.startswith('/*') and not s.startswith('*'):
                        first_real_line = ln
                        break
                if first_real_line and first_real_line[0] in (' ', '\t') and any(first_real_line.strip().startswith(kw) for kw in ['function ', 'error ', 'event ', 'modifier ', 'using ']):
                    print(f"      [ASSEMBLER] Discarding orphaned fragment for '{lib_name}'")
                    clean_lib = self._generate_placeholder_mock(lib_name)
                # 如果 {} 不成比例（} 比 { 多），也扔掉
                if clean_lib.count('}') > clean_lib.count('{') and clean_lib.strip():
                    print(f"      [ASSEMBLER] Discarding malformed content for '{lib_name}' (unbalanced braces)")
                    clean_lib = self._generate_placeholder_mock(lib_name)
            
            # 检查 library 的括号是否匹配
            open_braces = clean_lib.count('{')
            close_braces = clean_lib.count('}')
            if open_braces > close_braces:
                # 缺少闭合括号，添加它们
                missing = open_braces - close_braces
                clean_lib += '\n' + ('}\n' * missing)
            
            lines.append(clean_lib)
            lines.append("")
        
        # 3.4 添加从contracts中提取的interfaces（在全局作用域）
        if extracted_global_interfaces:
            lines.append('// Interfaces extracted from contracts (moved to global scope)')
            for interface_def in extracted_global_interfaces:
                lines.append(interface_def)
                lines.append('')
            
        # 3.5 后处理：生成全局缺失类型定义（不包括需要注入到合约内部的嵌套类型）
        filtered_structs = self._filter_candidate_types(all_code_for_analysis, referenced['structs'] - all_defined_type_names, symbol_index)
        filtered_interfaces = self._filter_candidate_types(all_code_for_analysis, referenced['interfaces'] - all_defined_type_names, symbol_index)
        filtered_contracts = self._filter_candidate_types(all_code_for_analysis, referenced['contracts'], symbol_index)
        filtered_contracts = {name for name in filtered_contracts if name not in all_defined_type_names}
        missing_types = {
            'structs': filtered_structs,
            'errors': missing_global_errors,
            'interfaces': filtered_interfaces,
            'nested_contracts': nested_contracts_to_create,
            'contracts': filtered_contracts,
        }
        currency_alias = self._resolve_currency_type(all_code_for_analysis)
        if currency_alias:
            lines.append('// Domain type resolver')
            lines.append(currency_alias)
            lines.append('')
        
        # 生成缺失类型的定义并添加到全局区域
        if any(missing_types.values()):
            lines.append('// Auto-generated missing type definitions')
            lines.append(self._generate_missing_type_definitions(missing_types, all_code_for_analysis))
            lines.append('')
        
        # 4. Contracts (Reconstructed)
        for name, contract in manifest.contracts.items():
            # 提取原始合约代码并清理 headers
            original_code = self._strip_headers(contract.code.strip())
            original_code = self._rewrite_variable_declarations(original_code, symbol_index)
            original_code = self._remove_unindented_function_blocks(original_code)
            
            # 检测并修复命名冲突（字段与函数同名）
            conflicts = self._detect_naming_conflicts(original_code)
            for contract_name, conflicting_names in conflicts:
                if contract_name == name:
                    for conflict_name in conflicting_names:
                        # 重命名 immutable 字段为 _fieldName
                        original_code = re.sub(
                            rf'\b((?:public|private|internal)?\s+immutable\s+\w+)\s+{conflict_name}\s*;',
                            rf'\1 _{conflict_name};',
                            original_code
                        )
                        # 更新字段引用
                        original_code = re.sub(
                            rf'\breturn\s+{conflict_name}\s*;',
                            rf'return _{conflict_name};',
                            original_code
                        )
            
            # 检测未声明的状态变量（从 setUp 等函数中提取）
            undeclared_vars = self._extract_undeclared_variables(original_code)
            
            # 收集已声明的变量名
            import re
            # 匹配各种变量声明模式
            existing_vars = set()
            # 简单类型: uint256 x;
            existing_vars.update(re.findall(r'\b(?:address|uint\d*|int\d*|bool|string|bytes\d*)\s+(\w+)\s*[;=]', original_code))
            # 自定义类型: MyType x; 或 MyType[] memory x; 或 Contract.Type x;
            existing_vars.update(
                var_name
                for _, var_name in re.findall(
                    r'\b([A-Z][A-Za-z0-9_\.]*(?:\[\d*\])*)\s+(?:(?:memory|storage|calldata)\s+)?(\w+)\s*[;=]',
                    original_code,
                )
            )
            # mapping: mapping(...) => ...) name;
            existing_vars.update(re.findall(r'mapping\s*\([^)]+\)\s+(?:public|private|internal)?\s*(\w+)\s*;', original_code))
            
            # 收集将要归位到此合约的孤儿函数
            orphan_codes = []
            for orphan in manifest.orphans:
                target_contract = inference.rehoming_map.get(orphan.name)
                if target_contract == name:
                    orphan_codes.append(orphan.code)
            
            combined_orphan_code = '\n'.join(orphan_codes)
            
            # 检测合约本身代码和孤儿函数中使用的未声明状态变量
            contract_used_vars = self._extract_used_state_variables(original_code + "\n" + combined_orphan_code, existing_vars)
            
            # 合并所有未声明的变量
            all_undeclared = undeclared_vars + contract_used_vars

            # 去重（保持首次出现顺序）
            unique_vars = []
            seen_var_names = set()
            for var_name, var_type in all_undeclared:
                if var_name in seen_var_names:
                    continue
                seen_var_names.add(var_name)
                unique_vars.append((var_name, var_type))
            all_undeclared = unique_vars

            # 检测缺失的 error 定义（仅在合约内未定义时）
            contract_scope_code = original_code + '\n' + combined_orphan_code
            existing_errors = set(re.findall(r'\berror\s+(\w+)\s*\(', original_code))
            referenced_errors = set(re.findall(r'revert\s+([A-Z]\w+)\s*\(', contract_scope_code))
            # 过滤掉已在嵌套类型中定义的错误
            nested_errors = nested_types_map.get(name, {}).get('errors', set())
            # 过滤掉已在全局或其他合约中定义的错误
            global_errors = set(re.findall(r'\berror\s+(\w+)\s*\(', all_code))
            missing_errors = [err for err in sorted(referenced_errors) 
                            if err not in existing_errors and err not in nested_errors and err not in global_errors]
            
            # 检查花括号是否匹配
            open_braces = original_code.count('{')
            close_braces = original_code.count('}')
            
            # 如果需要在合约声明后插入状态变量
            if all_undeclared or missing_errors:
                # 找到合约声明行的位置并插入状态变量
                contract_lines = original_code.split('\n')
                new_lines = []
                inserted_blocks = False
                
                for line in contract_lines:
                    new_lines.append(line)
                    # 在合约声明后插入自动生成的声明
                    if re.search(rf'\bcontract\s+{name}\b', line) and not inserted_blocks:
                        # 注入嵌套类型定义（如果此合约需要）
                        if name in nested_types_to_inject:
                            new_lines.append("    // Auto-generated nested type definitions")
                            for type_name in sorted(nested_types_to_inject[name]):
                                safe_type = self._sanitize_identifier(type_name, symbol_index)
                                # 检查类型是否已经在合约中定义
                                if not re.search(rf'\bstruct\s+{re.escape(type_name)}\s*\{{', original_code):
                                    new_lines.append(f"    struct {safe_type} {{")
                                    new_lines.append("        bytes data;  // Placeholder")
                                    new_lines.append("    }")
                            new_lines.append("")
                        if all_undeclared:
                            new_lines.append("    // Auto-detected state variables")
                            taken_names = set(existing_vars)
                            for var_name, var_type in all_undeclared:
                                if var_name in taken_names:
                                    continue
                                if var_name == name or self._state_var_name_conflicts_with_type(var_name, symbol_index):
                                    continue
                                taken_names.add(var_name)
                                new_lines.append(f"    {var_type} {var_name};")
                            new_lines.append("")
                        if missing_errors:
                            new_lines.append("    // Auto-detected error definitions")
                            for err in missing_errors:
                                new_lines.append(f"    error {err}();")
                            new_lines.append("")
                        inserted_blocks = True
                
                original_code = '\n'.join(new_lines)
            
            # 如果括号匹配，移除最后一个 '}' 以便添加孤儿函数
            if open_braces == close_braces and original_code.endswith("}"):
                original_code = original_code[:-1]
                need_closing_brace = True
            else:
                # 如果括号不匹配（原始文件不完整），直接使用原代码
                # 并确保后续会添加足够的闭合括号
                need_closing_brace = True
            
            lines.append(original_code)
            
            # 添加常见的修饰符（如果代码中使用了但未定义）
            if 'onlyOwner' in original_code or any('onlyOwner' in orphan.code for orphan in manifest.orphans if inference.rehoming_map.get(orphan.name) == name):
                lines.append("    modifier onlyOwner() { _; }  // Placeholder modifier")
            
            lines.append("    // --- Re-homed Functions ---")
            
            # 提取合约中已存在的函数签名
            existing_functions = self._extract_function_signatures(original_code)
            
            # 查找归属于此合约的孤儿函数（跳过已存在的）
            for orphan in manifest.orphans:
                target_contract = inference.rehoming_map.get(orphan.name)
                if target_contract == name:
                    # 检查函数是否已存在
                    orphan_funcs = self._extract_function_signatures(orphan.code)
                    if orphan_funcs and orphan_funcs.issubset(existing_functions):
                        continue  # 跳过已存在的函数
                    
                    # 修复函数可见性
                    fixed_code = self._fix_function_visibility(orphan.code)
                    
                    # 为孤儿函数添加缩进（4个空格）
                    indented_code = "\n".join(
                        "    " + line if line.strip() else line
                        for line in fixed_code.split("\n")
                    )
                    lines.append(indented_code)
            
            # 闭合合约（确保有闭合括号）
            if need_closing_brace:
                lines.append("}")
            lines.append("")
            
        # 后处理：修复保留关键字用作标识符的问题
        result = "\n".join(lines)
        
        # 修复 struct 字段名中的保留关键字
        import re
        result = re.sub(r'(\s+)string function;', r'\1string functionName;', result)
        result = re.sub(r'(\s+)address function;', r'\1address functionAddr;', result)
        result = normalize_primitive_type_aliases(result)
        
        result = self._ensure_nested_types_exist(result)
        result, kept_interfaces = self._remove_duplicate_interfaces(result)
        result = self._remove_empty_contracts_for_interfaces(result, kept_interfaces)
        result = self._dedupe_by_ownership(result)
        result = self._remove_cross_kind_conflicts(result)
        result = self._remove_duplicate_definitions(result, set())
        
        # 统一下一步：错误注入、嵌套类型注入、外部错误限定、getter清理
        result = self._inject_missing_errors_into_contracts(
            result, 
            nested_types_to_inject, 
            nested_error_owners, 
            global_errors_available
        )
        
        # Generic cleanup for hallucinated or unresolved references.
        # Prefer compiler feedback and LLM repair over project-specific special cases.
        unresolved_contract_refs = set(re.findall(r'\bnew\s+([A-Z]\w+)', result))
        unresolved_contract_refs.update(re.findall(r'\b([A-Z]\w+)\.[A-Z]\w+', result))
        unresolved_contract_refs.difference_update({'Test', 'console', 'console2', 'vm'})

        for ref_name in sorted(unresolved_contract_refs):
            result = re.sub(rf'(?ms)^\s*struct\s+{re.escape(ref_name)}\s*\{{.*?\n\s*\}}\s*\n?', '', result)
            result = re.sub(rf'(?ms)^\s*interface\s+{re.escape(ref_name)}\s*\{{.*?\n\s*\}}\s*\n?', '', result)
            if f"contract {ref_name}Mock" in result and f"contract {ref_name}" not in result:
                result = re.sub(rf'\bcontract\s+{re.escape(ref_name)}Mock\b', f'contract {ref_name}', result)

        result = self._rewrite_variable_declarations(result, symbol_index)
        result = self._ensure_nested_types_exist(result)
        result = normalize_primitive_type_aliases(result)

        # Move all interfaces to the top to resolve base/derived contract ordering issues
        interfaces = []
        interface_names = set()
        
        while True:
            match = re.search(r'\binterface\s+(\w+)\s*\{', result)
            if not match:
                break
            
            start_idx = match.start()
            name = match.group(1)
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = -1
            missing_brace = False
            for i in range(match.end() - 1, len(result)):
                if result[i] == '{':
                    brace_count += 1
                elif result[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
                
                # Check for top-level interface/contract declaration indicating a missing closing brace
                if brace_count == 1 and result[i] == '\n':
                    if result[i+1:].lstrip().startswith('interface ') or result[i+1:].lstrip().startswith('contract '):
                        end_idx = i
                        missing_brace = True
                        break
            
            if end_idx != -1:
                extracted = result[start_idx:end_idx]
                if missing_brace:
                    extracted += "\n}\n"
                if name not in interface_names:
                    interfaces.append(extracted)
                    interface_names.add(name)
                # Replace with empty string
                result = result[:start_idx] + result[end_idx:]
            else:
                # Malformed interface, just break to avoid infinite loop
                break
                
        if interfaces:
            # Remove any contract with the same name if we already extracted its interface
            for name in interface_names:
                # We need to find the contract properly with brace matching as well
                while True:
                    c_match = re.search(rf'\bcontract\s+{name}\b[^{{]*\{{', result)
                    if not c_match:
                        break
                    
                    c_start = c_match.start()
                    c_brace_count = 0
                    c_end = -1
                    c_missing_brace = False
                    for i in range(c_match.end() - 1, len(result)):
                        if result[i] == '{':
                            c_brace_count += 1
                        elif result[i] == '}':
                            c_brace_count -= 1
                            if c_brace_count == 0:
                                c_end = i + 1
                                break
                        
                        if c_brace_count == 1 and result[i] == '\n':
                            if result[i+1:].lstrip().startswith('interface ') or result[i+1:].lstrip().startswith('contract '):
                                c_end = i
                                c_missing_brace = True
                                break
                    if c_end != -1:
                        result = result[:c_start] + result[c_end:]
                    else:
                        break
                
            result = "\n\n".join(interfaces) + "\n\n" + result
            
        # Fix hallucinated revert
        result = result.replace('revert(add(32, errorMessage), mload(errorMessage));', 'revert(errorMessage);')

        # Fix missing errors globally
        referenced_errors = set(re.findall(r'\brevert\s+([A-Z]\w+)\s*\(', result))
        global_errors = set(re.findall(r'(?m)^error\s+(\w+)\s*\(', result))
        missing = referenced_errors - global_errors
        
        events_to_inject = []
        if "emit Transfer(" in result and "event Transfer(" not in result:
            events_to_inject.append("event Transfer(address indexed from, address indexed to, uint256 value);")
        if "emit Approval(" in result and "event Approval(" not in result:
            events_to_inject.append("event Approval(address indexed owner, address indexed spender, uint256 value);")

        if missing or events_to_inject:
            error_defs = "\n".join([f"error {err}();" for err in sorted(missing)]) if missing else ""
            event_defs = "\n".join(events_to_inject) if events_to_inject else ""
            injections = (error_defs + "\n" + event_defs).strip()
            
            # insert after pragma or at start
            pragma_idx = result.find("pragma solidity")
            if pragma_idx != -1:
                end_idx = result.find("\n", pragma_idx) + 1
                result = result[:end_idx] + "\n" + injections + "\n" + result[end_idx:]
            else:
                result = injections + "\n\n" + result

        return result
