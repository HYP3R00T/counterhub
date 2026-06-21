import os
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from supabase import Client, create_client

app = FastAPI(title="counterhub")


def get_client() -> Client:
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


class Counter(BaseModel):
    id: str
    count: int
    updated_at: datetime


def _row(data: list[Any]) -> dict[str, Any]:
    return cast(dict[str, Any], data[0])


@app.get("/")
def root() -> dict[str, str]:
    try:
        get_client().table("counters").select("id").limit(1).execute()
        db = "ok"
    except Exception:
        db = "unreachable"
    return {"status": "ok", "db": db}


@app.post("/counter/{counter_id}/increment")
def increment(counter_id: str) -> Counter:
    client = get_client()
    result = client.table("counters").select("*").eq("id", counter_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="counter not found")

    now = datetime.now(UTC).isoformat()
    row = _row(result.data)
    updated = (
        client
        .table("counters")
        .update({"count": int(row["count"]) + 1, "updated_at": now})
        .eq("id", counter_id)
        .execute()
    )
    row = _row(updated.data)
    return Counter(id=str(row["id"]), count=int(row["count"]), updated_at=row["updated_at"])


@app.get("/counter/{counter_id}")
def get_counter(counter_id: str) -> Counter:
    client = get_client()
    result = client.table("counters").select("*").eq("id", counter_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="counter not found")

    row = _row(result.data)
    return Counter(id=str(row["id"]), count=int(row["count"]), updated_at=row["updated_at"])
