use clap::{Arg, Command};
use std::fs;
use std::process;
use std::path::Path;

mod analyzer;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let matches = Command::new("SC_Slicer")
        .version("0.1.0")
        .author("SC_Slicer Team")
        .about("Solidity code slicing analysis tool based on Program Dependency Graph (PDG)")
        .arg(
            Arg::new("input")
                .help("Path to the Solidity contract file or directory containing .sol files")
                .required(true)
                .index(1),
        )
        .arg(
            Arg::new("contract_name")
                .help("Name of the contract to analyze")
                .required(true)
                .index(2),
        )
        .arg(
            Arg::new("variable_name")
                .help("Name of the variable to slice")
                .required(true)
                .index(3),
        )
        .arg(
            Arg::new("function_name")
                .help("Optional: Name of the function (for targeted analysis)")
                .index(4),
        )
        .arg(
            Arg::new("slice_level")
                .help("Slice level: 'function' (default) or 'line'")
                .long("level")
                .short('l')
                .value_parser(["function", "line"])
                .default_value("function"),
        )
        .arg(
            Arg::new("output")
                .help("Output file path (suppresses console output)")
                .long("output")
                .short('o')
                .value_name("FILE"),
        )
        .get_matches();

    let input_path = matches.get_one::<String>("input").unwrap();
    let contract_name = matches.get_one::<String>("contract_name").unwrap();
    let variable_name = matches.get_one::<String>("variable_name").unwrap();
    let function_name_str = matches.get_one::<String>("function_name");
    let function_name = function_name_str.map(|s| s.as_str()).unwrap_or("");
    let slice_level = matches.get_one::<String>("slice_level").unwrap();
    let output_file = matches.get_one::<String>("output");

    // Collect all .sol files
    let file_paths = collect_sol_files(input_path)?;

    if file_paths.is_empty() {
        eprintln!("❌ No .sol files found in {}", input_path);
        return Err("No .sol files found".into());
    }

    let slice = match slice_level.as_str() {
        "line" => {
            match analyzer::analyze_contracts_and_get_line_slice(&file_paths, contract_name, function_name, variable_name) {
                Ok(slice) => slice,
                Err(e) => {
                    eprintln!("❌ Error: {}", e);
                    return Err(e.into());
                }
            }
        }
        "function" | _ => {
            match analyzer::analyze_contracts_and_get_slice(&file_paths, contract_name, function_name, variable_name) {
                Ok(slice) => slice,
                Err(e) => {
                    eprintln!("❌ Error: {}", e);
                    return Err(e.into());
                }
            }
        }
    };

    if let Some(output_file) = output_file {
        fs::write(output_file, slice.join("\n")).expect("Failed to write to file");
        println!("✅ Results written to {}", output_file);
    } else {
        println!("🔍 Source Code Slice Analysis");
        println!("📁 Input: {}", input_path);
        println!("🏢 Contract: {}", contract_name);
        println!("⚡ Function: {}", if function_name.is_empty() { "All functions" } else { function_name });
        println!("📊 Variable: {}", variable_name);
        println!("🎯 Slice Level: {}", slice_level);
        println!("📋 Slice Results ({} lines):", slice.len());
        println!("{}", "=".repeat(60));

        for line in slice {
            println!("{}", line);
        }

        println!("{}", "=".repeat(60));
        println!("✅ Analysis completed successfully!");
    }
    Ok(())
}

fn collect_sol_files(input_path: &str) -> Result<Vec<String>, String> {
    let path = Path::new(input_path);
    let mut files = Vec::new();

    if path.is_file() {
        if path.extension().and_then(|s| s.to_str()) == Some("sol") {
            files.push(input_path.to_string());
        }
    } else if path.is_dir() {
        collect_sol_files_recursive(path, &mut files)?;
    } else {
        return Err(format!("Path {} is neither a file nor a directory", input_path));
    }

    Ok(files)
}

fn collect_sol_files_recursive(dir: &Path, files: &mut Vec<String>) -> Result<(), String> {
    for entry in fs::read_dir(dir).map_err(|e| format!("Failed to read directory: {}", e))? {
        let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let path = entry.path();

        if path.is_file() {
            if path.extension().and_then(|s| s.to_str()) == Some("sol") {
                files.push(path.to_string_lossy().to_string());
            }
        } else if path.is_dir() {
            // Skip common non-source directories
            if !path.ends_with("node_modules") && !path.ends_with(".git") && !path.ends_with("target") {
                collect_sol_files_recursive(&path, files)?;
            }
        }
    }

    Ok(())
}