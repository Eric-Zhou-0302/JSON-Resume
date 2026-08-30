# Changelog

All notable changes to JSON-Resume are recorded in this file.

## [1.1.0] - 2026-08-30

### Added

- Installable `json-resume` Python package metadata with the matching console command.
- A tag-gated PyPI Trusted Publishing workflow with no long-lived API token.
- `render_json_to_docx(data)` as the stable in-memory DOCX API for HTTP services.
- `render_json_file_to_docx(...)` as the stable file-generating API for Python scripts, with `pdf` and `force` options.
- A single runtime dependency set for DOCX and PDF support.
- Package metadata and service-level regression tests.

### Changed

- Resume JSON must now contain at least one nonempty section.
- Entries may omit `bullets` when they contain other visible metadata such as a title, position, location, or date.
- Contacts with a nonempty `href` render as black, single-underlined external hyperlinks.
- The default CLI output location is now `output/` under the current working directory.

### Removed

- The unused `--quiet` and `--no-banner` CLI options.

### Verified

- In-memory output is a complete DOCX package and preserves caller input.
- Validation failures retain the existing precise `FieldError` path.
- Distribution metadata and runtime versions remain synchronized.
- The built wheel installs in an isolated environment and its `json-resume` command generates a DOCX successfully.

## [1.0.0] - 2026-08-24

### Added

- Strict JSON-to-DOCX resume generation with locale-based A4 and Letter paper sizes.
- Stable DOCX styles, fixed 60/40 entry tables, explicit hyperlink targets, and real Word bullet numbering.
- Optional PDF export and a standalone PDF page-count command.
- Chinese and English examples, user documentation, developer architecture documentation, and an Agent Skill.
- A `--version` CLI option for identifying the installed release.

### Verified

- Full unit-test suite for validation, rendering, CLI behavior, PDF utilities, output protection, and error exit codes.
- One-page A4 Chinese and Letter English example PDFs reviewed for layout integrity.
