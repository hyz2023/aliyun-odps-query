import pytest

from odps_skill.config import load_config


def test_load_config_requires_project(monkeypatch):
    monkeypatch.delenv("ALIBABA_ODPS_PROJECT", raising=False)
    with pytest.raises(ValueError, match="project"):
        load_config(project=None)
