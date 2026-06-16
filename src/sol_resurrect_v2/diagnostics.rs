use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct ResurrectionDiagnostic {
    pub kind: String,
    pub message: String,
}
