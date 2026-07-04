# Global Rules for AI Agents

**Python Version:** 3.12+

**Language Policy:**

- **All artifacts are English-only**: rules, code, docstrings, comments, error messages, commit messages, and documentation.
- This applies across the whole repository — no mixed-language files.

---

## Core Principles (MANDATORY)

Agent MUST follow DRY, KISS, YAGNI and actively refactor violations.

**DO NOT:**

- Duplicate code logic 3+ times.
- Create functions longer than 20 lines (excluding docstrings/type hints).
- Create classes longer than 200 lines.
- Create modules longer than 400 lines, or with more than 7 public functions/classes.
  (Exception: pure aggregation modules — package `__init__.py` re-export lists and the
  DI provider registry `providers/service_provider.py` — carry no logic and may list
  more than 7 re-exported/wiring symbols; the ≤7 cap targets logic-bearing modules.)
- Hardcode secrets or configuration values.
- Skip error handling.

**DO:**

- **DRY**: extract duplicated code (>5 lines) into reusable functions.
- **KISS**: keep implementations simple; avoid unnecessary abstractions.
- **YAGNI**: don't add functionality until it's needed.
- **Single Responsibility**: one class/function = one reason to change.
- **Dependency Injection**: use injectable dependencies for testability; avoid hardcoded dependencies.

These are hard limits — refactor immediately when exceeded.

---

## Error Handling Rules

All errors MUST use custom exception classes instead of standard Python exceptions (`ValueError`, `RuntimeError`, `TypeError`, `KeyError`, etc.) for business logic.

**DO NOT:**

- Use standard exceptions for business logic.
- Create exceptions that do not inherit from the project's base error class.
- Use generic exception types in docstrings (e.g. `ValueError`) instead of the specific class.
- Duplicate error messages across the codebase.

**DO:**

- Always use custom error classes from `temporal_mcp.errors`.
- All custom errors must inherit from the project's single base error class (e.g. `TemporalMcpError`).
- Use clear, specific class names (e.g. `WorkflowNotFoundError`, `NamespaceUnauthorizedError`).
- Error messages MUST be in English.
- Store additional context in instance attributes (e.g. workflow ID, namespace) for handling/logging.
- Document raised exceptions in the `Raises` section of docstrings with the specific class, not a generic type.

**Example:**

```python
from temporal_mcp.errors import TemporalMcpError


class WorkflowNotFoundError(TemporalMcpError):
    """Raised when a workflow cannot be found in the given namespace."""

    def __init__(self, workflow_id: str, namespace: str) -> None:
        """Initialize with the workflow and namespace that were not found.

        Args:
            workflow_id: ID of the workflow that was not found.
            namespace: Temporal namespace that was searched.
        """
        super().__init__(f"Workflow '{workflow_id}' not found in namespace '{namespace}'")
        self.workflow_id = workflow_id
        self.namespace = namespace
```

```python
async def get_workflow(self, workflow_id: str, namespace: str) -> WorkflowModel:
    """Fetch a workflow by ID from a given namespace.

    Args:
        workflow_id: ID of the workflow to fetch.
        namespace: Temporal namespace to search.

    Returns:
        The workflow model.

    Raises:
        WorkflowNotFoundError: If the workflow is not found in the namespace.
    """
    workflow = await self._temporal_service.get_workflow(workflow_id, namespace)
    if workflow is None:
        raise WorkflowNotFoundError(workflow_id, namespace)
    return workflow
```

---

## Code Organization

**Project package:** `temporal_mcp` (src-layout: `src/temporal_mcp/`).

Organize by technical layer (`errors`, `models`, `mappers`, `renderers`, `services`, `providers`, `tools`, `prompts`, `resources`, `utils`).

```text
src/temporal_mcp/
├── __init__.py
├── main.py                 # Entry point, FastMCP build and run
├── errors/                 # Base error class + domain exceptions + message constants
├── models/                 # Pydantic models for Temporal entities
├── mappers/                # Map Temporal SDK/protobuf responses to output models
├── renderers/              # Render output models as Markdown for tool output
├── services/               # Business logic (client pool, auth, domain services)
├── providers/              # DI providers (config, client pool, per-domain services)
├── tools/                  # MCP tool definitions (FastMCP `@mcp.tool`)
├── prompts/                # MCP prompt definitions
├── resources/              # Read-only MCP resources (cluster/namespace data)
└── utils/                  # Shared helpers (visibility queries, ...)
```

**DO:**

- Organize code by layer; keep related modules in the same layer directory.
- Use clear, descriptive module names (e.g. `workflow_service.py`, `namespace_tools.py`).
- Add integration subpackages only when a second non-Temporal integration is introduced.

---

## Using `else` in try-except Blocks

