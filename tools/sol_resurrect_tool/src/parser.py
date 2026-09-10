from tree_sitter import Language, Parser
import tree_sitter_solidity
from .types import SymbolManifest, ContractShell, OrphanFunction, CodeBlock
import re

class SolidityParser:
    def __init__(self):
        # 适配新版 tree-sitter API (>=0.21.0)
        self.language = Language(tree_sitter_solidity.language())
        try:
            # 新版 API: Parser 接受 language 参数
            self.parser = Parser(self.language)
        except TypeError:
            # 旧版 API 兼容: 使用 set_language 方法
            self.parser = Parser()
            self.parser.set_language(self.language)

    def parse(self, code_bytes: bytes) -> SymbolManifest:
        tree = self.parser.parse(code_bytes)
        manifest = SymbolManifest()
        cursor = tree.walk()
        
        # 遍历 AST
        self._visit(cursor.node, code_bytes, manifest)
        self._build_symbol_index(code_bytes, manifest)
        return manifest

    def _extract_text(self, node, code_bytes) -> str:
        return code_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def _build_symbol_index(self, code_bytes, manifest: SymbolManifest):
        code = code_bytes.decode('utf-8', errors='ignore')
        symbols = manifest.symbols
        symbols.contracts.update(re.findall(r'\bcontract\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.interfaces.update(re.findall(r'\binterface\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.libraries.update(re.findall(r'\blibrary\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.structs.update(re.findall(r'\bstruct\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.errors.update(re.findall(r'\berror\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.enums.update(re.findall(r'\benum\s+([A-Z][A-Za-z0-9_]*)', code))
        symbols.types.update(re.findall(r'\btype\s+([A-Z][A-Za-z0-9_]*)\s+is\b', code))
        symbols.functions.update(re.findall(r'\bfunction\s+([a-z_][A-Za-z0-9_]*)\s*\(', code))
        symbols.state_variables.update(re.findall(r'\b(?:address|uint\d*|int\d*|bool|string|bytes\d*|[A-Z][A-Za-z0-9_]*)\s+([a-z_][A-Za-z0-9_]*)\s*(?:[;=,\)])', code))
        symbols.references.setdefault('nested', set())

        all_groups = [symbols.contracts, symbols.interfaces, symbols.libraries, symbols.structs, symbols.errors, symbols.enums, symbols.types, symbols.functions, symbols.state_variables]
        all_identifiers = set().union(*all_groups)
        symbols.all_identifiers.update(all_identifiers)

        for group_name, values in [
            ('contracts', symbols.contracts),
            ('interfaces', symbols.interfaces),
            ('libraries', symbols.libraries),
            ('structs', symbols.structs),
            ('errors', symbols.errors),
            ('enums', symbols.enums),
            ('types', symbols.types),
        ]:
            for name in values:
                symbols.conflicts.setdefault(name, set()).add(group_name)

        nested_pattern = re.compile(r'\b([A-Z][A-Za-z0-9_]*)\.([A-Z][A-Za-z0-9_]*)\b')
        for owner, nested in nested_pattern.findall(code):
            symbols.nested_types.setdefault(owner, set()).add(nested)

        abi_nested_pattern = re.compile(r'abi\.decode\([^,]+,\s*\(([^)]*)\)')
        for chunk in abi_nested_pattern.findall(code):
            for owner, nested in nested_pattern.findall(chunk):
                symbols.nested_types.setdefault(owner, set()).add(nested)

    def _visit(self, node, code_bytes, manifest: SymbolManifest):
        node_type = node.type
        
        # 1. 提取 Pragma 和 Imports
        if node_type == "pragma_directive":
            manifest.pragmas.append(self._extract_text(node, code_bytes))
        elif node_type == "import_directive":
            manifest.imports.append(self._extract_text(node, code_bytes))
            
        # 2. 提取全局类型 (Struct, Enum, Type)
        elif node_type in ["struct_declaration", "enum_declaration", "user_defined_type_definition"]:
            # 只有当它是顶层定义时才提取 (parent 是 source_file)
            if node.parent.type == "source_file":
                manifest.global_types.append(self._extract_text(node, code_bytes))

        # 3. 提取合约外壳
        elif node_type == "contract_declaration" or node_type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = self._extract_text(name_node, code_bytes)
                body_node = node.child_by_field_name("body")
                contract = ContractShell(
                    name=name, 
                    code=self._extract_text(node, code_bytes), # 暂存原始代码
                    start_byte=node.start_byte,
                    end_byte=node.end_byte
                )
                # 简单提取状态变量名 (用于辅助 LLM 归位)
                if body_node:
                    for child in body_node.children:
                        if child.type == "state_variable_declaration":
                            # 这是一个简化的提取，实际可能需要更细致的解析
                            contract.state_variables.append(self._extract_text(child, code_bytes))
                manifest.contracts[name] = contract

        # 4. 提取 Library (可能是空的/折叠的)
        elif node_type == "library_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = self._extract_text(name_node, code_bytes)
                manifest.libraries.append(CodeBlock(
                    name=name,
                    code=self._extract_text(node, code_bytes),
                    start_byte=node.start_byte,
                    end_byte=node.end_byte
                ))

        # 5. 提取悬空函数 (Orphans) -> 最关键的一步
        elif node_type == "function_definition":
            # 只有当它的父节点是 source_file 时，才是悬空函数
            if node.parent.type == "source_file":
                name_node = node.child_by_field_name("name")
                func_name = "unknown"
                if name_node:
                    func_name = self._extract_text(name_node, code_bytes)
                
                orphan = OrphanFunction(
                    name=func_name,
                    code=self._extract_text(node, code_bytes),
                    start_byte=node.start_byte,
                    end_byte=node.end_byte
                )
                
                # 提取更结构化的使用上下文，供最小接口推导使用
                self._extract_identifiers(node, code_bytes, orphan.used_identifiers)
                self._extract_call_expressions(node, code_bytes, orphan.call_expressions)
                self._extract_member_accesses(node, code_bytes, orphan.member_accesses)
                self._extract_return_contexts(node, code_bytes, orphan.return_contexts)
                manifest.orphans.append(orphan)

        # 递归遍历子节点 (除了 Contract 内部，我们不深入 Contract 内部遍历以节省资源，除非为了 specific tasks)
        if node_type not in ["contract_declaration", "library_definition", "interface_declaration", "function_definition"]:
            for child in node.children:
                self._visit(child, code_bytes, manifest)

    def _extract_identifiers(self, node, code_bytes, result_list):
        """递归提取函数体内的所有 identifier"""
        if node.type == "identifier":
            result_list.append(self._extract_text(node, code_bytes))
        for child in node.children:
            self._extract_identifiers(child, code_bytes, result_list)

    def _extract_call_expressions(self, node, code_bytes, result_list):
        if node.type == "call_expression":
            result_list.append(self._extract_text(node, code_bytes))
        for child in node.children:
            self._extract_call_expressions(child, code_bytes, result_list)

    def _extract_member_accesses(self, node, code_bytes, result_list):
        if node.type == "member_access" or node.type == "field_access":
            result_list.append(self._extract_text(node, code_bytes))
        for child in node.children:
            self._extract_member_accesses(child, code_bytes, result_list)

    def _extract_return_contexts(self, node, code_bytes, result_list):
        if node.type == "return_statement":
            result_list.append(self._extract_text(node, code_bytes))
        for child in node.children:
            self._extract_return_contexts(child, code_bytes, result_list)
