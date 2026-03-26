from odps_skill.diagnostics import build_diagnostics
from odps_skill.diagnostics import build_summary


def test_build_query_summary_marks_truncated_results():
    summary = build_summary(
        action="query",
        data={"columns": ["id"], "rows": [{"id": 1}], "count": 1},
        meta={"truncated": True},
    )
    assert "truncated" in summary.lower()


def test_build_diagnostics_for_empty_result_suggests_partition_checks():
    diagnostics = build_diagnostics(error_type="empty_result", context={"action": "query"})
    assert any("partition" in item.lower() for item in diagnostics)
