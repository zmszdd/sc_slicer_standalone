//! SolResurrect - AST-based Solidity Code Reconstruction Module
//!
//! This module takes fragmented/sliced Solidity code and reconstructs it into
//! a compilable file by inferring the correct placement of orphaned functions
//! using AST-based context analysis.
//!
//! ## Architecture
//! 
//! Phase 1: Resilient AST Parsing (handles incomplete code)
//! Phase 2: Context Inference Engine (Def-Use Analysis)
//! Phase 3: Code Reassembly (topologically sorted output)

use solar_ast::{self as ast, Item, ItemKind, Expr, ExprKind, Stmt, StmtKind, SourceUnit};
use solar_interface::{Session, source_map::FileName};
use solar_parse::Parser;
use std::collections::{HashMap, HashSet};
use anyhow::{Result, Context as AnyhowContext};

/// Represents the context of orphaned code elements
#[derive(Debug, Default)]
pub struct CodeFragment {
    /// Global type definitions (type, struct, enum, using...global)
    pub global_types: Vec<String>,
    
    /// Library definitions
    pub libraries: Vec<ContractBlock>,
    
    /// Interface definitions
    pub interfaces: Vec<ContractBlock>,
    
    /// Contract definitions (non-test)
    pub contracts: Vec<ContractBlock>,
    
    /// Orphaned functions (no parent contract)
    pub orphan_functions: Vec<FunctionBlock>,
    
    /// Orphaned state variables
    pub orphan_variables: Vec<String>,
    
    /// The main test contract
    pub test_contract: Option<ContractBlock>,
    
    /// Pragma and import statements
    pub preamble: Vec<String>,
}

/// Represents a contract/library/interface block with its source code
#[derive(Debug, Clone)]
pub struct ContractBlock {
    pub name: String,
    pub kind: ContractKind,
    pub source_code: String,
    pub state_variables: HashSet<String>, // Variable names defined in this contract
    pub functions: Vec<String>, // Function names
    pub span_start: usize,
    pub span_end: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ContractKind {
    Contract,
    Library,
    Interface,
    AbstractContract,
}

/// Represents an orphaned function with usage analysis
#[derive(Debug, Clone)]
pub struct FunctionBlock {
    pub name: String,
    pub source_code: String,
    pub referenced_identifiers: HashSet<String>, // Variables/functions referenced inside
    pub span_start: usize,
    pub span_end: usize,
}

/// The main context inference engine
pub struct ContextInference {
    /// Map: Contract Name -> State Variables
    contract_defs: HashMap<String, HashSet<String>>,
    
    /// Map: Function Name -> Referenced Identifiers
    function_uses: HashMap<String, HashSet<String>>,
    
    /// Map: Variable Name -> Contract Name (reverse lookup)
    variable_to_contract: HashMap<String, String>,
}

impl ContextInference {
    pub fn new() -> Self {
        Self {
            contract_defs: HashMap::new(),
            function_uses: HashMap::new(),
            variable_to_contract: HashMap::new(),
        }
    }
    
    /// Phase A: Build the "Def" map by traversing contract state variables
    pub fn build_def_map(&mut self, contracts: &[ContractBlock]) {
        for contract in contracts {
            self.contract_defs.insert(
                contract.name.clone(),
                contract.state_variables.clone()
            );
            
            // Build reverse lookup
            for var in &contract.state_variables {
                self.variable_to_contract.insert(var.clone(), contract.name.clone());
            }
        }
        
        println!("📊 [Def Map] Built definitions for {} contracts", contracts.len());
        for (contract, vars) in &self.contract_defs {
            println!("   - {}: {} state variables", contract, vars.len());
        }
    }
    
    /// Phase B: Build the "Use" map by analyzing function bodies
    pub fn build_use_map(&mut self, functions: &[FunctionBlock]) {
        for func in functions {
            self.function_uses.insert(
                func.name.clone(),
                func.referenced_identifiers.clone()
            );
        }
        
        println!("📊 [Use Map] Analyzed {} orphaned functions", functions.len());
        for (func, refs) in &self.function_uses {
            println!("   - {}: references {} identifiers", func, refs.len());
        }
    }
    
