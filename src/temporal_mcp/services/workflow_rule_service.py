"""Workflow-rule operations (low-level workflow_service RPCs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from temporalio.api.rules.v1 import WorkflowRuleAction, WorkflowRuleSpec
from temporalio.api.workflowservice.v1 import (
    CreateWorkflowRuleRequest,
    DeleteWorkflowRuleRequest,
    DescribeWorkflowRuleRequest,
    ListWorkflowRulesRequest,
)


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalWorkflowRuleService:
    """List, describe, create, and delete workflow rules."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_workflow_rules(self, namespace: str) -> list[Any]:
        """List all workflow rules in a namespace.

        Args:
            namespace: Target namespace.

        Returns:
            A list of WorkflowRule protos.
        """
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.list_workflow_rules(ListWorkflowRulesRequest(namespace=namespace))
        return list(resp.rules)

    async def describe_workflow_rule(self, namespace: str, rule_id: str) -> Any:  # noqa: ANN401
        """Return the WorkflowRule for one rule id.

        Args:
            namespace: Target namespace.
            rule_id: Workflow rule id.

        Returns:
            A WorkflowRule proto.
        """
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.describe_workflow_rule(
            DescribeWorkflowRuleRequest(namespace=namespace, rule_id=rule_id)
        )
        return resp.rule

    async def create_workflow_rule(
        self,
        namespace: str,
        rule_id: str,
        visibility_query: str,
        description: str = "",
        expiration: str | None = None,
    ) -> str:
        """Create a workflow rule that pauses matching activities.

        Args:
            namespace: Target namespace.
            rule_id: Id to assign to the new rule.
            visibility_query: Visibility query selecting target workflows.
            description: Human-readable description of the rule.
            expiration: Optional ISO-8601 expiration timestamp.

        Returns:
            The created rule id.
        """
        spec = WorkflowRuleSpec(
            id=rule_id,
            visibility_query=visibility_query,
            actions=[WorkflowRuleAction(activity_pause=WorkflowRuleAction.ActionActivityPause())],
        )
        if expiration:
            spec.expiration_time.FromDatetime(datetime.fromisoformat(expiration))
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.create_workflow_rule(
            CreateWorkflowRuleRequest(
                namespace=namespace,
                spec=spec,
                identity="temporal-mcp",
                request_id=str(uuid.uuid4()),
                description=description,
            )
        )
        return resp.rule.spec.id

    async def delete_workflow_rule(self, namespace: str, rule_id: str) -> None:
        """Delete a workflow rule.

        Args:
            namespace: Target namespace.
            rule_id: Workflow rule id to delete.
        """
        client = await self._pool.get(namespace)
        await client.workflow_service.delete_workflow_rule(
            DeleteWorkflowRuleRequest(namespace=namespace, rule_id=rule_id)
        )
