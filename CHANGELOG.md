# Changelog

All notable changes to conda-workspaces will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/).

## Unreleased

## 0.1.1 — 2026-03-05

### Changed

- Transferred repository to conda-incubator organization
- Added PyPI release workflow with trusted publishing
- Moved changelog to repository root

## 0.1.0 — 2026-03-05

### Added

- Initial implementation of conda-workspaces plugin
- `conda workspace` subcommand with `init`, `install`, `list`, `info`,
  `add`, `remove`, `clean`, `run`, and `activate` subcommands
- `cw` standalone CLI shortcut
- Parser support for `pixi.toml`, `conda.toml`, and `pyproject.toml`
  manifests
- Multi-environment workspace model with composable features
- Solve-group support for version coordination across environments
- Per-platform dependency overrides via `[target.<platform>]`
- PyPI dependency parsing (requires conda-pypi for installation)
- Project-local environments under `.conda/envs/`
- Sphinx documentation with conda-sphinx-theme
- PyPI release workflow with trusted publishing
