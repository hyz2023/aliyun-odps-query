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
