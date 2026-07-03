import pytest

from temporal_mcp.errors import UnknownWorkflowStatusError
from temporal_mcp.utils.query import status_to_query


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("failed", 'ExecutionStatus="Failed"'),
        ("RUNNING", 'ExecutionStatus="Running"'),
        ("TIMED_OUT", 'ExecutionStatus="TimedOut"'),
        ("continued_as_new", 'ExecutionStatus="ContinuedAsNew"'),
        (None, None),
    ],
)
def test_status_to_query(inp, expected):
    assert status_to_query(inp) == expected


def test_status_to_query_invalid():
    with pytest.raises(UnknownWorkflowStatusError):
        status_to_query("bogus")
