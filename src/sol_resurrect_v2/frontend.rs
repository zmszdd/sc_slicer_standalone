use std::path::PathBuf;

use anyhow::Result;

use super::source_db::SourceDatabase;

pub struct SourceFrontend;

impl SourceFrontend {
    pub fn parse_files(files: &[PathBuf]) -> Result<SourceDatabase> {
        SourceDatabase::build(files)
    }
}
