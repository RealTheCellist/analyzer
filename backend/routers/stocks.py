import asyncio
from fastapi import APIRouter, Query, HTTPException
from services.data_fetcher import search_stocks, get_current_price

router = APIRouter()


async def _enrich(results: list[dict]) -> list[dict]:
    if not results:
        return []
    semaphore = asyncio.Semaphore(5)

    async def _fetch(ticker: str, market: str) -> float:
        async with semaphore:
            return await asyncio.to_thread(get_current_price, ticker, market)

    prices = await asyncio.gather(*[_fetch(r["ticker"], r["market"]) for r in results])
    return [
        {"ticker": r["ticker"], "name": r["name"], "market": r["market"], "current_price": p}
        for r, p in zip(results, prices)
    ]


@router.get("/search")
async def search(q: str = Query(..., min_length=1), market: str = Query("ALL")):
    market_upper = market.upper()
    if market_upper not in {"KR", "US", "ALL"}:
        raise HTTPException(status_code=400, detail="market은 KR, US, ALL만 허용됩니다")

    if market_upper == "ALL":
        kr_results, us_results = await asyncio.gather(
            asyncio.to_thread(search_stocks, q, "KR"),
            asyncio.to_thread(search_stocks, q, "US"),
        )
        combined = (kr_results + us_results)[:15]
        return {"results": await _enrich(combined)}

    results = await asyncio.to_thread(search_stocks, q, market_upper)
    return {"results": await _enrich(results)}
