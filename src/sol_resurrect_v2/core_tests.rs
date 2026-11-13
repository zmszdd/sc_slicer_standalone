use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use super::closure::ClosureEngine;
use super::fallback::{FallbackController, FallbackLevel};
use super::renderer::SourceBackedRenderer;
use super::slice_graph::SliceGraph;
use super::source_db::SourceDatabase;
use super::{run_resurrection_v2, ResurrectionV2Request};

const CORE_FIXTURE: &str = r#"// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Vault {
    uint256 public totalAssets;

    event Deposited(uint256 amount);

    function deposit(uint256 amount) external {
        totalAssets += amount;
        emit Deposited(amount);
    }

    function unrelated() external pure returns (uint256) {
        return 42;
    }
}

contract Unrelated {
    function helper() external pure returns (uint256) {
        return 1;
    }
}
"#;

const PIPELINE_FIXTURE: &str = r#"// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Vault {
    uint256 public totalAssets;

    function deposit(uint256 amount) external {
        totalAssets += amount;
    }

    function test_deposit() external {
        deposit(100);
        assert(totalAssets == 100);
    }
}
"#;

struct TempSolidity {
    dir: PathBuf,
}

impl TempSolidity {
    fn new(content: &str) -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock before epoch")
            .as_nanos();
        let dir = std::env::temp_dir().join(format!(
            "sc_slicer_core_tests_{}_{}",
            std::process::id(),
            nonce
        ));
        fs::create_dir_all(&dir).expect("create temp dir");
        fs::write(dir.join("input.sol"), content).expect("write fixture");
        Self { dir }
    }

    fn path(&self) -> PathBuf {
        self.dir.join("input.sol")
    }
}

impl Drop for TempSolidity {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.dir);
    }
}

fn build_db(content: &str) -> (TempSolidity, SourceDatabase) {
    let fixture = TempSolidity::new(content);
    let db = SourceDatabase::build(std::slice::from_ref(&fixture.path()))
        .expect("SourceDatabase should build from fixture");
    (fixture, db)
}

fn render_initial_slice(content: &str, contract: &str, function: &str, focus: &str) -> String {
    let (_fixture, db) = build_db(content);
    let mut graph = SliceGraph::seed(
        contract.to_string(),
        function.to_string(),
        focus.to_string(),
    );
    ClosureEngine::new(&db).apply_initial_closure(&mut graph);
    SourceBackedRenderer::new(&db)
        .render(&graph)
        .expect("render should succeed")
}

fn forge_available() -> bool {
    std::process::Command::new("forge")
        .arg("--version")
        .output()
        .is_ok()
}

#[test]
fn source_database_indexes_functions_state_and_focus_providers() {
    let (_fixture, db) = build_db(CORE_FIXTURE);

    assert!(db.resolve_container("Vault").is_some());
    assert!(db.resolve_function("Vault", "deposit").is_some());
    assert!(db.resolve_function("Vault", "unrelated").is_some());
    assert!(db.resolve_function("Unrelated", "helper").is_some());

    let deposit = db.resolve_function("Vault", "deposit").expect("deposit");
    let statements = db.function_statements(deposit);
    assert!(
        statements
            .iter()
            .any(|(_, text)| text.contains("totalAssets")),
        "deposit statements should include totalAssets update: {statements:?}"
    );

    assert!(
        !db.providers_for_symbol("totalAssets").is_empty(),
        "totalAssets should have indexed providers"
    );
}

#[test]
fn minimal_slice_keeps_target_focus_and_drops_unrelated_contract() {
    let output = render_initial_slice(CORE_FIXTURE, "Vault", "deposit", "totalAssets");

    assert!(output.contains("contract Vault"), "{output}");
    assert!(output.contains("totalAssets"), "{output}");
    assert!(output.contains("deposit"), "{output}");
    assert!(!output.contains("unrelated"), "{output}");
    assert!(!output.contains("contract Unrelated"), "{output}");
}

