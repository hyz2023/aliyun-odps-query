MUTATION_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"}


class InvalidQueryError(ValueError):
    """Raised when a query violates the local read-only contract."""


def validate_read_only_sql(sql: str) -> None:
    normalized = sql.strip().upper()
    if ";" in normalized.rstrip(";"):
        raise InvalidQueryError("Multi-statement SQL is not supported")
    if any(keyword in normalized for keyword in MUTATION_KEYWORDS):
        raise InvalidQueryError("Only read-only SQL is supported")
