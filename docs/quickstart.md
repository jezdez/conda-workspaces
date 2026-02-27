# Quick start

## Installation

::::{tab-set}

:::{tab-item} conda

```bash
conda install -c conda-forge conda-workspaces
```

:::

:::{tab-item} pixi

```bash
pixi global install conda-workspaces
```

:::

::::

## Your first workspace

Create a manifest in your project root:

::::{tab-set}

:::{tab-item} conda.toml

```toml
[workspace]
name = "my-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.10"
numpy = ">=1.24"

[feature.test.dependencies]
pytest = ">=8.0"
pytest-cov = ">=4.0"

[environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
```

:::

:::{tab-item} pixi.toml

```toml
[workspace]
name = "my-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.10"
numpy = ">=1.24"

[feature.test.dependencies]
pytest = ">=8.0"
pytest-cov = ">=4.0"

[environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
```

:::

:::{tab-item} pyproject.toml

```toml
[tool.conda.workspace]
name = "my-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[tool.conda.dependencies]
python = ">=3.10"
numpy = ">=1.24"

[tool.conda.feature.test.dependencies]
pytest = ">=8.0"
pytest-cov = ">=4.0"

[tool.conda.environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
```

:::

::::

Or use the init command to scaffold one:

```bash
cw init
# or: cw init --format conda
# or: cw init --format pyproject
```

## Install environments

```bash
cw install
```

This creates project-local conda environments under `.conda/envs/` for
each environment defined in your manifest. A `conda.lock` file is
generated automatically after solving.

## Reproducible installs

To install from the lockfile without re-solving:

```bash
cw install --locked
```

This uses the exact package URLs recorded in `conda.lock`, ensuring
identical environments across machines and CI.

## Run commands

```bash
cw run -e test -- pytest -v
```

## List environments

```bash
cw list
```

## View environment details

```bash
cw info test
```

## Next steps

- Read about [features](features.md) to learn how environments compose
- See the [configuration](configuration.md) reference for all manifest options
- Check out the [tutorials](tutorials/index.md) for more in-depth guides
