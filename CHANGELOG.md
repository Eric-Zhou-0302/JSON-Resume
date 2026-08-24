# Changelog

All notable changes to JSON-Resume are recorded in this file.

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
