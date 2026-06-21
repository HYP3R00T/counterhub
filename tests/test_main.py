import sys
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.main as main_module
from app.main import app


class RpcRequest:
    def __init__(self, data: Any):
        self._data = data

    async def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=self._data)


class TableRequest:
    def __init__(self, data: Any):
        self._data = data

    def select(self, *_args: Any, **_kwargs: Any) -> "TableRequest":
        return self

    def limit(self, *_args: Any, **_kwargs: Any) -> "TableRequest":
        return self

    async def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=self._data)


class StubClient:
    def __init__(self, rpc_responses: dict[str, Any] | None = None, table_data: Any = None):
        self.rpc_responses = rpc_responses if rpc_responses is not None else {}
        self.table_request = TableRequest(table_data if table_data is not None else [])
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []

    def rpc(self, fn: str, params: dict[str, Any]) -> RpcRequest:
        self.rpc_calls.append((fn, params))
        response = self.rpc_responses.get(fn, [])
        if isinstance(response, list):
            data = response.pop(0) if response and isinstance(response[0], list) else response
        else:
            data = response
        return RpcRequest(data)

    def table(self, _name: str) -> TableRequest:
        return self.table_request


async def stub_get_client_factory(client: StubClient) -> StubClient:
    return client


def test_increment_counter_returns_totals(monkeypatch) -> None:
    updated_at = datetime(2026, 6, 21, tzinfo=UTC).isoformat()
    client = StubClient(
        rpc_responses={
            "increment_counter": [
                {
                    "counter_id": "dotfiles",
                    "total_count": 13,
                    "today_count": 3,
                    "updated_at": updated_at,
                }
            ]
        }
    )
    monkeypatch.setattr(main_module, "get_client", lambda: stub_get_client_factory(client))

    response = TestClient(app).post("/count/dotfiles")

    assert response.status_code == 200
    assert response.json() == {
        "counter_id": "dotfiles",
        "total_count": 13,
        "today_count": 3,
        "updated_at": "2026-06-21T00:00:00Z",
    }
    assert client.rpc_calls == [("increment_counter", {"counter_name": "dotfiles"})]


def test_increment_counter_returns_404_when_unregistered(monkeypatch) -> None:
    client = StubClient(rpc_responses={"increment_counter": []})
    monkeypatch.setattr(main_module, "get_client", lambda: stub_get_client_factory(client))

    response = TestClient(app).post("/count/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "counter not found"}


def test_get_counter_returns_summary(monkeypatch) -> None:
    updated_at = datetime(2026, 6, 21, tzinfo=UTC).isoformat()
    client = StubClient(
        rpc_responses={
            "get_counter_summary": [
                {
                    "counter_id": "dotfiles",
                    "total_count": 12,
                    "last_updated_at": updated_at,
                    "first_bucket_date": date(2026, 6, 11).isoformat(),
                    "last_bucket_date": date(2026, 6, 21).isoformat(),
                }
            ]
        }
    )
    monkeypatch.setattr(main_module, "get_client", lambda: stub_get_client_factory(client))

    response = TestClient(app).get("/count/dotfiles")

    assert response.status_code == 200
    assert response.json() == {
        "counter_id": "dotfiles",
        "total_count": 12,
        "last_updated_at": "2026-06-21T00:00:00Z",
        "first_bucket_date": "2026-06-11",
        "last_bucket_date": "2026-06-21",
    }


def test_get_counter_returns_404_when_unregistered(monkeypatch) -> None:
    client = StubClient(rpc_responses={"get_counter_summary": []})
    monkeypatch.setattr(main_module, "get_client", lambda: stub_get_client_factory(client))

    response = TestClient(app).get("/count/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "counter not found"}


def test_get_counter_series_returns_points_and_total(monkeypatch) -> None:
    client = StubClient(
        rpc_responses={
            "get_counter_summary": [
                [
                    {
                        "counter_id": "dotfiles",
                        "total_count": 12,
                        "last_updated_at": None,
                        "first_bucket_date": date(2026, 1, 1).isoformat(),
                        "last_bucket_date": date(2026, 1, 31).isoformat(),
                    }
                ]
            ],
            "get_counter_series": [
                {"bucket_date": date(2026, 1, 1).isoformat(), "count": 4},
                {"bucket_date": date(2026, 1, 2).isoformat(), "count": 6},
            ],
        }
    )
    monkeypatch.setattr(main_module, "get_client", lambda: stub_get_client_factory(client))

    response = TestClient(app).get("/count/dotfiles/series?start=2026-01-01&end=2026-01-31")

    assert response.status_code == 200
    assert response.json() == {
        "counter_id": "dotfiles",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "total_count": 10,
        "points": [
            {"bucket_date": "2026-01-01", "count": 4},
            {"bucket_date": "2026-01-02", "count": 6},
        ],
    }
    assert client.rpc_calls == [
        ("get_counter_summary", {"counter_name": "dotfiles"}),
        (
            "get_counter_series",
            {
                "counter_name": "dotfiles",
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 1, 31),
            },
        ),
    ]
