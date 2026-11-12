use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

static LOG_PATH: OnceLock<PathBuf> = OnceLock::new();

pub fn unix_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

pub fn init(path: PathBuf, args: &[String]) -> std::io::Result<PathBuf> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let initialized = LOG_PATH.set(path.clone()).is_ok();
    if initialized {
        let mut file = OpenOptions::new().create(true).append(true).open(&path)?;
        writeln!(file, "{}", "=".repeat(96))?;
        writeln!(file, "[{}] SC_Slicer execution started", unix_timestamp())?;
        writeln!(file, "argv: {}", redact_args(args).join(" "))?;
    }

    Ok(path)
}

fn redact_args(args: &[String]) -> Vec<String> {
    let mut redacted = Vec::with_capacity(args.len());
    let mut redact_next = false;
    for arg in args {
        if redact_next {
            redacted.push("<redacted>".to_string());
            redact_next = false;
            continue;
        }

        if arg == "--api-key" {
            redacted.push(arg.clone());
            redact_next = true;
            continue;
        }

        if let Some((key, _)) = arg.split_once('=') {
            if key == "--api-key" || key.ends_with("API_KEY") {
                redacted.push(format!("{}=<redacted>", key));
                continue;
            }
        }

        redacted.push(arg.clone());
    }
    redacted
}

pub fn log_line(message: impl AsRef<str>) {
    let Some(path) = LOG_PATH.get() else {
        return;
    };
    let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) else {
        return;
    };
    let _ = writeln!(file, "[{}] {}", unix_timestamp(), message.as_ref());
}

pub fn phase_start(name: &str) {
    log_line(format!(">>> phase_start name={}", name));
}

pub fn phase_end(name: &str, summary: impl AsRef<str>) {
    log_line(format!("<<< phase_end name={} {}", name, summary.as_ref()));
}

pub fn detail(name: &str, value: impl AsRef<str>) {
    log_line(format!("detail {} {}", name, value.as_ref()));
}

pub fn sample<I, S>(name: &str, values: I, limit: usize)
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let mut values = values
        .into_iter()
        .map(|value| value.as_ref().to_string())
        .collect::<Vec<_>>();
    values.sort();
    let total = values.len();
    let shown = values.into_iter().take(limit).collect::<Vec<_>>();
    log_line(format!(
        "sample {} total={} shown={} values=[{}]",
        name,
        total,
        shown.len(),
        shown.join(", ")
    ));
}
