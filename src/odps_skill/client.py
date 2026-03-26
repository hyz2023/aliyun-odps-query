from odps_skill.config import RuntimeConfig


class DependencyMissingError(RuntimeError):
    """Raised when an optional runtime dependency is unavailable."""


def create_client(config: RuntimeConfig):
    try:
        from odps import ODPS
    except ImportError as exc:
        raise DependencyMissingError("pyodps is required") from exc

    return ODPS(
        access_id=config.access_id,
        secret_access_key=config.access_key,
        endpoint=config.endpoint,
        project=config.project,
    )
