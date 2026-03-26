from types import SimpleNamespace

from odps_skill.metadata import MetadataService


class FakeClient:
    def __init__(self, tables):
        self._tables = tables

    def list_tables(self):
        return self._tables


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