    /// Phase C: Scoring & Re-homing
    /// Calculate affinity between orphaned functions and contracts
    pub fn calculate_affinity(&self, func_name: &str, contract_name: &str) -> usize {
        let func_uses = self.function_uses.get(func_name).cloned().unwrap_or_default();
        let contract_defs = self.contract_defs.get(contract_name).cloned().unwrap_or_default();
        
        // Score = Intersection(func.uses, contract.defs)
        func_uses.intersection(&contract_defs).count()
    }
    
    /// Find the best home for an orphaned function
    pub fn infer_home(&self, func: &FunctionBlock) -> Option<String> {
        println!("🔍 [Inference] Finding home for function '{}'", func.name);
        println!("   References: {:?}", func.referenced_identifiers);
        
        // Heuristic A: Call-site matching (check if function name suggests a contract)
        // e.g., setMockPositionBalanceArray -> MockPanopticPool
        if func.name.starts_with("setMock") || func.name.starts_with("getMock") {
            for contract_name in self.contract_defs.keys() {
                if contract_name.contains("Mock") {
                    println!("   ✓ Heuristic A (Mock pattern): Assigning to {}", contract_name);
                    return Some(contract_name.clone());
                }
            }
        }
        
        // Heuristic B: Variable matching - find contract with highest affinity
        let mut best_contract: Option<String> = None;
        let mut best_score = 0;
        
        for contract_name in self.contract_defs.keys() {
            let score = self.calculate_affinity(&func.name, contract_name);
            if score > best_score {
                best_score = score;
                best_contract = Some(contract_name.clone());
            }
        }
        
        if best_score > 0 {
            println!("   ✓ Heuristic B (Affinity): Assigning to {} (score: {})", 
                     best_contract.as_ref().unwrap(), best_score);
            return best_contract;
        }
        
        // Heuristic C: Name-based inference
        // e.g., computeNAV -> PanopticVaultAccountant (if "accountant" mentioned)
        for ident in &func.referenced_identifiers {
            if let Some(contract) = self.variable_to_contract.get(ident) {
                println!("   ✓ Heuristic C (Variable ownership): Assigning to {}", contract);
                return Some(contract.clone());
            }
        }
        
        println!("   ✗ No suitable home found");
        None
    }
}

/// Main SolResurrect tool
pub struct SolResurrect {
    raw_code: String,
    session: Session,
}

impl SolResurrect {
    pub fn new(raw_code: String) -> Self {
        let session = Session::builder()
            .with_buffer_emitter(solar_interface::ColorChoice::Never)
            .build();
        
        Self { raw_code, session }
    }
    
    /// Phase 1: Parse the fragmented code (with resilience)
    pub fn parse_slice(&self) -> Result<CodeFragment> {
        println!("🔧 [Phase 1] Parsing fragmented Solidity code...");
        
        // Strategy 1: Try direct parsing
        let result = self.session.enter(|| -> solar_interface::Result<SourceUnit> {
            let arena = ast::Arena::new();
            
            // Write to temp file (required by solar parser)
            let temp_dir = std::env::temp_dir();
            let temp_file = temp_dir.join("fragment.sol");
            if let Err(e) = std::fs::write(&temp_file, &self.raw_code) {
                eprintln!("Failed to write temp file: {}", e);
                return Ok(CodeFragment::default());
            }
            
            let mut parser = Parser::from_file(&self.session, &arena, &temp_file)?;
            parser.parse_file().map_err(|e| e.emit())
        });
        
        match result {
            Ok(ast) => {
                println!("   ✓ Direct parsing succeeded");
                self.fragment_code(ast)
            }
            Err(_) => {
                println!("   ⚠ Direct parsing failed, trying resilient mode...");
                self.parse_with_wrapper()
            }
        }
    }
    
