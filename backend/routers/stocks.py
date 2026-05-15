import asyncio
from fastapi import APIRouter, Query, HTTPException
from services.data_fetcher import search_stocks, get_current_price

router = APIRouter()


@router.get("/search")
async def search(q: str = Query(..., min_length=1), market: str = Query("KR")):
    market_upper = market.upper()
    if market_upper not in {"KR", "US"}:
        raise HTTPException(status_code=400, detail="market은 KR 또는 US만 허용됩니다")

    results = await asyncio.to_thread(search_stocks, q, market_upper)

    if not results:
        return {"results": []}

    semaphore = asyncio.Semaphore(3)

    async def _fetch_with_limit(ticker: str, market: str) -> float:
        async with semaphore:
            return await asyncio.to_thread(get_current_price, ticker, market)

    prices = await asyncio.gather(
        *[_fetch_with_limit(r["ticker"], r["market"]) for r in results]
    )

    enriched = [
        {"ticker": r["ticker"], "name": r["name"], "market": r["market"], "current_price": p}
        for r, p in zip(results, prices)
    ]
    return {"results": enriched}
