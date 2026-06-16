use solar_ast::{
    self as ast, Expr, ExprKind, Item, ItemKind, SourceUnit, Stmt, StmtKind, Type, TypeKind,
};
use solar_interface::{ColorChoice, Session};
use solar_parse::Parser;
use std::collections::HashSet;
use std::sync::Once;

use super::normalizer;

static INIT_PANIC_HOOK: Once = Once::new();

#[derive(Debug, Default)]
pub struct ExtractionResult {
    pub missing_interfaces: Vec<String>,
    pub missing_mocks: Vec<String>,
    pub missing_errors: Vec<String>,
}

pub fn parse_and_extract(code: &str) -> Result<ExtractionResult, String> {
    // Prevent panic output spam for ast worker threads in a thread-safe way
    INIT_PANIC_HOOK.call_once(|| {
        let default_hook = std::panic::take_hook();
        std::panic::set_hook(Box::new(move |info| {
            let thread = std::thread::current();
            let name = thread.name().unwrap_or("");
            if !name.starts_with("solar_ast_worker") {
                default_hook(info);
            }
        }));
    });

    let normalized = normalizer::normalize_source(code);
    let sanitized = normalized.code;
    if normalized.report.has_changes() {
        println!(
            "      [Brain] Normalized Solidity before AST: {} cleanup actions.",
            normalized.report.actions.len()
        );
    }
    let parse_result = parse_with_solar(&sanitized);

    match parse_result {
        Ok(result) => Ok(result),
        Err(e) => {
            if let Some(partial) = parse_top_level_chunks_with_solar(&sanitized) {
                println!(
                    "      [Brain] Solar full-file AST extraction failed: {}. Recovered with chunked AST extraction.",
                    e
                );
                return Ok(partial);
            }

            let context = normalizer::first_suspicious_line(&sanitized)
                .map(|(line, text)| format!(" First suspicious line {}: {}", line, text.trim()));
            if e == "Thread panicked" {
                println!(
                    "      [Brain] Solar AST extraction panicked after sanitization and chunked AST recovery. Using lexical fallback.{}",
                    context.unwrap_or_default()
                );
            } else {
                println!(
                    "      [Brain] Solar AST extraction failed after sanitization and chunked AST recovery: {}. Using lexical fallback.{}",
                    e,
                    context.unwrap_or_default()
                );
            }
            Ok(lexical_extract(&sanitized))
        }
    }
}

fn parse_with_solar(code: &str) -> Result<ExtractionResult, String> {
    let temp_dir = std::env::temp_dir();
    let temp_file = temp_dir.join(format!(
        "sol_resurrect_temp_{}_{}.sol",
        std::process::id(),
        std::thread::current().name().unwrap_or("worker")
    ));
    std::fs::write(&temp_file, code).map_err(|e| format!("Failed to write temp file: {}", e))?;

    // Solar may panic internally on malformed/incomplete resurrection slices.
    // Isolate the panic by spawning a separate thread. This prevents Tokio worker
    // poisoning and safely drops any broken thread-local state left by Solar.
    let temp_file_clone = temp_file.clone();
    let handle = std::thread::Builder::new()
        .name("solar_ast_worker".to_string())
        .spawn(move || {
            let sess = Session::builder()
                .with_buffer_emitter(ColorChoice::Never)
                .build();
            sess.enter(|| {
                let arena = ast::Arena::new();
                let mut parser = Parser::from_file(&sess, &arena, &temp_file_clone)
                    .map_err(|_| "Parser creation failed".to_string())?;

                let ast_unit = parser.parse_file().map_err(|e| {
                    e.emit();
                    "Parsing failed".to_string()
                })?;

                let mut visitor = ContextVisitor::new();
                visitor.visit_source_unit(&ast_unit);

                Ok::<ExtractionResult, String>(visitor.build_result())
            })
        });

    let parse_result = match handle {
        Ok(thread) => thread
            .join()
            .unwrap_or_else(|_| Err("Thread panicked".to_string())),
        Err(e) => Err(format!("Failed to spawn thread: {}", e)),
    };

    // Clean up even when Solar panics while parsing malformed generated Solidity.
    let _ = std::fs::remove_file(temp_file);

    parse_result
}