    /// Resilient parsing: wrap orphaned code in a dummy contract
    fn parse_with_wrapper(&self) -> Result<CodeFragment> {
        let wrapped_code = format!(
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract __Wrapper__ {{\n{}\n}}",
            self.raw_code
        );
        
        let result = self.session.enter(|| -> solar_interface::Result<SourceUnit> {
            let arena = ast::Arena::new();
            let temp_dir = std::env::temp_dir();
            let temp_file = temp_dir.join("wrapped_fragment.sol");
            if let Err(e) = std::fs::write(&temp_file, &wrapped_code) {
                eprintln!("Failed to write temp file: {}", e);
                return Ok(CodeFragment::default());
            }
            
            let mut parser = Parser::from_file(&self.session, &arena, &temp_file)?;
            parser.parse_file().map_err(|e| e.emit())
        });
        
        match result {
            Ok(ast) => {
                println!("   ✓ Wrapped parsing succeeded");
                // Extract from wrapper and adjust offsets
                self.fragment_code_from_wrapper(ast)
            }
            Err(e) => {
                anyhow::bail!("Both direct and wrapped parsing failed: {:?}", e)
            }
        }
    }
    
    /// Fragment the AST into logical buckets
    fn fragment_code(&self, ast: SourceUnit) -> Result<CodeFragment> {
        let mut fragment = CodeFragment::default();
        
        for item in ast.items.iter() {
            match &item.kind {
                ItemKind::Pragma(pragma) => {
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    fragment.preamble.push(code);
                }
                ItemKind::Import(import) => {
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    fragment.preamble.push(code);
                }
                ItemKind::Using(_) => {
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    fragment.global_types.push(code);
                }
                ItemKind::Struct(_) | ItemKind::Enum(_) | ItemKind::Udvt(_) => {
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    fragment.global_types.push(code);
                }
                ItemKind::Contract(contract) => {
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    
                    let kind = match contract.kind {
                        ast::ContractKind::Contract => ContractKind::Contract,
                        ast::ContractKind::Library => ContractKind::Library,
                        ast::ContractKind::Interface => ContractKind::Interface,
                        ast::ContractKind::AbstractContract => ContractKind::AbstractContract,
                    };
                    
                    // Extract state variables
                    let mut state_vars = HashSet::new();
                    let mut functions = Vec::new();
                    
                    for body_item in contract.body.iter() {
                        match &body_item.kind {
                            ItemKind::Variable(var) => {
                                if let Some(name) = &var.name {
                                    state_vars.insert(name.to_string());
                                }
                            }
                            ItemKind::Function(func) => {
                                if let Some(name) = &func.header.name {
                                    functions.push(name.to_string());
                                }
                            }
                            _ => {}
                        }
                    }
                    
                    let contract_block = ContractBlock {
                        name: contract.name.to_string(),
                        kind,
                        source_code: code,
                        state_variables: state_vars,
                        functions,
                        span_start: span.lo().to_usize(),
                        span_end: span.hi().to_usize(),
                    };
                    
                    // Categorize contracts
                    let is_test = contract.name.to_string().contains("Test") 
                        || contract.name.to_string() == "PoC";
                    
                    if is_test {
                        fragment.test_contract = Some(contract_block);
                    } else {
                        match contract_block.kind {
                            ContractKind::Library => fragment.libraries.push(contract_block),
                            ContractKind::Interface => fragment.interfaces.push(contract_block),
                            _ => fragment.contracts.push(contract_block),
                        }
                    }
                }
                ItemKind::Function(func) => {
                    // Orphaned function (not inside any contract)
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    
                    let name = func.header.name
                        .as_ref()
                        .map(|n| n.to_string())
                        .unwrap_or_else(|| "anonymous".to_string());
                    
                    // Analyze function body to extract referenced identifiers
                    let referenced_ids = if let Some(body) = &func.body {
                        self.extract_identifiers_from_block(body)
                    } else {
                        HashSet::new()
                    };
                    
                    fragment.orphan_functions.push(FunctionBlock {
                        name,
                        source_code: code,
                        referenced_identifiers: referenced_ids,
                        span_start: span.lo().to_usize(),
                        span_end: span.hi().to_usize(),
                    });
                }
                ItemKind::Variable(_) => {
                    // Orphaned state variable
                    let span = item.span;
                    let code = self.extract_span_text(span.lo().to_usize(), span.hi().to_usize());
                    fragment.orphan_variables.push(code);
                }
                _ => {}
            }
        }
        
        println!("   📦 Fragmentation complete:");
        println!("      - Preamble: {} items", fragment.preamble.len());
        println!("      - Global types: {} items", fragment.global_types.len());
        println!("      - Libraries: {}", fragment.libraries.len());
        println!("      - Interfaces: {}", fragment.interfaces.len());
        println!("      - Contracts: {}", fragment.contracts.len());
        println!("      - Orphan functions: {}", fragment.orphan_functions.len());
        println!("      - Test contract: {}", if fragment.test_contract.is_some() { "Yes" } else { "No" });
        
        Ok(fragment)
    }
    
