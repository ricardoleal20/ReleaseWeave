# ReleaseWeave quickstart / Inicio rápido

ReleaseWeave records changes, previews the next versions and updates only affected package manifests and changelogs. These examples use the executable shipped in this archive; after installation, run `releaseweave` from your PATH.

## Single repository

From a project containing Cargo.toml, package.json or pyproject.toml:

```sh
releaseweave init --yes --mode single
releaseweave create --bump minor --message "Add configurable greetings"
releaseweave plan
releaseweave bump --dry-run
releaseweave bump
```

A 1.2.3 package becomes 1.3.0, gains a CHANGELOG entry and records the proposed v1.3.0 GitHub tag. The bump command changes local files; publishing is handled by the optional GitHub workflows.

## Monorepo

From the root containing several independently versioned packages:

```sh
releaseweave init --yes --mode monorepo
releaseweave create --package acme-api --bump minor --message "Add a health endpoint"
releaseweave create --package @acme/web --bump patch --message "Fix status indicator"
releaseweave plan --json
releaseweave bump --dry-run
releaseweave bump
```

| Package | Before | After | Tag |
| --- | --- | --- | --- |
| acme-api | 1.4.0 | 1.5.0 | acme-api/v1.5.0 |
| @acme/web | 2.1.0 | 2.1.1 | @acme/web/v2.1.1 |
| acme-worker | 0.7.2 | unchanged | none |

Review releaseweave.toml after discovery to select the packages you release. Only affected packages receive changelogs. Incompatible Cargo path-dependency requirements stop the plan with instructions to update them manually.

## Try the included examples safely

Copy examples/single-repo or examples/monorepo to a temporary directory. Then run the commands above from the copied root, or pass `--root PATH`. Original fixture versions stay unchanged so the examples can be repeated.

## GitHub

`releaseweave init --yes --github` adds release-PR and release-on-merge workflow templates without overwriting existing files. Use `ricardoleal20/ReleaseWeave@v0.2.0` for the CLI action, or pin its exact commit for reproducible setup. The workflows require contents/pull-requests permissions and the repository setting allowing Actions to create PRs.

## Límites de esta primera release

Las versiones son independientes y explícitas. No hay propagación automática de bumps/rangos, versiones heredadas `version.workspace`, prereleases, grupos fijos ni publicación en registries. Cargo.lock se actualiza para paquetes locales; otros lockfiles se regeneran con su package manager. `bump --dry-run` no modifica archivos. `release --json` permite inspeccionar la metadata de publicación.