fn parse_top_level_chunks_with_solar(code: &str) -> Option<ExtractionResult> {
    let chunks = normalizer::split_top_level_chunks(code);
    let mut combined = ExtractionResult::default();
    let mut parsed_any = false;

    for chunk in chunks {
        let chunk = normalizer::normalize_solidity_fragment(&chunk);
        if !normalizer::looks_parse_worthy(&chunk) {
            continue;
        }

        if let Ok(result) = parse_with_solar(&chunk) {
            parsed_any = true;
            combined
                .missing_interfaces
                .extend(result.missing_interfaces);
            combined.missing_mocks.extend(result.missing_mocks);
            combined.missing_errors.extend(result.missing_errors);
        }
    }

    if parsed_any {
        combined.missing_interfaces.sort();
        combined.missing_interfaces.dedup();
        combined.missing_mocks.sort();
        combined.missing_mocks.dedup();
        combined.missing_errors.sort();
        combined.missing_errors.dedup();
        Some(combined)
    } else {
        None
    }
}

pub fn sanitize_resurrection_source(code: &str) -> String {
    normalizer::normalize_solidity_fragment(code)
}

fn lexical_extract(code: &str) -> ExtractionResult {
    let cleaned = strip_comments_and_strings(code);
    let defined_types = collect_defined_types(&cleaned);
    let builtins: HashSet<&str> = [
        // Test actors/placeholders
        "Actual",
        "Alice",
        "Auto",
        "Available",
        "Baseline",
        "Bob",
        "Charlie",
        "Context",
        "Dave",
        "Error",
        "Test",
        // Solidity built-in globals
        "abi",
        "msg",
        "block",
        "tx",
        "this",
        "super",
        "type",
        // Common library contracts
        "Address",
        "Bytes",
        "SafeERC20",
        "SafeMath",
        // Foundry test framework
        "Vm",
        "VmSafe",
        "console",
        "console2",
        "safeconsole",
        "StdChains",
        "StdCheatsSafe",
        "StdStyle",
        "StdAssertions",
        "StdInvariant",
        "StdUtils",
        "stdJson",
        "stdToml",
        "stdStorage",
        "stdStorageSafe",
        "stdMath",
        "StdStorage",
        "Multicall",
        // OpenZeppelin common contracts
        "ERC1155",
        "ERC1155Holder",
        "ERC165",
        "ERC721",
        "IERC165",
        "IERC1155Receiver",
        "IERC20Metadata",
        "IERC721",
        "Ownable",
        "Pausable",
        "ReentrancyGuard",
    ]
    .into_iter()
    .collect();

    let mut found_interfaces = HashSet::new();
    let mut found_mocks = HashSet::new();
    let mut found_errors = HashSet::new();
    let tokens = tokenize_identifiers(&cleaned);

    for window in tokens.windows(2) {
        let current = window[0].as_str();
        let next = window[1].as_str();
        if current == "revert" && is_upper_ident(next) {
            found_errors.insert(next.to_string());
        }
        if current == "new" && is_upper_ident(next) {
            classify_type_name(next, &mut found_interfaces, &mut found_mocks);
        }
    }

    for window in tokens.windows(3) {
        let owner = window[0].as_str();
        let separator = window[1].as_str();
        if separator == "."
            && is_upper_ident(owner)
            && !defined_types.contains(owner)
            && !builtins.contains(owner)
        {
            classify_type_name(owner, &mut found_interfaces, &mut found_mocks);
        }
    }

    for token in &tokens {
        if !is_upper_ident(token)
            || defined_types.contains(token.as_str())
            || builtins.contains(token.as_str())
        {
            continue;
        }
        if looks_like_interface(token) {
            found_interfaces.insert(token.clone());
        }
    }

    let mut missing_interfaces: Vec<String> = found_interfaces
        .into_iter()
        .filter(|name| !defined_types.contains(name.as_str()))
        .collect();
    let mut missing_mocks: Vec<String> = found_mocks
        .into_iter()
        .filter(|name| !defined_types.contains(name.as_str()) && !builtins.contains(name.as_str()))
        .collect();
    let mut missing_errors: Vec<String> = found_errors
        .into_iter()
        .filter(|name| !defined_types.contains(name.as_str()))
        .collect();

    missing_interfaces.sort();
    missing_interfaces.dedup();
    missing_mocks.sort();
    missing_mocks.dedup();
    missing_errors.sort();
    missing_errors.dedup();

    ExtractionResult {
        missing_interfaces,
        missing_mocks,
        missing_errors,
    }
}

