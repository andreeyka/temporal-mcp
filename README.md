# temporal-multi-namespace-mcp

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastMCP 3](https://img.shields.io/badge/FastMCP-3%2B-purple.svg)](https://gofastmcp.com/)
[![Temporal](https://img.shields.io/badge/Temporal-MCP-6366f1.svg)](https://temporal.io/)

**Multi-namespace [Temporal](https://temporal.io/) MCP server** built on [FastMCP 3](https://gofastmcp.com/).
Expose cluster, namespace, workflow, schedule, failure-analysis, and task-queue operations to AI agents through the [Model Context Protocol](https://modelcontextprotocol.io/).

Unlike single-namespace Temporal MCP servers, every namespace-scoped tool takes `namespace` as an explicit argument — one server instance serves **all** namespaces in the cluster.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Connect an MCP Client](#connect-an-mcp-client)
- [Docker](#docker)
- [Kubernetes](#kubernetes)
- [Configuration](#configuration)
- [Tools](#tools)
- [Prompts and Resources](#prompts-and-resources)
- [Architecture](#architecture)
- [Development](#development)
- [License](#license)

## Features

| Area | What you get |
| --- | --- |
| **Multi-namespace** | One MCP server for the whole cluster; pass `namespace` per call instead of pinning a single namespace in config. |
| **Workflow ops** | List, describe, count, start, signal, query, cancel, pause, unpause, update, reset, and terminate workflows. |
| **Failure triage** | Analyze workflow failures, summarize namespace failures, and rank top failure types. |
| **Schedules & queues** | List/describe schedules, pause/unpause, create/update/trigger/backfill; describe task queues and search attributes. |
| **Cluster admin** | Namespaces, batch operations, worker deployments, Nexus endpoints, workflow rules, and activities. |
| **Auth flexibility** | Service API key/OIDC, caller token passthrough, or RFC 8693 token exchange. |
| **Read-only mode** | Hide all mutating tools server-side with `MCP_READ_ONLY=true`. |
| **Tool discovery** | BM25 `search_tools` / `call_tool` layer on top of the full tool catalog. |
| **Structured output** | Optional `structured_content=true` on entity/list tools for JSON payloads. |

## Quick Start

### Prerequisites

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A running Temporal cluster (local [Temporal CLI](https://docs.temporal.io/cli) dev server or remote frontend)

### Install and run

```bash
git clone https://github.com/andreeyka/temporal-mcp.git
cd temporal-mcp

cp env.examples .env   # edit TEMPORAL_HOST and auth settings
uv sync
uv run temporal-mcp
```

The server listens on `MCP_HOST:MCP_PORT` (default `0.0.0.0:8000`) using the transport from `MCP_TRANSPORT` (default `http`).

### Minimal `.env` for local dev

```bash
TEMPORAL_HOST=localhost:7233
TEMPORAL_AUTH_MODE=service
# TEMPORAL_API_KEY=...        # if your cluster requires it
MCP_TRANSPORT=http
MCP_PORT=8000
```

## Connect an MCP Client

Add the server to your MCP client configuration. Example for **Cursor** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "temporal": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Then ask your agent to `list_namespaces`, pick a namespace, and call workflow or failure tools with that `namespace` argument.

<details>
<summary><strong>Read-only deployment</strong></summary>

Set `MCP_READ_ONLY=true` in `.env` before starting the server. Mutating tools are unlisted and cannot be invoked, including through the `call_tool` search proxy.

</details>

## Docker

### Local image

```bash
docker build -t temporal-mcp .
docker run --rm -p 8000:8000 \
  -e TEMPORAL_HOST=host.docker.internal:7233 \
  temporal-mcp
```

The image runs the `temporal-mcp` console script with `MCP_TRANSPORT=http`,
`MCP_HOST=0.0.0.0`, and `MCP_PORT=8000` by default. Override configuration with
environment variables at runtime.

### Published images

Release images are published to GitHub Container Registry:

```bash
docker pull ghcr.io/andreeyka/temporal-mcp:v0.1.1
```

The release workflow publishes immutable SemVer tags from git tags:

| Git tag | Image tags |
| --- | --- |
| `v0.1.1` | `v0.1.1`, `0.1.1`, `0.1` |

The project does not publish `latest`. Pin a concrete version tag in Kubernetes.

### Release procedure

Keep `pyproject.toml` and the git tag aligned:

```bash
uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
git tag v0.1.1
git push origin v0.1.1
```

The tag push builds and publishes `ghcr.io/andreeyka/temporal-mcp:v0.1.1`.

## Kubernetes

Configure the container through environment variables. Use a ConfigMap for
non-secret values and a Secret for credentials.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: temporal-mcp-config
data:
  MCP_TRANSPORT: http
  MCP_PORT: "8000"
  MCP_READ_ONLY: "false"
  TEMPORAL_HOST: temporal-frontend.temporal.svc.cluster.local:7233
  TEMPORAL_AUTH_MODE: service
---
apiVersion: v1
kind: Secret
metadata:
  name: temporal-mcp-secret
type: Opaque
stringData:
  TEMPORAL_API_KEY: replace-me
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: temporal-mcp
  template:
    metadata:
      labels:
        app: temporal-mcp
    spec:
      containers:
        - name: temporal-mcp
          image: ghcr.io/andreeyka/temporal-mcp:v0.1.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
          envFrom:
            - configMapRef:
                name: temporal-mcp-config
            - secretRef:
                name: temporal-mcp-secret
---
apiVersion: v1
kind: Service
metadata:
  name: temporal-mcp
spec:
  selector:
    app: temporal-mcp
  ports:
    - name: http
      port: 8000
      targetPort: http
```

If the GHCR package is private, add an `imagePullSecrets` entry that references
a registry credential secret in the target namespace.

## Configuration

Settings are loaded from the environment (or a `.env` file) via `pydantic-settings`. Copy `env.examples` as a starting point.

### Server (`MCP_*`)

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_SERVER_NAME` | `temporal-multi-namespace` | MCP server name |
| `MCP_MASK_ERROR_DETAILS` | `true` | Hide internal error details from clients |
| `MCP_HOST` | `0.0.0.0` | Bind host |
| `MCP_PORT` | `8000` | Bind port |
| `MCP_TRANSPORT` | `http` | `http`, `streamable-http`, or `sse` |
| `MCP_STATELESS_HTTP` | `true` | Stateless HTTP mode |
| `MCP_READ_ONLY` | `false` | Expose only read-only tools |
| `MCP_TOOL_SEARCH` | `true` | Expose tools via BM25 `search_tools`/`call_tool`; `false` lists the full catalog |
| `MCP_AUTH_MODE` | `none` | Incoming auth: `none` or `keycloak` (client-initiated SSO via RFC 9728) |
| `MCP_AUTH_CLAIM_EXPR` | _(empty)_ | Optional CEL expression for verified incoming JWT claims, such as Keycloak `groups` |

### Temporal (`TEMPORAL_*`)

| Variable | Default | Description |
| --- | --- | --- |
| `TEMPORAL_HOST` | `localhost:7233` | Temporal frontend address |
| `TEMPORAL_AUTH_MODE` | `service` | `service`, `passthrough`, or `exchange` |
| `TEMPORAL_API_KEY` | _(empty)_ | Static API key (service mode) |
| `TEMPORAL_POOL_MAX` | `64` | Max cached `(namespace, identity)` clients |

<details>
<summary><strong>OIDC and token-exchange settings</strong></summary>

| Variable | Description |
| --- | --- |
| `TEMPORAL_OIDC_TOKEN_URL` | OIDC client-credentials token URL (service mode) |
| `TEMPORAL_OIDC_CLIENT_ID` / `TEMPORAL_OIDC_CLIENT_SECRET` | OIDC client credentials |
| `TEMPORAL_OIDC_SCOPE` / `TEMPORAL_OIDC_AUDIENCE` | Optional OIDC scope/audience |
| `TEMPORAL_OIDC_REFRESH_SECONDS` | Background JWT refresh interval (default `300`) |
| `TEMPORAL_EXCHANGE_TOKEN_URL` | RFC 8693 token-exchange endpoint (exchange mode) |
| `TEMPORAL_EXCHANGE_AUDIENCE` / `TEMPORAL_EXCHANGE_SCOPE` | Exchange audience/scope |
| `TEMPORAL_EXCHANGE_CLIENT_ID` / `TEMPORAL_EXCHANGE_CLIENT_SECRET` | Exchange client credentials |

</details>

Auth has two independent boundaries — incoming (who can call this server,
`MCP_AUTH_*`/`IDP_*`) and outbound (what identity the server presents to
Temporal, `TEMPORAL_AUTH_MODE`) — that share a common `IDP_*` issuer anchor.
When `MCP_AUTH_MODE=keycloak`, `MCP_AUTH_CLAIM_EXPR` can further restrict
access by verified JWT claims after issuer, signature, and audience checks pass.
Tokens that pass JWT validation but fail this expression receive an MCP
authorization error instead of being treated as invalid tokens.
See [`docs/auth/README.md`](docs/auth/README.md) for the full model and a
decision guide, and the per-mode guides for setup and verification steps:

- [Keycloak setup](docs/auth/keycloak-setup.md)
- [Mode: service](docs/auth/mode-service.md)
- [Mode: passthrough](docs/auth/mode-passthrough.md)
- [Mode: exchange](docs/auth/mode-exchange.md)
- [Incoming auth / SSO](docs/auth/incoming-sso.md)

## Tools

Tools are grouped by domain. Namespace-scoped tools require a `namespace` argument.

| Domain | Read | Write / mutate |
| --- | --- | --- |
| **Cluster & namespace** | `get_cluster_info`, `list_namespaces`, `describe_namespace` | — |
| **Workflows** | `list_workflows`, `describe_workflow`, `get_workflow_history`, `count_workflows` | `start_workflow`, `signal_workflow`, `query_workflow`, `cancel_workflow`, `terminate_workflow`, `pause_workflow`, `unpause_workflow`, `signal_with_start_workflow`, `update_workflow`, `reset_workflow` |
| **Failures** | `analyze_workflow_failure`, `summarize_namespace_failures`, `top_failure_types` | — |
| **Schedules** | `list_schedules`, `describe_schedule` | `pause_schedule`, `unpause_schedule`, `delete_schedule`, `create_schedule`, `update_schedule`, `trigger_schedule`, `backfill_schedule` |
| **Task queues** | `describe_task_queue`, `list_search_attributes` | — |
| **Activities** | `list_activities`, `describe_activity` | — |
| **Batch ops** | `list_batch_operations`, `describe_batch_operation` | `stop_batch_operation` |
| **Worker deployments** | `list_worker_deployments`, `describe_worker_deployment` | — |
| **Nexus** | `list_nexus_endpoints`, `get_nexus_endpoint` | `create_nexus_endpoint`, `delete_nexus_endpoint` |
| **Workflow rules** | `list_workflow_rules`, `describe_workflow_rule` | `create_workflow_rule`, `delete_workflow_rule` |
| **Discovery** | `search_tools`, `call_tool` (BM25 layer; underlying tools remain callable) | — |

Tool annotations follow three levels: **read** (`read_only`), **write** (additive/reversible), and **mutate** (destructive). When `MCP_READ_ONLY=true`, all `mutating`-tagged tools are disabled.

## Prompts and Resources

**Prompts** (`prompts_mcp`):

| Prompt | Purpose |
| --- | --- |
| `triage_namespace_failures` | Walk through failed executions in a namespace |
| `diagnose_workflow_failure` | Root-cause analysis for one workflow |
| `cluster_health_review` | Cluster-wide health and failure load review |

**Resources** (`resources_mcp`):

| URI | Content |
| --- | --- |
| `temporal://namespaces` | JSON list of all namespaces |
| `temporal://namespace/{ns}/failures` | JSON failure summary for a namespace |

## Architecture

Layered layout under `src/temporal_mcp/`:

```
src/temporal_mcp/
├── main.py              # FastMCP app, providers, pool lifespan, BM25 transform
├── config.py            # McpServerConfig (MCP_*) + TemporalConfig (TEMPORAL_*)
├── tools/               # MCP tool definitions by domain
├── services/            # Business logic and Temporal client pool
├── providers/           # DI wiring (config, pool, per-domain services)
├── models/              # Pydantic output models
├── mappers/             # Temporal SDK/protobuf to Pydantic model conversion
├── renderers/           # Markdown text rendering
├── errors/              # TemporalMcpError hierarchy
├── prompts/             # Reusable MCP prompts
└── resources/           # Read-only MCP resources
```

**Request flow:** tools validate input → providers supply pooled Temporal SDK clients → services fetch raw Temporal data → mappers build Pydantic output models → renderers build Markdown responses.

`TemporalClientPool` caches gRPC clients per `(namespace, identity)` with LRU eviction and is started/stopped via the FastMCP lifespan in `main.py`.

## Development

```bash
uv sync
uv run ruff check --fix --show-fixes
uv run ty check src
uv run ruff format
uv run pytest -q
```

See [`AGENTS.md`](AGENTS.md) for coding conventions (module size limits, custom errors, English-only artifacts).

## License

[MIT](LICENSE) © Andrey Shlyapin
