import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    access_id: str | None
    access_key: str | None
    endpoint: str
    project: str


def load_config(
    *,
    access_id: str | None = None,
    access_key: str | None = None,
    endpoint: str | None = None,
    project: str | None = None,
) -> RuntimeConfig:
    resolved_project = project or os.getenv("ALIBABA_ODPS_PROJECT")
    if not resolved_project:
        raise ValueError("Missing project")

    return RuntimeConfig(
        access_id=access_id or os.getenv("ALIBABA_ACCESSKEY_ID"),
        access_key=access_key or os.getenv("ALIBABA_ACCESSKEY_SECRET"),
        endpoint=endpoint or os.getenv("ALIBABA_ODPS_ENDPOINT", "http://service.odps.aliyun.com/api"),
        project=resolved_project,
    )
