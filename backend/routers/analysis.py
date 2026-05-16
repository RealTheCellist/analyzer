import asyncio
import re
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone, timedelta

from services.data_fetcher import get_stock_data
from services.fundamental import calculate_fundamental_score
from services.etf_scorer import calculate_etf_score
from services.technical import calculate_technical_score
from services.news_service import collect_news_and_score
from services.ai_judge import get_ai_judgment

router = APIRouter()
logger = logging.getLogger(__name__)

_TICKER_RE = re.compile(r'^[A-Z0-9.\-]{1,20}$')
_CACHE_TTL = timedelta(minutes=30)

# 캐시: (ticker, market) → (result, cached_at)
_cache: dict[tuple, tuple] = {}


def _get_cached(ticker: str, market: str) -> dict | None:
    key = (ticker, market)
    if key not in _cache:
        return None
    result, cached_at = _cache[key]
    if datetime.now(timezone.utc) - cached_at > _CACHE_TTL:
        del _cache[key]
        return None
    return result


def _set_cache(ticker: str, market: str, result: dict):
    _cache[(ticker, market)] = (result, datetime.now(timezone.utc))


class AnalysisRequest(BaseModel):
    ticker: str
    market: str
    force_refresh: bool = False

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not _TICKER_RE.match(v):
            raise ValueError("유효하지 않은 티커 형식 (영문/숫자/.-만 허용, 최대 20자)")
        return v

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in {"KR", "US"}:
            raise ValueError("market은 KR 또는 US만 허용됩니다")
        return v_upper


@router.post("/run")
async def run_analysis(req: AnalysisRequest):
    ticker = req.ticker
    market = req.market

    if not req.force_refresh:
        cached = _get_cached(ticker, market)
        if cached:
            logger.info("[cache hit] %s %s", ticker, market)
            return cached

    try:
        stock_data = await asyncio.to_thread(get_stock_data, ticker, market)
    except Exception as e:
        logger.exception("종목 데이터 조회 실패: %s %s", ticker, market)
        raise HTTPException(status_code=404, detail=f"종목 데이터 조회 실패: {e}")

    is_etf = stock_data.get("quote_type") == "ETF"
    score_fn = calculate_etf_score if is_etf else calculate_fundamental_score

    fundamental, technical, news = await asyncio.gather(
        asyncio.to_thread(score_fn, stock_data),
        asyncio.to_thread(calculate_technical_score, stock_data.get("history")),
        asyncio.to_thread(collect_news_and_score, ticker, stock_data["name"], market),
    )
    ai = await get_ai_judgment(stock_data, fundamental, technical, news)

    total_score = round(
        fundamental["score"]
        + technical["score"]
        + news["sentiment_score"]
        + news["news_score"]
        + ai["score"],
        2,
    )

    if total_score >= 75:
        verdict = "STRONG_BUY"
        recommendation = "강력매수"
    elif total_score >= 65:
        verdict = "QUALIFIED"
        recommendation = "매수"
    elif total_score >= 50:
        verdict = "WATCHLIST"
        recommendation = "분할매수"
    else:
        verdict = "DISQUALIFIED"
        recommendation = "관망"

    result = {
        "ticker": stock_data["ticker"],
        "name": stock_data["name"],
        "market": stock_data["market"],
        "quote_type": stock_data.get("quote_type", "EQUITY"),
        "current_price": stock_data["current_price"],
        "market_cap": stock_data["market_cap"],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "total_score": total_score,
        "verdict": verdict,
        "recommendation": recommendation,
        "cached": False,
        "breakdown": {
            "fundamental": fundamental,
            "technical": technical,
            "sentiment": {
                "sentiment_score": news["sentiment_score"],
                "news_score": news["news_score"],
                "positive_ratio": news["positive_ratio"],
                "neutral_ratio": news["neutral_ratio"],
                "negative_ratio": news["negative_ratio"],
                "summary": news["summary"],
                "bull_signals": news["bull_signals"],
                "bear_signals": news["bear_signals"],
                "keywords": news["keywords"],
            },
            "ai": ai,
        },
        "news": news["news_list"],
    }

    _set_cache(ticker, market, {**result, "cached": True})
    return result


@router.get("/cache/status")
async def cache_status():
    now = datetime.now(timezone.utc)
    entries = [
        {
            "ticker": k[0],
            "market": k[1],
            "cached_at": v[1].isoformat(),
            "expires_in_sec": max(0, int((_CACHE_TTL - (now - v[1])).total_seconds())),
        }
        for k, v in _cache.items()
    ]
    return {"count": len(entries), "ttl_minutes": 30, "entries": entries}


@router.delete("/cache/clear")
async def cache_clear():
    _cache.clear()
    return {"message": "캐시 초기화 완료"}