fn classify_type_name(name: &str, interfaces: &mut HashSet<String>, mocks: &mut HashSet<String>) {
    if looks_like_constant_or_state_identifier(name) {
        return;
    }
    if looks_like_interface(name) {
        interfaces.insert(name.to_string());
    } else {
        mocks.insert(name.to_string());
    }
}

fn looks_like_interface(name: &str) -> bool {
    name.starts_with('I') && name.chars().nth(1).map_or(false, |c| c.is_uppercase())
}

fn is_upper_ident(name: &str) -> bool {
    name.chars()
        .next()
        .map_or(false, |c| c.is_ascii_uppercase())
}

fn looks_like_constant_or_state_identifier(name: &str) -> bool {
    let has_alpha = name.chars().any(|ch| ch.is_ascii_alphabetic());
    has_alpha
        && name
            .chars()
            .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == '_')
        && name.contains('_')
}

fn looks_like_custom_type_name(name: &str) -> bool {
    name.starts_with(|c: char| c.is_uppercase()) && !looks_like_constant_or_state_identifier(name)
}

fn collect_defined_types(code: &str) -> HashSet<String> {
    let mut defined = HashSet::new();
    let tokens = tokenize_identifiers(code);
    for window in tokens.windows(2) {
        if matches!(
            window[0].as_str(),
            "contract" | "interface" | "library" | "struct" | "enum" | "error" | "type"
        ) {
            defined.insert(window[1].clone());
        }
    }
    defined
}

