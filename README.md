# Launchpad

---

Launchpad is a GitOps commit generator that lets you deploy Helm charts to Kubernetes through a simple web UI while keeping Git as the single source of truth. 
Every deployment becomes auditable and reproducible through Git commit. No controllers, no lock in, no hidden state.

It is not:

- A Kubernetes controller

- A GitOps platform

- A cluster owner

Git remains the single source of truth.

---

## Core Idea

Launchpad reduces cognitive load when deploying Helm charts but it does not abstract Kubernetes away.

It:

- Executes Helm

- Writes `values.yaml` and deployment metadata to the repository

- Optionally signs commits

- Provides lightweight read only observability

It does not:

- Reconcile drift

- Continuously watch the cluster

- Introduce custom controllers

---

## Git Repository Structure

Repository layout:

```
repo-root/
├── backup_charts/
│   └── <helm_chart_name>_<helm_chart_version>/
│       └── <helm_chart_name>/
│           └── (full pulled Helm chart)
└── charts/
    └── <release_name>/
        └── <namespace>/
            ├── metadata.yaml
            └── values.yaml
```

### `metadata.yaml`

Metadata describing what was deployed and when:

```
backup_helm_chart_deployed: <boolean>
helm_chart_name: <chart name>
helm_chart_url: <source URL>
helm_chart_version: <deployed version>
timestamp: <deployment timestamp>
```

### `values.yaml`

The exact Helm values used for the deployment.

This guarantees reproducibility and clean Git diffs.

---

## Deployment Flow

1. User submits Helm configuration via UI

2. Backend validates input and YAML

3. Helm CLI executes against the cluster

4. On success:

    - `values.yaml` is written

    - `metadata.yaml` is written

    - Commit is created

    - Changes are pushed to the configured branch

Commit format:

```
bot(<release_namespace>): Update Helm chart and values [<timestamp>].
```

Commits can be optionally GPG signed. Each deployment is a auditable Git event.

---

## Cluster Observability

Read-only cluster inspection lets you:

- View the full cluster state

- Inspect specific release namespaces and services

---

## Configuration Overview

Launchpad requires:

### GitOps

- Repository URL

- Personal access token

- Branch name

- Commit identity

- Optional GPG key

### Kubernetes

- API server

- Token

- Base64 CA certificate

Database configuration exists for future use.

Launchpad itself remains stateless.

---

## No Lock In

Launchpad is fully removable. You can:

- Disable the service

- Delete deployments

- Migrate to ArgoCD or Flux

No CRDs, controllers, reconciliation loops or proprietary data stores are required. Git remains the source of truth.

---