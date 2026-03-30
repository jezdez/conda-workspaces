# CI pipeline

This tutorial shows how to use conda-workspaces in GitHub Actions to
install environments, run tasks, and test your project.

## Basic setup

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4

      - uses: conda-incubator/setup-miniconda@v3
        with:
          miniforge-version: latest
          activate-environment: ""

      - name: Install conda-workspaces
        run: conda install -c conda-forge conda-workspaces

      - name: Install test environment
        run: conda workspace install -e test

      - name: Run tests
        run: conda task run -e test check
```

## Caching environments

Speed up CI by caching the `.conda/envs/` directory:

```yaml
      - uses: actions/cache@v4
        with:
          path: .conda/envs
          key: conda-envs-${{ runner.os }}-${{ hashFiles('conda.toml') }}
          restore-keys: |
            conda-envs-${{ runner.os }}-

      - name: Install test environment
        run: conda workspace install -e test
```

## Multiple environments

Run different checks in separate jobs:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: conda-incubator/setup-miniconda@v3
        with:
          miniforge-version: latest
      - run: conda install -c conda-forge conda-workspaces
      - run: conda workspace install -e test
      - run: conda task run -e test check

  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: conda-incubator/setup-miniconda@v3
        with:
          miniforge-version: latest
      - run: conda install -c conda-forge conda-workspaces
      - run: conda workspace install -e docs
      - run: conda task run -e docs build-docs
```

## Task caching in CI

If your tasks use `inputs`/`outputs` caching, the cache directory can
be preserved between runs for faster incremental builds:

```yaml
      - uses: actions/cache@v4
        with:
          path: ~/.cache/conda-workspaces
          key: conda-workspaces-tasks-${{ hashFiles('src/**/*.py') }}
```

## Tasks without workspaces

If you use conda-workspaces only for task running (no workspace
definition), your CI setup is simpler — just install dependencies
manually and run tasks:

```yaml
      - run: conda install -c conda-forge conda-workspaces pytest ruff
      - run: conda task run check
```