    /// Extract from wrapper (adjust offsets)
    fn fragment_code_from_wrapper(&self, ast: SourceUnit) -> Result<CodeFragment> {
        // Similar to fragment_code but extract from the wrapper contract
        // For MVP, just use direct extraction
        self.fragment_code(ast)
    }
    
    /// Extract identifiers from a statement block (recursive)
    fn extract_identifiers_from_block(&self, block: &ast::Block) -> HashSet<String> {
        let mut identifiers = HashSet::new();
        
        for stmt in block.stmts.iter() {
            self.extract_identifiers_from_stmt(stmt, &mut identifiers);
        }
        
        identifiers
    }
    
    /// Extract identifiers from a statement (recursive traversal)
    fn extract_identifiers_from_stmt(&self, stmt: &Stmt, identifiers: &mut HashSet<String>) {
        match &stmt.kind {
            StmtKind::Expr(expr) => {
                self.extract_identifiers_from_expr(expr, identifiers);
            }
            StmtKind::DeclSingle(_, _) | StmtKind::DeclMulti(_, _) => {
                // Variable declarations - skip for now
            }
            StmtKind::If(cond, then_branch, else_branch) => {
                self.extract_identifiers_from_expr(cond, identifiers);
                self.extract_identifiers_from_stmt(then_branch, identifiers);
                if let Some(else_stmt) = else_branch {
                    self.extract_identifiers_from_stmt(else_stmt, identifiers);
                }
            }
            StmtKind::While(cond, body) => {
                self.extract_identifiers_from_expr(cond, identifiers);
                self.extract_identifiers_from_stmt(body, identifiers);
            }
            StmtKind::For { init, cond, next, body, .. } => {
                if let Some(init) = init {
                    self.extract_identifiers_from_stmt(init, identifiers);
                }
                if let Some(cond) = cond {
                    self.extract_identifiers_from_expr(cond, identifiers);
                }
                if let Some(next) = next {
                    self.extract_identifiers_from_expr(next, identifiers);
                }
                self.extract_identifiers_from_stmt(body, identifiers);
            }
            StmtKind::Return(expr) => {
                if let Some(expr) = expr {
                    self.extract_identifiers_from_expr(expr, identifiers);
                }
            }
            StmtKind::Block(block) => {
                for stmt in block.stmts.iter() {
                    self.extract_identifiers_from_stmt(stmt, identifiers);
                }
            }
            _ => {}
        }
    }
    
