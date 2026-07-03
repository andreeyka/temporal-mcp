from temporal_mcp.providers.client_provider import get_client_pool
from temporal_mcp.services.client_service import TemporalClientPool


def test_pool_singleton():
    a = get_client_pool()
    b = get_client_pool()
    assert a is b
    assert isinstance(a, TemporalClientPool)


def test_failure_service_provider_builds_service():
    from temporal_mcp.providers.service_provider import get_failure_service
    from temporal_mcp.services.failure_service import TemporalFailureService

    assert isinstance(get_failure_service(), TemporalFailureService)
