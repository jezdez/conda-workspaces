# conda-workspaces

Project-scoped multi-environment workspace management for conda, with pixi
manifest compatibility.

```bash
cw install              # create all workspace environments
cw run -e test -- pytest  # run a command in an environment
cw list                 # show defined environments
```

```toml
# conda.toml
[workspace]
name = "my-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.10"
numpy = ">=1.24"

[feature.test.dependencies]
pytest = ">=8.0"

[environments]
default = { solve-group = "default" }
test = { features = ["test"], solve-group = "default" }
```

---

::::{grid} 2
:gutter: 3

:::{grid-item-card} {octicon}`rocket` Getting started
:link: quickstart
:link-type: doc

Install conda-workspaces and set up your first workspace in under a minute.
:::

:::{grid-item-card} {octicon}`mortar-board` Tutorials
:link: tutorials/index
:link-type: doc

Step-by-step guides: your first workspace, migrating from pixi, CI setup.
:::

:::{grid-item-card} {octicon}`list-unordered` Features
:link: features
:link-type: doc

Environments, features, solve-groups, platform overrides, PyPI dependencies,
and more.
:::

:::{grid-item-card} {octicon}`gear` Configuration
:link: configuration
:link-type: doc

All manifest fields and file formats (`conda.toml`, `pixi.toml`,
`pyproject.toml`).
:::

:::{grid-item-card} {octicon}`terminal` CLI reference
:link: reference/cli
:link-type: doc

Complete `conda workspace` command-line documentation.
:::

:::{grid-item-card} {octicon}`code` API reference
:link: reference/api
:link-type: doc

Python API for models, parsers, resolver, context, and environments.
:::

::::

```{toctree}
:hidden:

quickstart
tutorials/index
features
configuration
reference/cli
reference/api
motivation
changelog
```