#[test]
fn statement_closure_includes_defining_statement_for_focus_expression() {
    let fixture = r#"pragma solidity ^0.8.13;

contract Vault {
    uint256 public totalAssets;

    function deposit(uint256 amount) external {
        uint256 fee = amount / 100;
        totalAssets += fee;
    }
}
"#;
    let output = render_initial_slice(fixture, "Vault", "deposit", "totalAssets");

    assert!(output.contains("uint256 fee = amount / 100;"), "{output}");
    assert!(output.contains("totalAssets += fee;"), "{output}");
}

#[test]
fn full_source_unit_fallback_renders_complete_input() {
    let (_fixture, db) = build_db(CORE_FIXTURE);
    let mut graph = SliceGraph::seed(
        "Vault".to_string(),
        "deposit".to_string(),
        "totalAssets".to_string(),
    );
    graph.set_fallback_level(FallbackLevel::FullSourceUnit);

    let output = SourceBackedRenderer::new(&db)
        .render(&graph)
        .expect("full source render should succeed");

    assert!(output.contains("contract Vault"), "{output}");
    assert!(output.contains("contract Unrelated"), "{output}");
    assert!(output.contains("unrelated"), "{output}");
}

#[test]
fn fallback_widen_without_compile_guarantee_stops_before_libraries() {
    let mut graph = SliceGraph::seed(
        "Vault".to_string(),
        "deposit".to_string(),
        "totalAssets".to_string(),
    );
    let mut fallback = FallbackController::new(false);

    while fallback.widen(&mut graph) {}

    assert_eq!(fallback.level(), FallbackLevel::FullDependencyFunctions);
    assert_eq!(
        graph.fallback_level(),
        FallbackLevel::FullDependencyFunctions
    );
}

#[test]
fn fallback_widen_with_compile_guarantee_reaches_required_libraries() {
    let mut graph = SliceGraph::seed(
        "Vault".to_string(),
        "deposit".to_string(),
        "totalAssets".to_string(),
    );
    let mut fallback = FallbackController::new(true);

    while fallback.widen(&mut graph) {}

    assert_eq!(
        fallback.level(),
        FallbackLevel::FullRequiredLibrariesInterfaces
    );
}

#[test]
fn renderer_output_is_deterministic_across_independent_databases() {
    let first = render_initial_slice(CORE_FIXTURE, "Vault", "deposit", "totalAssets");
    let second = render_initial_slice(CORE_FIXTURE, "Vault", "deposit", "totalAssets");

    assert!(!first.is_empty(), "rendered slice must not be empty");
    assert_eq!(
        first, second,
        "renderer output must be byte-identical across independent SourceDatabase builds"
    );
}

#[tokio::test]
async fn full_pipeline_is_deterministic_when_forge_available() {
    if !forge_available() {
        eprintln!(
            "skipping full_pipeline_is_deterministic_when_forge_available: forge unavailable"
        );
        return;
    }

    let fixture = TempSolidity::new(PIPELINE_FIXTURE);
    let output_dir = fixture.dir.join("out");
    fs::create_dir_all(&output_dir).expect("create output dir");

    let build_request = |output_name: &str| ResurrectionV2Request {
        input_files: vec![fixture.path()],
        project_root: fixture.dir.clone(),
        seed_slice: String::new(),
        target_contract: "Vault".to_string(),
        target_test: "test_deposit".to_string(),
        focus_symbol: "totalAssets".to_string(),
        output_path: output_dir.join(output_name),
        compile_guarantee: true,
    };

    let first = run_resurrection_v2(build_request("first.sol"))
        .await
        .expect("first pipeline run should complete");
    let second = run_resurrection_v2(build_request("second.sol"))
        .await
        .expect("second pipeline run should complete");

    assert!(first.code.contains("contract Vault"), "{}", first.code);
    assert_eq!(
        first.code, second.code,
        "full pipeline output must be byte-identical across runs"
    );
}
