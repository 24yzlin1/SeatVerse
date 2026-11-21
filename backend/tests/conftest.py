"""Pytest fixtures：每个用例一个独立临时数据库，绝不触碰演示库。"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.seed import seed_all


@pytest.fixture()
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "seatverse-test.db"
    monkeypatch.setenv("SEATVERSE_DATABASE_PATH", str(db_path))
    monkeypatch.setenv(
        "SEATVERSE_JWT_SECRET", "pytest-seatverse-secret-0123456789abcdef"
    )
    seed_all(reset=True)
    return db_path


@pytest.fixture()
def client(database_path: Path) -> Iterator[TestClient]:
    import main

    with TestClient(main.app) as test_client:
        yield test_client