fn tokenize_identifiers(code: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for ch in code.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            current.push(ch);
        } else {
            if !current.is_empty() {
                tokens.push(std::mem::take(&mut current));
            }
            if ch == '.' {
                tokens.push(".".to_string());
            }
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn strip_comments_and_strings(code: &str) -> String {
    let mut out = String::with_capacity(code.len());
    let mut chars = code.chars().peekable();
    let mut in_line_comment = false;
    let mut in_block_comment = false;
    let mut in_string: Option<char> = None;
    let mut escaped = false;

    while let Some(ch) = chars.next() {
        if in_line_comment {
            if ch == '\n' {
                in_line_comment = false;
                out.push('\n');
            } else {
                out.push(' ');
            }
            continue;
        }

        if in_block_comment {
            if ch == '*' && chars.peek() == Some(&'/') {
                chars.next();
                in_block_comment = false;
                out.push(' ');
                out.push(' ');
            } else if ch == '\n' {
                out.push('\n');
            } else {
                out.push(' ');
            }
            continue;
        }

        if let Some(quote) = in_string {
            if ch == '\n' {
                in_string = None;
                out.push('\n');
            } else {
                out.push(' ');
                if ch == quote && !escaped {
                    in_string = None;
                }
                escaped = ch == '\\' && !escaped;
                if ch != '\\' {
                    escaped = false;
                }
            }
            continue;
        }

        if ch == '/' && chars.peek() == Some(&'/') {
            chars.next();
            in_line_comment = true;
            out.push(' ');
            out.push(' ');
        } else if ch == '/' && chars.peek() == Some(&'*') {
            chars.next();
            in_block_comment = true;
            out.push(' ');
            out.push(' ');
        } else if ch == '"' || ch == '\'' {
            in_string = Some(ch);
            escaped = false;
            out.push(' ');
        } else {
            out.push(ch);
        }
    }
    out
}

struct ContextVisitor {
    found_interfaces: HashSet<String>,
    found_mocks: HashSet<String>,
    found_errors: HashSet<String>,
    defined_types: HashSet<String>,
}

impl ContextVisitor {
    fn new() -> Self {
        Self {
            found_interfaces: HashSet::new(),
            found_mocks: HashSet::new(),
            found_errors: HashSet::new(),
            defined_types: HashSet::new(),
        }
    }

    fn build_result(self) -> ExtractionResult {
        // Filter out types that are already defined in the AST
        let mut missing_interfaces = Vec::new();
        for i in self.found_interfaces {
            if !self.defined_types.contains(&i) {
                missing_interfaces.push(i);
            }
        }

        let mut missing_mocks = Vec::new();
        let builtins = [
            // Test actors/placeholders
            "Actual",
            "Alice",
            "Auto",
            "Available",
            "Baseline",
            "Bob",
            "Charlie",
            "Context",
            "Dave",
            "Error",
            "Test",
            // Foundry test framework
            "Vm",
            "VmSafe",
            "console",
            "console2",
            "safeconsole",
            "StdChains",
            "StdCheatsSafe",
            "StdStyle",
            "StdAssertions",
            "StdInvariant",
            "StdUtils",
            "stdJson",
            "stdToml",
            "stdStorage",
            "stdStorageSafe",
            "stdMath",
            "StdStorage",
            "Multicall",
            // OpenZeppelin common contracts
            "ERC1155",
            "ERC1155Holder",
            "ERC165",
            "ERC721",
            "IERC165",
            "IERC1155Receiver",
            "IERC20Metadata",
            "IERC721",
            "Ownable",
            "Pausable",
            "ReentrancyGuard",
        ];
        for m in self.found_mocks {
            if !builtins.contains(&m.as_str()) && !self.defined_types.contains(&m) {
                missing_mocks.push(m);
            }
        }

        let mut missing_errors = Vec::new();
        for e in self.found_errors {
            if !self.defined_types.contains(&e) {
                missing_errors.push(e);
            }
        }

        ExtractionResult {
            missing_interfaces,
            missing_mocks,
            missing_errors,
        }
    }

    fn visit_source_unit(&mut self, unit: &SourceUnit) {
        for item in unit.items.iter() {
            self.visit_item(item);
        }
    }

    fn visit_item(&mut self, item: &Item) {
        match &item.kind {
            ItemKind::Contract(contract) => {
                self.defined_types.insert(contract.name.to_string());
                for base in contract.bases.iter() {
                    if let Some(last) = base.name.segments().last() {
                        let name = last.as_str().to_string();
                        if name.starts_with('I')
                            && name
                                .chars()
                                .nth(1)
                                .map_or(false, |c: char| c.is_uppercase())
                        {
                            self.found_interfaces.insert(name);
                        } else if looks_like_custom_type_name(&name) {
                            self.found_mocks.insert(name);
                        }
                    }
                }
                for body_item in contract.body.iter() {
                    self.visit_item(body_item);
                }
            }
            ItemKind::Function(func) => {
                // Record parameters
                for param in func.header.parameters.vars.iter() {
                    self.visit_type(&param.ty);
                }
                // Record return parameters
                if let Some(returns) = &func.header.returns {
                    for param in returns.vars.iter() {
                        self.visit_type(&param.ty);
                    }
                }
                // Visit body
                if let Some(block) = &func.body {
                    self.visit_block(block);
                }
            }
            ItemKind::Variable(var) => {
                self.visit_type(&var.ty);
                if let Some(expr) = &var.initializer {
                    self.visit_expr(expr);
                }
            }
            ItemKind::Error(error) => {
                self.defined_types.insert(error.name.as_str().to_string());
                for param in error.parameters.vars.iter() {
                    self.visit_type(&param.ty);
                }
            }
            ItemKind::Struct(strct) => {
                self.defined_types.insert(strct.name.to_string());
                for field in strct.fields.iter() {
                    self.visit_type(&field.ty);
                }
            }
            ItemKind::Udvt(udvt) => {
                self.defined_types.insert(udvt.name.to_string());
                self.visit_type(&udvt.ty);
            }
            ItemKind::Enum(enm) => {
                self.defined_types.insert(enm.name.to_string());
            }
            ItemKind::Using(using) => match &using.list {
                ast::UsingList::Single(path) => {
                    if let Some(last) = path.segments().last() {
                        let name = last.as_str().to_string();
                        if looks_like_custom_type_name(&name) {
                            self.found_mocks.insert(name);
                        }
                    }
                }
                ast::UsingList::Multiple(list) => {
                    for (path, _) in list.iter() {
                        if let Some(last) = path.segments().last() {
                            let name = last.as_str().to_string();
                            if looks_like_custom_type_name(&name) {
                                self.found_mocks.insert(name);
                            }
                        }
                    }
                }
            },
            _ => {}
        }
    }

    fn visit_block(&mut self, block: &ast::Block) {
        for stmt in block.stmts.iter() {
            self.visit_stmt(stmt);
        }
    }

    fn visit_stmt(&mut self, stmt: &Stmt) {
        match &stmt.kind {
            StmtKind::Expr(expr) => self.visit_expr(expr),
            StmtKind::Revert(path, _) => {
                if let Some(last) = path.segments().last() {
                    let name = last.as_str().to_string();
                    if name.starts_with(|c: char| c.is_uppercase()) {
                        self.found_errors.insert(name);
                    }
                }
            }
            StmtKind::DeclSingle(var_decl) => {
                self.visit_type(&var_decl.ty);
                if let Some(expr) = &var_decl.initializer {
                    self.visit_expr(expr);
                }
            }
            StmtKind::DeclMulti(_, expr) => {
                self.visit_expr(expr);
            }
            StmtKind::If(cond, then_br, else_br) => {
                self.visit_expr(cond);
                self.visit_stmt(then_br);
                if let Some(e) = else_br {
                    self.visit_stmt(e);
                }
            }
            StmtKind::While(cond, body) | StmtKind::DoWhile(body, cond) => {
                self.visit_expr(cond);
                self.visit_stmt(body);
            }
            StmtKind::For {
                init,
                cond,
                next,
                body,
            } => {
                if let Some(i) = init {
                    self.visit_stmt(i);
                }
                if let Some(c) = cond {
                    self.visit_expr(c);
                }
                if let Some(n) = next {
                    self.visit_expr(n);
                }
                self.visit_stmt(body);
            }
            StmtKind::Block(block) | StmtKind::UncheckedBlock(block) => {
                self.visit_block(block);
            }
            StmtKind::Return(Some(expr)) => self.visit_expr(expr),
            StmtKind::Emit(path, _) => {
                if let Some(last) = path.segments().last() {
                    let name = last.as_str().to_string();
                    if name.starts_with(|c: char| c.is_uppercase()) {
                        // Might be an event, not adding to errors
                    }
                }
            }
            _ => {}
        }
    }

    fn visit_expr(&mut self, expr: &Expr) {
        match &expr.kind {
            ExprKind::New(ty) => {
                self.visit_type(ty);
                if let TypeKind::Custom(path) = &ty.kind {
                    if let Some(last) = path.segments().last() {
                        let name = last.as_str().to_string();
                        if name.starts_with('I')
                            && name
                                .chars()
                                .nth(1)
                                .map_or(false, |c: char| c.is_uppercase())
                        {
                            self.found_interfaces.insert(name);
                        } else if looks_like_custom_type_name(&name) {
                            self.found_mocks.insert(name);
                        }
                    }
                }
            }
            ExprKind::Call(func, args) => {
                self.visit_expr(func);
                for arg in args.exprs() {
                    self.visit_expr(arg);
                }

                // Track `IInterface(address)`
                if let ExprKind::Ident(ident) = &func.kind {
                    let name = ident.as_str().to_string();
                    if name.starts_with('I')
                        && name
                            .chars()
                            .nth(1)
                            .map_or(false, |c: char| c.is_uppercase())
                    {
                        self.found_interfaces.insert(name);
                    }
                }
            }
            ExprKind::Member(obj, _) => {
                self.visit_expr(obj);
                // Track `MockContract.member`
                if let ExprKind::Ident(ident) = &obj.kind {
                    let name = ident.as_str().to_string();
                    if name.starts_with('I')
                        && name
                            .chars()
                            .nth(1)
                            .map_or(false, |c: char| c.is_uppercase())
                    {
                        self.found_interfaces.insert(name);
                    } else if looks_like_custom_type_name(&name)
                        && name != "abi"
                        && name != "msg"
                        && name != "block"
                        && name != "tx"
                    {
                        self.found_mocks.insert(name);
                    }
                }
            }
            ExprKind::Assign(lhs, _, rhs) | ExprKind::Binary(lhs, _, rhs) => {
                self.visit_expr(lhs);
                self.visit_expr(rhs);
            }
            ExprKind::Tuple(exprs) => {
                for opt in exprs.iter() {
                    if let solar_interface::SpannedOption::Some(e) = opt {
                        self.visit_expr(e);
                    }
                }
            }
            ExprKind::Array(exprs) => {
                for e in exprs.iter() {
                    self.visit_expr(e);
                }
            }
            ExprKind::Ternary(cond, t, f) => {
                self.visit_expr(cond);
                self.visit_expr(t);
                self.visit_expr(f);
            }
            ExprKind::Unary(_, e) => self.visit_expr(e),
            ExprKind::Index(obj, idx) => {
                self.visit_expr(obj);
                match idx {
                    ast::IndexKind::Index(Some(e)) => self.visit_expr(e),
                    ast::IndexKind::Range(l, r) => {
                        if let Some(e) = l {
                            self.visit_expr(e);
                        }
                        if let Some(e) = r {
                            self.visit_expr(e);
                        }
                    }
                    _ => {}
                }
            }
            _ => {}
        }
    }

    fn visit_type(&mut self, ty: &Type) {
        if let TypeKind::Custom(path) = &ty.kind {
            if let Some(last) = path.segments().last() {
                let name = last.as_str().to_string();
                if name.starts_with('I')
                    && name
                        .chars()
                        .nth(1)
                        .map_or(false, |c: char| c.is_uppercase())
                {
                    self.found_interfaces.insert(name);
                } else if looks_like_custom_type_name(&name) {
                    self.found_mocks.insert(name);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sanitizer_drops_orphan_natspec_fragments() {
        let input = r#"
type LiquidityChunk is uint256;
using LiquidityChunkLibrary for LiquidityChunk global;
 * @dev Standard math utilities missing in the Solidity language.
 */
contract Example {}
"#;

        let sanitized = sanitize_resurrection_source(input);

        assert!(sanitized.contains("type LiquidityChunk is uint256;"));
        assert!(sanitized.contains("contract Example {}"));
        assert!(!sanitized.contains("@dev Standard math utilities"));
        assert!(!sanitized.contains("*/"));
    }

    #[test]
    fn sanitizer_drops_bare_section_labels_without_touching_code() {
        let input = r#"
MOCKS
contract MockToken {}
TESTS
contract PoC {
    uint256 INITIAL_BALANCE;
}
"#;

        let sanitized = sanitize_resurrection_source(input);

        assert!(!sanitized.lines().any(|line| line.trim() == "MOCKS"));
        assert!(!sanitized.lines().any(|line| line.trim() == "TESTS"));
        assert!(sanitized.contains("contract MockToken {}"));
        assert!(sanitized.contains("uint256 INITIAL_BALANCE;"));
    }

    #[test]
    fn lexical_fallback_ignores_words_from_orphan_comments() {
        let input = r#"
contract Example {
    function run() external {
        revert MissingError();
    }
}
 * [IMPORTANT]
 * INITIAL_BALANCE should not be detected from comments.
 */
"#;

        let sanitized = sanitize_resurrection_source(input);
        let extraction = lexical_extract(&sanitized);

        assert_eq!(extraction.missing_interfaces, Vec::<String>::new());
        assert_eq!(extraction.missing_errors, vec!["MissingError".to_string()]);
    }

    #[test]
    fn parse_and_extract_retries_with_sanitized_source() {
        let input = r#"
contract Example {
    function run() external {
        revert MissingError();
    }
}
 * @dev orphaned comment from a sliced doc block.
 */
"#;

        let extraction = parse_and_extract(input).expect("sanitized source should be parseable");

        assert_eq!(extraction.missing_errors, vec!["MissingError".to_string()]);
    }
}
