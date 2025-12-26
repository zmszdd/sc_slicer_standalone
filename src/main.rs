mod analyzer;

use clap::{Arg, Command};
use std::fs;
use std::process;

fn main() {
    let matches = Command::new("SC_Slicer")
        .version("0.1.0")
        .author("SC_Slicer Team")
        .about("Solidity code slicing analysis tool based on Program Dependency Graph (PDG)")
        .arg(
            Arg::new("contract_file")
                .help("Path to the Solidity contract file")
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

    let file_path = matches.get_one::<String>("contract_file").unwrap();
    let contract_name = matches.get_one::<String>("contract_name").unwrap();
    let variable_name = matches.get_one::<String>("variable_name").unwrap();
    let function_name_str = matches.get_one::<String>("function_name");
    let function_name = function_name_str.map(|s| s.as_str()).unwrap_or("");
    let slice_level = matches.get_one::<String>("slice_level").unwrap();
    let output_file = matches.get_one::<String>("output");

    let slice = match slice_level.as_str() {
        "line" => {
            match analyzer::analyze_contract_and_get_line_slice(file_path, contract_name, function_name, variable_name) {
                Ok(slice) => slice,
                Err(e) => {
                    eprintln!("❌ Error: {}", e);
                    process::exit(1);
                }
            }
        }
        "function" | _ => {
            match analyzer::analyze_contract_and_get_slice(file_path, contract_name, function_name, variable_name) {
                Ok(slice) => slice,
                Err(e) => {
                    eprintln!("❌ Error: {}", e);
                    process::exit(1);
                }
            }
        }
    };

    if let Some(output_file) = output_file {
        fs::write(output_file, slice.join("\n")).expect("Failed to write to file");
        println!("✅ Results written to {}", output_file);
    } else {
        println!("🔍 Source Code Slice Analysis");
        println!("📁 File: {}", file_path);
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
}