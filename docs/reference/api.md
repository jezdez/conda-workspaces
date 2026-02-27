# API reference

```{toctree}
:hidden:

api/models
api/parsers
api/resolver
api/context
api/environments
```

::::{grid} 2
:gutter: 3

:::{grid-item-card} Models
:link: api/models
:link-type: doc

Workspace configuration, features, environments, dependencies, and channels.
:::

:::{grid-item-card} Parsers
:link: api/parsers
:link-type: doc

File format parsers, detection logic, and the parser registry.
:::

:::{grid-item-card} Resolver
:link: api/resolver
:link-type: doc

Feature-to-environment resolution and solve-group coordination.
:::

:::{grid-item-card} Context
:link: api/context
:link-type: doc

Lazy workspace context for conda state and platform introspection.
:::

:::{grid-item-card} Environments
:link: api/environments
:link-type: doc

Environment creation, removal, and inspection via conda's APIs.
:::

::::
