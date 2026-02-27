# Features

## Environments

Environments are named conda prefixes composed from one or more features.
Each environment is installed under `.conda/envs/<name>/` in your project.

```toml
[environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
docs = { features = ["docs"] }
```

The `default` environment always exists and includes the top-level
`[dependencies]`. Named environments inherit the default feature unless
`no-default-feature = true` is set.

## Features

Features are composable groups of dependencies, channels, and settings.
They map to `[feature.<name>]` tables in the manifest:

```toml
[feature.test.dependencies]
pytest = ">=8.0"
pytest-cov = ">=4.0"

[feature.docs.dependencies]
sphinx = ">=7.0"
myst-parser = ">=3.0"
```

When an environment includes multiple features, dependencies are merged
in order. Later features override earlier ones for the same package name.

## Channels

Channels are specified at the workspace level and can be overridden per
feature:

```toml
[workspace]
channels = ["conda-forge"]

[feature.special.dependencies]
some-pkg = "*"

[feature.special]
channels = ["conda-forge", "bioconda"]
```

Feature channels are appended after workspace channels, with duplicates
removed.

## Platform targeting

Per-platform dependency overrides use `[target.<platform>]` tables:

```toml
[dependencies]
python = ">=3.10"

[target.linux-64.dependencies]
linux-headers = ">=5.10"

[target.osx-arm64.dependencies]
llvm-openmp = ">=14.0"
```

Platform overrides are merged on top of the base dependencies when
resolving for a specific platform.

## Solve-groups

Solve-groups coordinate dependency versions across related environments.
Environments in the same group are solved together to ensure consistent
package versions:

```toml
[environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
docs = { features = ["docs"] }
```

Here, `default` and `test` share the `"default"` solve-group, so they
will have identical versions for shared packages. The `docs` environment
is solved independently.

## PyPI dependencies

PyPI dependencies are specified separately from conda dependencies:

```toml
[pypi-dependencies]
my-local-pkg = { path = ".", editable = true }
some-pypi-only = ">=1.0"

[feature.test.pypi-dependencies]
pytest-benchmark = ">=4.0"
```

PyPI dependencies are parsed and stored in the model. Installation
requires [conda-pypi](https://github.com/conda-incubator/conda-pypi)
to be available.

## No-default-feature

An environment can opt out of inheriting the default feature:

```toml
[environments]
minimal = { features = ["minimal"], no-default-feature = true }
```

This is useful for environments that need a completely independent
dependency set.

## Activation

Features can specify activation scripts and environment variables:

```toml
[activation]
scripts = ["scripts/activate.sh"]
env = { MY_VAR = "value" }

[feature.dev.activation]
env = { DEBUG = "1" }
```

Activation settings are merged across features when composing an
environment.

## System requirements

System requirements declare minimum system-level dependencies:

```toml
[system-requirements]
cuda = "12"
glibc = "2.17"
```

These are stored and validated during environment installation.

## Lock

After installing environments, conda-workspaces generates a `conda.lock`
file at the project root. This lockfile records the exact packages
installed in each environment using the
[rattler-lock v6](https://github.com/conda/rattler/blob/main/crates/rattler_lock/src/parse/v6.rs)
format (the same format pixi uses for `pixi.lock`).

```bash
# Generate or update the lockfile
cw lock

# Install from lockfile (skip solving)
cw install --locked
```

The lockfile contains all environments and their resolved packages:

```yaml
version: 6
environments:
  default:
    channels:
      - url: https://conda.anaconda.org/conda-forge/
    packages:
      linux-64:
        - conda: https://conda.anaconda.org/conda-forge/linux-64/python-3.12.0-...
  test:
    channels:
      - url: https://conda.anaconda.org/conda-forge/
    packages:
      linux-64:
        - conda: https://conda.anaconda.org/conda-forge/linux-64/python-3.12.0-...
        - conda: https://conda.anaconda.org/conda-forge/linux-64/pytest-8.0.0-...
packages:
  - conda: https://conda.anaconda.org/conda-forge/linux-64/python-3.12.0-...
    sha256: abc123...
    depends:
      - libffi >=3.4
    # ...
```

Using `--locked` skips the solver entirely and installs the exact package
URLs recorded in the lockfile, ensuring reproducible environments across
machines and CI.

## Project-local environments

All environments are installed under `.conda/envs/` in your project
directory, keeping them isolated from global conda environments:

```
my-project/
├── conda.toml
├── conda.lock
├── .conda/
│   └── envs/
│       ├── default/
│       ├── test/
│       └── docs/
└── src/
```

Environments are standard conda prefixes and work with `conda activate`.