    /// Extract identifiers from an expression (the core of Def-Use analysis)
    fn extract_identifiers_from_expr(&self, expr: &Expr, identifiers: &mut HashSet<String>) {
        match &expr.kind {
            ExprKind::Ident(ident) => {
                identifiers.insert(ident.to_string());
            }
            ExprKind::Member(target, member) => {
                self.extract_identifiers_from_expr(target, identifiers);
                identifiers.insert(member.to_string());
            }
            ExprKind::Call(target, args) => {
                self.extract_identifiers_from_expr(target, identifiers);
                for arg in args.args.iter() {
                    self.extract_identifiers_from_expr(arg, identifiers);
                }
            }
            ExprKind::Index(target, index) => {
                self.extract_identifiers_from_expr(target, identifiers);
                if let Some(idx) = index {
                    self.extract_identifiers_from_expr(idx, identifiers);
                }
            }
            ExprKind::Binary(op, left, right) => {
                self.extract_identifiers_from_expr(left, identifiers);
                self.extract_identifiers_from_expr(right, identifiers);
            }
            ExprKind::Unary(op, expr) => {
                self.extract_identifiers_from_expr(expr, identifiers);
            }
            ExprKind::Ternary(cond, if_true, if_false) => {
                self.extract_identifiers_from_expr(cond, identifiers);
                self.extract_identifiers_from_expr(if_true, identifiers);
                self.extract_identifiers_from_expr(if_false, identifiers);
            }
            _ => {}
        }
    }
    
    /// Extract source text from span
    fn extract_span_text(&self, start: usize, end: usize) -> String {
        if start < self.raw_code.len() && end <= self.raw_code.len() {
            self.raw_code[start..end].to_string()
        } else {
            String::new()
        }
    }
    
    /// Phase 2: Infer context and re-home orphaned functions
    pub fn infer_context(&self, fragment: &mut CodeFragment) -> Result<()> {
        println!("\n🧠 [Phase 2] Context Inference (Def-Use Analysis)...");
        
        let mut inference = ContextInference::new();
        
        // Build Def Map from existing contracts
        inference.build_def_map(&fragment.contracts);
        
        // Build Use Map from orphaned functions
        inference.build_use_map(&fragment.orphan_functions);
        
        // Re-home each orphaned function
        let mut re_homed = Vec::new();
        
        for func in &fragment.orphan_functions {
            if let Some(contract_name) = inference.infer_home(func) {
                re_homed.push((func.clone(), contract_name));
            }
        }
        
        // Apply re-homing by injecting functions into contracts
        for (func, contract_name) in re_homed {
            if let Some(contract) = fragment.contracts.iter_mut()
                .find(|c| c.name == contract_name) {
                    
                // Inject function before the closing brace
                let closing_brace_pos = contract.source_code.rfind('}')
                    .unwrap_or(contract.source_code.len());
                
                contract.source_code.insert_str(closing_brace_pos, &format!("\n    {}\n", func.source_code));
                contract.functions.push(func.name.clone());
                
                println!("   ✓ Injected '{}' into '{}'", func.name, contract_name);
            }
        }
        
        Ok(())
    }
    
    /// Phase 3: Generate library stubs for missing dependencies
    pub fn generate_stubs(&self, fragment: &CodeFragment) -> Vec<String> {
        println!("\n🔧 [Phase 3] Generating library stubs...");
        
        let mut stubs = Vec::new();
        let mut missing_libs = HashSet::new();
        
        // Scan for library calls in all code
        let contracts_code: Vec<String> = fragment.contracts.iter().map(|c| c.source_code.clone()).collect();
        let orphan_code: Vec<String> = fragment.orphan_functions.iter().map(|f| f.source_code.clone()).collect();
        let test_code = fragment.test_contract.as_ref().map(|c| c.source_code.as_str()).unwrap_or("");
        
        let all_code = format!(
            "{}\n{}\n{}",
            contracts_code.join("\n"),
            orphan_code.join("\n"),
            test_code
        );
        
        // Simple pattern: LibName.function() - extract LibName
        let re = regex::Regex::new(r"\b([A-Z][a-zA-Z0-9_]+)\.([a-z][a-zA-Z0-9_]+)\(").unwrap();
        for cap in re.captures_iter(&all_code) {
            let lib_name = cap[1].to_string();
            
            // Check if it's already defined
            let is_defined = fragment.libraries.iter().any(|l| l.name == lib_name)
                || fragment.contracts.iter().any(|c| c.name == lib_name);
            
            if !is_defined {
                missing_libs.insert(lib_name);
            }
        }
        
        // Generate stubs
        for lib_name in missing_libs {
            let stub = format!(
                "library {} {{\n    /* Generated stub - replace with actual implementation */\n}}",
                lib_name
            );
            println!("   ✓ Generated stub for '{}'", lib_name);
            stubs.push(stub);
        }
        
        stubs
    }
    