When a `try` block contains code that should only run after success (no exception), use the `else` block instead of placing the return at the end of `try` or duplicating it in `except`.

```python
try:
    workflow = await self._client.describe_workflow(workflow_id)
except WorkflowExecutionNotFoundError:
    raise WorkflowNotFoundError(workflow_id, namespace) from None
else:
    return WorkflowModel.from_describe_response(workflow)
```

---

## Python UV Execution Rules

**MANDATORY:** Agent MUST use `uv run python` instead of bare `python`/`python3` for all execution, and `uv run <tool>` for project tools (pytest, ruff, ty).

```bash
uv sync                          # install/update the environment
uv run python -m pytest          # run tests
uv run ruff check --fix          # lint
uv run ty check src              # type check (Astral ty)
uv run python -c "..."           # short inline snippets (<20 lines)
```

Never assume Python or project tools are available on bare `PATH` — always go through `uv run`.

---

## Linting and Type Checking Gate

**MANDATORY:** Agent MUST achieve zero errors at each step, in this exact sequence, before considering a change complete:

1. `uv run ruff check --fix --show-fixes` — auto-fix and resolve remaining lint errors.
2. `uv run ty check src` — resolve all type errors (Astral `ty`; config in `[tool.ty]`).
3. `uv run ruff format` — final formatting pass.

**DO NOT:**

- Skip a step or proceed with errors remaining.
- Use legacy typing syntax (`Union`, `Optional`, `List`, `Dict`) — use `X | None`, `list[X]`, `dict[K, V]`.
- Suppress a diagnostic without a specific rule and a justification comment — use `# ty: ignore[rule-name]  # why`, never a bare blanket ignore.
- Use `Any` without a justification comment.

**DO:**

- Fix errors by priority: critical (E9xx, F8xx) → security (S, B) → logic → style.
- Infer types from actual code (return statements, parameter usage), not guesswork.
- Re-run each command until it reports zero errors before moving to the next step.

---

## FastMCP Tool Parameter Rules

Tools use Pydantic `Field()` (directly or via `Annotated[Type, Field(...)]`) for all user-facing parameters — this drives validation and the schema shown to LLM clients.

**DO NOT:**

- Use `Field()` on dependency-injection parameters (e.g. a service or provider injected by FastMCP). DI parameters carry no `Field()`.
- Use `Field(default=None, ...)` for optional values — use the positional form `Field(None, ...)`.
- Skip `# noqa: B008` when `Field()` is used as a literal default value.

**DO:**

- Prefer `Annotated[Type, Field(...)]` when there are constraints (`ge`/`le`, `min_length`/`max_length`, `pattern`).
- Give every field of a pydantic entity model (in `models/`) a `Field(description=...)`; use `Annotated[Type, Field(description=...)]`.
- Use `param: Type = Field(...)` for simple, description-only parameters.

**Example:**

```python
from typing import Annotated

from pydantic import Field

from temporal_mcp.providers import TemporalWorkflowServiceProvider
from temporal_mcp.services.workflow_service import TemporalWorkflowService


@temporal_mcp_tools.tool
async def get_workflow_status(
    workflow_id: Annotated[str, Field(description="Workflow ID to look up")],
    namespace: Annotated[str, Field(description="Temporal namespace to search")],
    *,
    temporal_workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,  # no Field(): DI
) -> ToolResult:
    """Get the current status of a workflow execution."""
    ...
```

**Tool annotations:** every `@*.tool(...)` registration passes
`annotations=read_only("Title")` / `write("Title")` / `mutating("Title")`
from `temporal_mcp.tool_annotations` — never a hand-built `ToolAnnotations`.
Reads use `read_only`; additive/reversible writes (e.g. start/signal/query/
cancel workflow, pause/unpause schedule) use `write`; destructive,
non-idempotent ops (`terminate_workflow`, `delete_schedule`) use `mutating`.
Every tool has a human-readable `title` via the factory's `title` argument.

---

## MCP ToolResult Structured Output

Tools that return entity or list data from Temporal (workflows, events, namespaces, ...) MUST support optional structured output via `ToolResult.structured_content`, so clients can consume JSON instead of parsing text.

**DO:**

- Add `structured_content: bool = Field(default=False, description="...")` to tools returning lists or single entities.
- When `structured_content=True`, set `result.structured_content` to a dict with a clear key for the payload (e.g. `{"workflows": [...]}`, or the entity dict itself for a single object).
- Always return human-readable text/markdown in `content`; `structured_content` is opt-in, additive.

```python
result = ToolResult(content=[TextContent(type="text", text=formatted_text)])
if structured_content:
    result.structured_content = {"workflows": [w.model_dump(mode="json") for w in workflows]}
return result
```

---

## Documentation

All docstrings follow Google-style format (`Args`, `Returns`, `Raises`), written in English, for all public functions, classes, and modules.
