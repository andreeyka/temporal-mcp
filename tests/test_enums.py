from temporal_mcp.enums import AuthMode, TemporalToolTags, TransportType
from temporal_mcp.tool_annotations import mutating, read_only


def test_enum_values():
    assert TransportType.HTTP.value == "http"
    assert AuthMode.PASSTHROUGH.value == "passthrough"
    assert TemporalToolTags.MUTATING.value == "mutating"


def test_annotations():
    read_only_annotations = read_only("")
    mutating_annotations = mutating("")
    assert read_only_annotations.readOnlyHint is True
    assert read_only_annotations.idempotentHint is True
    assert read_only_annotations.openWorldHint is True
    assert mutating_annotations.readOnlyHint is False
    assert mutating_annotations.destructiveHint is True
    assert mutating_annotations.idempotentHint is False
    assert mutating_annotations.openWorldHint is True


def test_failure_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.FAILURE == "failure"


def test_activity_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.ACTIVITY == "activity"


def test_worker_deployment_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.WORKER_DEPLOYMENT == "worker_deployment"


def test_batch_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.BATCH == "batch"


def test_workflow_rule_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.WORKFLOW_RULE == "workflow_rule"


def test_nexus_tag_value():
    from temporal_mcp.enums import TemporalToolTags

    assert TemporalToolTags.NEXUS == "nexus"


def test_incoming_auth_mode_values():
    from temporal_mcp.enums import IncomingAuthMode

    assert IncomingAuthMode.NONE == "none"
    assert IncomingAuthMode.KEYCLOAK == "keycloak"
    assert {m.value for m in IncomingAuthMode} == {"none", "keycloak"}
