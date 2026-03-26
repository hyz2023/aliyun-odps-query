import pytest

from odps_skill.query import InvalidQueryError
from odps_skill.query import validate_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t SELECT * FROM s",
        "DELETE FROM t WHERE id = 1",
        "DROP TABLE t",
        "SELECT * FROM t; DELETE FROM t",
    ],
)
def test_validate_read_only_sql_rejects_mutations(sql):
    with pytest.raises(InvalidQueryError):
        validate_read_only_sql(sql)
