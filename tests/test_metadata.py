from types import SimpleNamespace

from odps_skill.metadata import MetadataService


class FakeClient:
    def __init__(self, tables):
        self._tables = tables

    def list_tables(self):
        return self._tables

    @classmethod
    def with_table_schema(cls):
        return cls([])

    def get_table(self, table_name):
        columns = [SimpleNamespace(name="order_id", type="BIGINT", comment="")]
        partitions = [SimpleNamespace(name="dt", type="STRING", comment="")]
        schema = SimpleNamespace(columns=columns, partitions=partitions)
        table = SimpleNamespace(
            name=table_name,
            project="demo",
            schema=schema,
            comment="orders",
            creation_time="2026-03-26",
            last_data_modified_time="2026-03-26",
            is_virtual_view=False,
            reload=lambda: None,
        )
        return table


def test_list_tables_returns_items_sorted_by_name():
    service = MetadataService(
        client=FakeClient(
            [
                SimpleNamespace(name="b_table", project="demo", creation_time="2026-03-26"),
                SimpleNamespace(name="a_table", project="demo", creation_time="2026-03-25"),
            ]
        )
    )
    payload = service.list_tables()
    assert payload["items"][0]["name"] == "a_table"


def test_describe_table_returns_columns_and_partitions():
    service = MetadataService(client=FakeClient.with_table_schema())
    payload = service.describe_table("orders")
    assert payload["columns"][0]["name"] == "order_id"
    assert payload["partitions"][0]["name"] == "dt"
