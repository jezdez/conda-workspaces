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

## Your first tasks

![task quickstart demo](../demos/task-quickstart.gif)

Create a `conda.toml` in your project root:

```toml
[tasks]
hello = "echo 'Hello from conda-workspaces!'"
test = { cmd = "pytest tests/ -v", depends-on = ["build"] }
build = "python -m build"
```

Run a task:

```bash
conda task run hello
conda task run test    # runs build first, then test
conda task list        # see all tasks
```

Tasks run in your current conda environment. No workspace definition is
required — you can start with tasks alone and add workspace features later.

## Your first workspace

![quickstart demo](../demos/quickstart.gif)

Add workspace configuration to the same `conda.toml`:

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
default = []
test = { features = ["test"] }
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
default = []
test = { features = ["test"] }
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
default = []
test = { features = ["test"] }
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

You can point to a specific manifest with `--file` / `-f`:

```bash
cw install -f path/to/conda.toml
```

To recreate environments from scratch, use `--force-reinstall`:

```bash
cw install --force-reinstall
```

## Lock

![lockfile demo](../demos/lockfile.gif)

The `cw lock` command runs the solver and records the solution in
`conda.lock` without installing any environments:

```bash
cw lock
```

## Reproducible installs

Use `--locked` to install from the lockfile. This validates that the
lockfile is still fresh relative to the manifest — if the manifest has
changed, the install fails:

```bash
cw install --locked
```

Use `--frozen` to install from the lockfile as-is, without checking
freshness:

```bash
cw install --frozen
```

## Run tasks in workspace environments

Once your workspace is installed, run tasks in specific environments:

```bash
conda task run -e test pytest -v
```

Or spawn an interactive shell:

```bash
cw shell -e test
```

You can also pass a one-shot command to `cw shell`:

```bash
cw shell -e test -- python -c "import numpy; print(numpy.__version__)"
```

## Add dependencies

```bash
cw add numpy
```

Add to a specific feature:

```bash
cw add --feature test pytest
```

Add a PyPI dependency:

```bash
cw add --pypi requests
```

## List packages and environments

```bash
cw list              # packages in default env
cw list -e test      # packages in test env
cw envs              # list defined environments
```

## Workspace overview

```bash
cw info
cw info -e test      # details for a specific environment
```

## Next steps

- Read about [features](features.md) to learn how environments and tasks work
- See the [configuration](configuration.md) reference for all manifest options
- Check out the [tutorials](tutorials/index.md) for more in-depth guides
