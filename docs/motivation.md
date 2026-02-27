# Motivation

## Why conda-workspaces?

Conda is a powerful package and environment manager, but it has lacked
project-scoped multi-environment workspace management. Projects that need
separate environments for testing, documentation, and development typically
manage them manually with `environment.yml` files and shell scripts.

[pixi](https://pixi.sh) introduced an excellent workspace model that
integrates multi-environment management with project configuration.
conda-workspaces brings that same capability to conda as a plugin, so
existing conda users can define workspaces without switching tools.

## Workspaces, not environments

conda-workspaces adds workspace-level orchestration on top of conda's
existing environment management. It does not replace conda's solver,
channels, or installation machinery.

In pixi, a single `pixi.toml` manages both the workspace definition and
the installation. Running `pixi install` uses rattler (a Rust-based solver)
to resolve and install packages into `.pixi/envs/`. conda-workspaces
separates these concerns:

| Responsibility | In pixi | In conda + conda-workspaces |
|---|---|---|
| Define workspace & envs | `pixi.toml` | `conda.toml`, `pixi.toml`, or `pyproject.toml` |
| Solve dependencies | rattler (bundled) | conda / libmamba (existing) |
| Install packages | rattler (into `.pixi/envs/`) | conda (into `.conda/envs/`) |
| Manage environments | `pixi install` | `cw install` (delegates to conda) |
| Run commands | `pixi run` | `cw run` |
| Activate | `pixi shell` | `conda activate .conda/envs/<name>` |

This approach has advantages:

- Uses conda's mature solver and package cache
- Environments are standard conda prefixes (compatible with all conda tooling)
- No additional resolver or package installation system to maintain
- Works with existing conda channels, mirrors, and authentication
- Incremental adoption without changing your existing conda workflow

## Compatibility with pixi

conda-workspaces reads the same manifest format as pixi. A project with a
`pixi.toml` can use both tools:

- pixi users run `pixi install` and `pixi run` as usual
- conda users run `cw install` and `cw run` using conda's solver

This coexistence is possible because each tool stores environments in a
different directory (`.pixi/envs/` vs `.conda/envs/`), so they don't
interfere with each other.

See [DESIGN.md](https://github.com/conda-incubator/conda-workspaces/blob/main/DESIGN.md)
for the full compatibility mapping.

## Comparison to other tools

| Tool | Scope | Solver | Environments | Lock files | Multi-env |
|---|---|---|---|---|---|
| conda-workspaces | Workspace orchestration | conda / libmamba | Project-local (`.conda/envs/`) | Yes (`conda.lock`) | Yes |
| pixi | Full project management | rattler (bundled) | Project-local (`.pixi/envs/`) | Yes | Yes |
| conda-project | Project management | conda (via conda-lock) | Project-local (`./envs/`) | Yes | Yes |
| anaconda-project | Project management | conda | Project-local (`./envs/`) | Yes | Yes |
| conda-devenv | Environment templating | conda / mamba | Global named | Yes | Via includes |
| conda-lock | Lock file generation | conda | N/A (lock files only) | Yes | N/A |
| `environment.yml` | Single environment spec | conda | Global or named | No | No |
| tox / nox | Test matrix | pip | Virtualenvs | No | Yes |

### Prior art

conda-workspaces builds on ideas from several earlier tools.

[anaconda-project](https://github.com/anaconda/anaconda-project) was the
first tool to add project-scoped conda environments, command runners, and
secrets management via an `anaconda-project.yml` manifest. It supports
multiple named environment specs and lock files. However, development has
slowed and the manifest format is not shared with any other tool.

[conda-project](https://github.com/conda-incubator/conda-project) is the
spiritual successor to anaconda-project. It uses `conda-project.yml` for
multi-environment management and generates lock files via conda-lock.
conda-project remains in alpha and uses its own manifest format.

[conda-devenv](https://github.com/ESSS/conda-devenv) takes a different
approach: it extends `environment.yml` with Jinja2 templating, file
includes, and environment variable definitions. It is well suited for
composing a single environment from multiple projects, but does not
support multiple independent environments per project.

conda-workspaces differs from all of the above in two ways:

1. It uses pixi's TOML-based manifest format rather than inventing a new
   one. Projects can share a single `pixi.toml` or `pyproject.toml`
   between pixi and conda-workspaces.
2. It integrates as a conda plugin (`conda workspace`) rather than
   shipping a standalone CLI. Environments are standard conda prefixes
   that work with `conda activate` and all existing conda tooling.
