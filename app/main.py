import os
from datetime import date, datetime
from typing import Annotated, Any, cast

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel

from supabase import AsyncClient, acreate_client

app = FastAPI(title="counterhub")

CounterPath = Annotated[str, Path(min_length=1)]
DateQuery = Annotated[date | None, Query()]


async def get_client() -> AsyncClient:
    return await acreate_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


class CounterIncrementResult(BaseModel):
    counter_id: str
    total_count: int
    today_count: int
    updated_at: datetime


class CounterSummary(BaseModel):
    counter_id: str
    total_count: int
    last_updated_at: datetime | None = None
    first_bucket_date: date | None = None
    last_bucket_date: date | None = None


class CounterSeriesPoint(BaseModel):
    bucket_date: date
    count: int


class CounterSeries(BaseModel):
    counter_id: str
    start_date: date | None = None
    end_date: date | None = None
    total_count: int
    points: list[CounterSeriesPoint]


def _first_row(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        if not data:
            return None
        return cast(dict[str, Any], data[0])
    if isinstance(data, dict):
        return cast(dict[str, Any], data)
    return None


def _rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [cast(dict[str, Any], row) for row in data]
    if isinstance(data, dict):
        return [cast(dict[str, Any], data)]
    return []


@app.get("/")
async def root() -> dict[str, str]:
    try:
        client = await get_client()
        await client.table("counters").select("id").limit(1).execute()
        db = "ok"
    except Exception:
        db = "unreachable"
    return {"status": "ok", "db": db}


@app.post("/count/{counter_id}")
async def increment_counter(counter_id: CounterPath) -> CounterIncrementResult:
    client = await get_client()
    result = await client.rpc("increment_counter", {"counter_name": counter_id}).execute()
    row = _first_row(result.data)

    if row is None:
        raise HTTPException(status_code=404, detail="counter not found")

    return CounterIncrementResult.model_validate(row)


@app.get("/count/{counter_id}")
async def get_counter(counter_id: CounterPath) -> CounterSummary:
    client = await get_client()
    result = await client.rpc("get_counter_summary", {"counter_name": counter_id}).execute()
    row = _first_row(result.data)

    if row is None:
        raise HTTPException(status_code=404, detail="counter not found")

    return CounterSummary.model_validate(row)


@app.get("/count/{counter_id}/series")
async def get_counter_series(
    counter_id: CounterPath,
    start: DateQuery = None,
    end: DateQuery = None,
) -> CounterSeries:
    client = await get_client()
    summary_result = await client.rpc("get_counter_summary", {"counter_name": counter_id}).execute()
    summary_row = _first_row(summary_result.data)

    if summary_row is None:
        raise HTTPException(status_code=404, detail="counter not found")

    result = await client.rpc(
        "get_counter_series",
        {"counter_name": counter_id, "start_date": start, "end_date": end},
    ).execute()
    points = [CounterSeriesPoint.model_validate(row) for row in _rows(result.data)]

    return CounterSeries(
        counter_id=counter_id,
        start_date=start,
        end_date=end,
        total_count=sum(point.count for point in points),
        points=points,
    )
