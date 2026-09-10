import re


class ErrorRouter:
    @staticmethod
    def _source_snippets(compiler_output: str) -> list[str]:
        snippets = []
        for line in (compiler_output or "").splitlines():
            numbered = re.match(r"\s*\d+\s*\|\s*(.+)$", line)
            piped = re.match(r"\s*\|\s*(.+)$", line)
            if numbered:
                snippets.append(numbered.group(1))
            elif piped and "^" not in piped.group(1):
                snippets.append(piped.group(1))
        return snippets

    @staticmethod
    def _has_type_like_missing_symbol(compiler_output: str) -> bool:
        keywords = {
            "Error", "Identifier", "Did", "Warning", "Compiler", "Undeclared",
            "return", "if", "require", "revert", "emit", "new", "delete",
            "address", "bool", "bytes", "string", "uint", "int",
        }
        for snippet in ErrorRouter._source_snippets(compiler_output):
            for token in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", snippet):
                if token in keywords:
                    continue
                if token.startswith("I") and len(token) > 1 and token[1].isupper():
                    return True
                if token[0].isupper():
                    return True
        return False

    @staticmethod
    def classify(compiler_output: str) -> str:
        text = compiler_output or ""
        lower = text.lower()

        # Structure-level failures first.
        if re.search(r"declaration expected|function, variable, struct or modifier declaration expected|source file requires pragma", lower):
            return "structure"

        # Body / syntax-level failures next.
        if re.search(
            r"expected identifier but got|expected expression|expected type name|invalid token|expected ';'|expected ','|unexpected ';'|bare identifier|stray token|expected primary expression|parsererror|syntaxerror|unexpected token",
            lower,
        ):
            return "body_syntax"
        if re.search(r"expected identifier|expected primary expression|function body|empty function body", lower):
            return "body_syntax"

        if re.search(r"identifier already declared|identifier already exists|duplicate", lower):
            return "duplicate-declaration"
        if re.search(r"identifier not found or not unique|identifier not found", lower):
            if re.search(r"\btype\b|struct|error|interface|contract", lower) or ErrorRouter._has_type_like_missing_symbol(text):
                return "undefined-type"
            return "signature-mismatch"
        if re.search(r"undeclared identifier", lower):
            if ErrorRouter._has_type_like_missing_symbol(text):
                return "undefined-type"
            return "signature-mismatch"
        if re.search(r"member .* not found|wrong argument count|invalid implicit conversion|not implicitly convertible", lower):
            return "signature-mismatch"
        if re.search(r"typeerror", lower):
            return "undefined-type"
        return "semantic"

    @staticmethod
    def should_use_llm(error_class: str, deterministic_fix_failed: bool, ast_can_resolve: bool) -> bool:
        if error_class in {"structure", "body_syntax"}:
            return False
        if error_class == "duplicate-declaration":
            return False
        if error_class in {"undefined-type", "signature-mismatch"} and ast_can_resolve:
            return False
        if error_class == "signature-mismatch" and not deterministic_fix_failed:
            return False
        return error_class == "semantic" or deterministic_fix_failed
