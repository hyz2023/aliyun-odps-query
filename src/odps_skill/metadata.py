class MetadataService:
    def __init__(self, client):
        self.client = client

    def list_tables(self, *, pattern: str | None = None) -> dict:
        items = []
        for table in self.client.list_tables():
            name = table.name
            if pattern and pattern.lower() not in name.lower():
                continue
            items.append(
                {
                    "name": name,
                    "project": getattr(table, "project", None),
                    "created_time": str(getattr(table, "creation_time", "")),
                    "is_virtual_view": bool(getattr(table, "is_virtual_view", False)),
                }
            )
        items.sort(key=lambda item: item["name"])
        return {"items": items, "count": len(items)}

    def describe_table(self, table_name: str) -> dict:
        table = self.client.get_table(table_name)
        if hasattr(table, "reload"):
            table.reload()
        schema = getattr(table, "schema", None)
        columns = [
            {
                "name": column.name,
                "type": str(getattr(column, "type", "")),
                "comment": getattr(column, "comment", ""),
            }
            for column in getattr(schema, "columns", [])
        ]
        partitions = [
            {
                "name": partition.name,
                "type": str(getattr(partition, "type", "")),
                "comment": getattr(partition, "comment", ""),
            }
            for partition in getattr(schema, "partitions", [])
        ]
        return {
            "name": table.name,
            "project": getattr(table, "project", None),
            "comment": getattr(table, "comment", ""),
            "created_time": str(getattr(table, "creation_time", "")),
            "last_modified_time": str(getattr(table, "last_data_modified_time", "")),
            "is_virtual_view": bool(getattr(table, "is_virtual_view", False)),
            "columns": columns,
            "partitions": partitions,
        }
