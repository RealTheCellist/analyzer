import asyncio
import re
from fastapi import APIRouter, Query, HTTPException
from services.news_service import collect_news_and_score
from services.data_fetcher import get_stock_name

router = APIRouter()

_TICKER_RE = re.compile(r'^[A-Z0-9.\-]{1,20}$')


@router.get("/{ticker}")
async def get_news(ticker: str, market: str = Query("KR")):
    market_upper = market.upper()
    if market_upper not in {"KR", "US"}:
        raise HTTPException(status_code=400, detail="market은 KR 또는 US만 허용됩니다")
    if not _TICKER_RE.match(ticker.strip().upper()):
        raise HTTPException(status_code=400, detail="유효하지 않은 티커 형식")
    name = get_stock_name(ticker.strip().upper(), market_upper)
    result = await asyncio.to_thread(collect_news_and_score, ticker.strip().upper(), name, market_upper)
    return result
