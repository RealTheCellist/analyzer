import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 전역 캐시: Code → {name, market, close, marcap, volume}
_kr_listing_cache: pd.DataFrame = pd.DataFrame()


async def init_stock_cache():
    import asyncio
    try:
        df = await asyncio.to_thread(_fetch_kr_listing)
        global _kr_listing_cache
        _kr_listing_cache = df
        logger.info("[cache] KR 종목 %d개 로드 완료", len(df))
    except Exception:
        logger.exception("[cache] 초기화 실패 (빈 캐시로 진행)")


def _fetch_kr_listing() -> pd.DataFrame:
    import FinanceDataReader as fdr
    df = fdr.StockListing('KRX')
    df = df[['Code', 'Name', 'Market', 'Close', 'Volume', 'Marcap']].copy()
    df['Code'] = df['Code'].astype(str).str.zfill(6)
    df = df.set_index('Code')
    return df


def get_current_price(ticker: str, market: str) -> float:
    if market == "KR":
        global _kr_listing_cache
        if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
            return float(_kr_listing_cache.loc[ticker, 'Close'] or 0)
        # 캐시 미스 시 FDR 직접 조회
        try:
            import FinanceDataReader as fdr
            today = datetime.now().strftime('%Y-%m-%d')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            df = fdr.DataReader(ticker, week_ago, today)
            if not df.empty:
                return float(df['Close'].iloc[-1])
        except Exception:
            logger.exception("KR 현재가 조회 실패: %s", ticker)
        return 0.0
    else:
        try:
            import yfinance as yf
            info = yf.Ticker(ticker.upper()).fast_info
            return float(getattr(info, 'last_price', 0) or 0)
        except Exception:
            logger.exception("US 현재가 조회 실패: %s", ticker)
            return 0.0


def search_stocks(query: str, market: str) -> list[dict]:
    if market == "KR":
        global _kr_listing_cache
        if _kr_listing_cache.empty:
            return []
        query_upper = query.upper()
        name_mask = _kr_listing_cache['Name'].str.contains(query, na=False, regex=False)
        code_mask = _kr_listing_cache.index.str.contains(query_upper, na=False, regex=False)
        matched = _kr_listing_cache[name_mask | code_mask].head(20)
        return [
            {"ticker": str(code), "name": str(row['Name']), "market": "KR"}
            for code, row in matched.iterrows()
        ]
    else:
        try:
            import yfinance as yf
            search = yf.Search(query, max_results=10)
            results = []
            for q in search.quotes:
                symbol = q.get('symbol', '')
                name = q.get('longname') or q.get('shortname') or symbol
                if symbol:
                    results.append({"ticker": symbol, "name": name, "market": "US"})
            return results[:10]
        except Exception:
            logger.exception("US 검색 실패: %s", query)
            return []


def get_stock_name(ticker: str, market: str) -> str:
    if market == "KR":
        global _kr_listing_cache
        if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
            return str(_kr_listing_cache.loc[ticker, "Name"])
    return ticker


def get_stock_data(ticker: str, market: str) -> dict:
    if market == "KR":
        return _get_kr_stock_data(ticker)
    else:
        return _get_us_stock_data(ticker)


def _get_kr_stock_data(ticker: str) -> dict:
    import FinanceDataReader as fdr
    from services.naver_scraper import fetch_kr_fundamentals

    global _kr_listing_cache
    name = ticker
    current_price = 0.0
    market_cap = 0.0
    volume = 0

    kr_market = ""
    if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
        row = _kr_listing_cache.loc[ticker]
        name = str(row['Name'])
        current_price = float(row['Close'] or 0)
        market_cap = float(row['Marcap'] or 0)
        volume = int(row['Volume'] or 0)
        kr_market = str(row.get('Market', ''))

    # 가격 히스토리 (기술 분석용); 캐시 미스 시에만 current_price 보정
    try:
        start = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        history_df = fdr.DataReader(ticker, start, end)
        history_df.index = pd.to_datetime(history_df.index)
        if current_price == 0.0 and not history_df.empty:
            current_price = float(history_df['Close'].iloc[-1])
    except Exception:
        logger.exception("KR 가격 히스토리 조회 실패: %s", ticker)
        history_df = pd.DataFrame()

    # 네이버 금융에서 재무지표 스크래핑
    fundamentals = fetch_kr_fundamentals(ticker)

    return {
        "ticker": ticker,
        "name": name,
        "market": "KR",
        "sector": kr_market,
        "industry": "",
        "current_price": current_price,
        "market_cap": market_cap,
        "volume": volume,
        "per": fundamentals["per"],
        "pbr": fundamentals["pbr"],
        "roe": fundamentals["roe"],
        "eps": fundamentals["eps"],
        "debt_ratio": fundamentals["debt_ratio"],
        "revenue_growth": fundamentals["revenue_growth"],
        "history": history_df,
    }


def _get_us_stock_data(ticker: str) -> dict:
    import yfinance as yf

    ticker_obj = yf.Ticker(ticker.upper())
    info = ticker_obj.info

    try:
        history_df = ticker_obj.history(period="6mo")
        history_df.index = pd.to_datetime(history_df.index)
    except Exception:
        logger.exception("US 가격 히스토리 조회 실패: %s", ticker)
        history_df = pd.DataFrame()

    current_price = float(info.get('currentPrice') or info.get('regularMarketPrice') or 0.0)
    market_cap = float(info.get('marketCap') or 0.0)
    volume = int(info.get('volume') or 0)

    per = info.get('trailingPE') or info.get('forwardPE')
    pbr = info.get('priceToBook')
    roe = (info.get('returnOnEquity') or 0) * 100 if info.get('returnOnEquity') else None
    eps = info.get('trailingEps')
    revenue_growth = (info.get('revenueGrowth') or 0) * 100 if info.get('revenueGrowth') else None

    total_debt = info.get('totalDebt') or 0
    total_equity = info.get('totalStockholdersEquity') or 0
    debt_ratio = (total_debt / total_equity * 100) if total_equity > 0 else None

    return {
        "ticker": ticker.upper(),
        "name": info.get('longName') or info.get('shortName', ticker.upper()),
        "market": "US",
        "sector": info.get('sector') or "",
        "industry": info.get('industry') or "",
        "current_price": current_price,
        "market_cap": market_cap,
        "volume": volume,
        "per": float(per) if per else None,
        "pbr": float(pbr) if pbr else None,
        "roe": float(roe) if roe else None,
        "eps": float(eps) if eps else None,
        "debt_ratio": float(debt_ratio) if debt_ratio else None,
        "revenue_growth": float(revenue_growth) if revenue_growth else None,
        "history": history_df,
    }