    /// Phase 4: Assemble the final output
    pub fn assemble(&self, fragment: &CodeFragment, stubs: Vec<String>) -> String {
        println!("\n🔨 [Phase 4] Assembling final code...");
        
        let mut output = String::new();
        
        // 1. Preamble (Pragma & Imports)
        if !fragment.preamble.is_empty() {
            output.push_str(&fragment.preamble.join("\n"));
            output.push_str("\n\n");
        } else {
            // Add default pragma
            output.push_str("// SPDX-License-Identifier: MIT\n");
            output.push_str("pragma solidity ^0.8.0;\n\n");
        }
        
        // 2. Global Types & Structs
        if !fragment.global_types.is_empty() {
            output.push_str("// ========== GLOBAL TYPES ==========\n\n");
            output.push_str(&fragment.global_types.join("\n\n"));
            output.push_str("\n\n");
        }
        
        // 3. Libraries (Original + Stubs)
        if !fragment.libraries.is_empty() || !stubs.is_empty() {
            output.push_str("// ========== LIBRARIES ==========\n\n");
            for lib in &fragment.libraries {
                output.push_str(&lib.source_code);
                output.push_str("\n\n");
            }
            for stub in &stubs {
                output.push_str(stub);
                output.push_str("\n\n");
            }
        }
        
        // 4. Interfaces
        if !fragment.interfaces.is_empty() {
            output.push_str("// ========== INTERFACES ==========\n\n");
            for iface in &fragment.interfaces {
                output.push_str(&iface.source_code);
                output.push_str("\n\n");
            }
        }
        
        // 5. Contracts (with injected orphan functions)
        if !fragment.contracts.is_empty() {
            output.push_str("// ========== CONTRACTS ==========\n\n");
            for contract in &fragment.contracts {
                output.push_str(&contract.source_code);
                output.push_str("\n\n");
            }
        }
        
        // 6. Orphan variables (inject into first suitable contract or create holder)
        if !fragment.orphan_variables.is_empty() {
            output.push_str("// ========== ORPHAN VARIABLES ==========\n");
            output.push_str("// TODO: Manually assign to appropriate contract\n");
            for var in &fragment.orphan_variables {
                output.push_str(var);
                output.push_str("\n");
            }
            output.push_str("\n");
        }
        
        // 7. Test Contract
        if let Some(test) = &fragment.test_contract {
            output.push_str("// ========== TEST CONTRACT ==========\n\n");
            output.push_str(&test.source_code);
            output.push_str("\n");
        }
        
        println!("   ✓ Assembly complete ({} lines)", output.lines().count());
        
        output
    }
    
    /// Main pipeline: Parse -> Infer -> Stub -> Assemble
    pub fn resurrect(&self) -> Result<String> {
        println!("🚀 Starting SolResurrect pipeline...\n");
        
        let mut fragment = self.parse_slice()
            .context("Failed to parse code fragment")?;
        
        self.infer_context(&mut fragment)
            .context("Failed to infer context")?;
        
        let stubs = self.generate_stubs(&fragment);
        
        let output = self.assemble(&fragment, stubs);
        
        println!("\n✅ Resurrection complete!");
        
        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_resurrection() {
        let raw_code = r#"
        function computeNAV(address vault) external view returns (uint256) {
            return IERC20(token).balanceOf(vault);
        }
        
        contract PanopticVaultAccountant {
            address token;
        }
        "#.to_string();
        
        let resurrect = SolResurrect::new(raw_code);
        let result = resurrect.resurrect();
        
        assert!(result.is_ok());
        let output = result.unwrap();
        assert!(output.contains("computeNAV"));
        assert!(output.contains("PanopticVaultAccountant"));
    }
}
