# Coming from pixi

![pixi compatibility demo](../../demos/pixi-compat.gif)

If you already use pixi for workspace management and tasks,
conda-workspaces can read the same manifest files. This guide explains
how the two tools relate and how to use them side by side.

## Key differences

| Aspect | pixi | conda-workspaces |
|---|---|---|
| Solver | rattler (bundled) | conda / libmamba |
| Environment location | `.pixi/envs/` | `.conda/envs/` |
| Lock file | `pixi.lock` | `conda.lock` |
| Task runner | Built-in | Built-in (`conda task`) |
| Template engine | MiniJinja (Rust) | Jinja2 (Python) |
| Shell | `deno_task_shell` | Native platform shell |
| Package builds | pixi-build (rattler-build) | conda-build (separate) |
| CLI | `pixi` | `cw` / `ct` / `conda workspace` / `conda task` |

## Using both tools

Since pixi stores environments in `.pixi/envs/` and conda-workspaces
uses `.conda/envs/`, both tools can coexist on the same project:

```bash
# pixi users
pixi install
pixi run test

# conda users
cw install
conda task run test
```

Both read the same `pixi.toml` manifest — workspace definitions and
task definitions alike.

## Command mapping

| pixi | conda-workspaces |
|---|---|
| `pixi init` | `cw init` |
| `pixi install` | `cw install` |
| `pixi install --locked` | `cw install --locked` (validates lockfile freshness) |
| `pixi install --frozen` | `cw install --frozen` (installs from lockfile as-is) |
| `pixi add python` | `cw add python` |
| `pixi add --feature test pytest` | `cw add -e test pytest` or `cw add --feature test pytest` |
| `pixi add --pypi requests` | `cw add --pypi requests` |
| `pixi remove numpy` | `cw remove numpy` |
| `pixi run <task>` | `conda task run <task>` or `ct run <task>` |
| `pixi run CMD` | `cw shell -- CMD` (runs in project env) |
| `pixi list` | `cw list` (packages in default env) |
| `pixi list` (envs) | `cw envs` |
| `pixi list` (specific env) | `cw list -e <env>` |
| `pixi info` | `cw info` (workspace overview) |
| `pixi info` (per-env) | `cw info -e <env>` |
| `pixi lock` | `cw lock` (pure solve, no install required) |
| `pixi shell` | `cw shell` or `cw shell -e <env>` |
| `pixi clean` | `cw clean` |
| `pixi task list` | `conda task list` or `ct list` |

## Template compatibility

pixi uses MiniJinja (Rust) and conda-workspaces uses Jinja2 (Python).
The template syntax is identical for all practical purposes:

- `{{ pixi.platform }}` works in conda-workspaces when reading from
  `pixi.toml`
- `{{ conda.platform }}` is available everywhere
- Jinja2 supports a few extra filters not present in MiniJinja, but you
  are unlikely to hit any incompatibilities going the other direction

## Shell differences

pixi uses `deno_task_shell`, a cross-platform shell that understands
commands like `rm` on Windows. conda-workspaces uses the native platform
shell (`sh` on Unix, `cmd` on Windows).

For cross-platform compatibility, use platform overrides:

```toml
[tasks]
clean = "rm -rf build/"

[target.win-64.tasks]
clean = "rd /s /q build"
```

Or use Jinja2 conditionals:

```toml
[tasks]
clean = "{% if conda.is_win %}rd /s /q build{% else %}rm -rf build/{% endif %}"
```

## Using conda.toml instead

If your team uses only conda, you can use `conda.toml` instead of
`pixi.toml`. The format is structurally identical:

```bash
cw init --format conda
```

This creates a `conda.toml` file with the same workspace/feature/
environment/task structure. The only difference is:

- `conda.toml` uses `[workspace]` exclusively (no `[project]` fallback)
- `conda.toml` is searched first, before `pixi.toml` and `pyproject.toml`

## Embedded in pyproject.toml

You can also embed workspace and task configuration in `pyproject.toml`:

```toml
# Preferred: under [tool.conda.*]
[tool.conda.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64"]

[tool.conda.dependencies]
python = ">=3.10"

[tool.conda.tasks]
test = "pytest tests/ -v"

# Also supported: [tool.pixi.*]
# (same format pixi uses)
```

## Exporting pixi tasks

If you want to convert pixi task definitions to `conda.toml` format,
use the built-in export command:

```bash
conda task export --file pixi.toml -o conda.toml
```

This reads your existing `pixi.toml` tasks (including platform overrides)
and writes a fully equivalent `conda.toml`.

## What's not supported

Some pixi-only concepts don't apply to conda-workspaces:

- `[package]` / pixi-build — use conda-build instead
- `[host-dependencies]` / `[build-dependencies]` — part of pixi-build
- `deno_task_shell` — conda-workspaces uses native platform shells
- `solve-group` — accepted for compatibility but has no effect (conda's
  solver operates on a single environment at a time)

See [DESIGN.md](https://github.com/conda-incubator/conda-workspaces/blob/main/DESIGN.md)
for the full compatibility mapping.
