import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 전역 캐시: Code → {name, market, close, marcap, volume}
_kr_listing_cache: pd.DataFrame = pd.DataFrame()
_kr_etf_codes: set[str] = set()


async def init_stock_cache():
    import asyncio
    try:
        stock_df, etf_df = await asyncio.gather(
            asyncio.to_thread(_fetch_kr_listing),
            asyncio.to_thread(_fetch_kr_etf_listing),
        )
        global _kr_listing_cache, _kr_etf_codes
        _kr_listing_cache = pd.concat([stock_df, etf_df])
        _kr_listing_cache = _kr_listing_cache[~_kr_listing_cache.index.duplicated(keep='last')]
        _kr_etf_codes = set(etf_df.index.tolist())
        logger.info("[cache] KR 주식 %d개 + ETF %d개 로드 완료", len(stock_df), len(etf_df))
    except Exception:
        logger.exception("[cache] 초기화 실패 (빈 캐시로 진행)")


def _fetch_kr_listing() -> pd.DataFrame:
    import FinanceDataReader as fdr
    df = fdr.StockListing('KRX')
    df = df[['Code', 'Name', 'Market', 'Close', 'Volume', 'Marcap']].copy()
    if 'Market' in df.columns:
        df = df[~df['Market'].str.upper().str.contains('ETF', na=False)]
    df['Code'] = df['Code'].astype(str).str.zfill(6)
    df = df.set_index('Code')
    return df


def _fetch_kr_etf_listing() -> pd.DataFrame:
    import FinanceDataReader as fdr
    try:
        df = fdr.StockListing('ETF/KR')
        df = df.copy()
        code_col = 'Symbol' if 'Symbol' in df.columns else 'Code'
        df['Code'] = df[code_col].astype(str).str.zfill(6)
        df = df.set_index('Code')
        # KRX 컬럼과 맞추기
        df['Market'] = 'ETF'
        # Name 컬럼 방어: 실제 컬럼명이 다를 수 있음
        if 'Name' not in df.columns:
            name_candidates = [c for c in df.columns if 'name' in c.lower() or 'nm' in c.lower()]
            df['Name'] = df[name_candidates[0]] if name_candidates else pd.Series('', index=df.index)
        price_col = 'Price' if 'Price' in df.columns else None
        marcap_col = 'MarCap' if 'MarCap' in df.columns else None
        volume_col = 'Volume' if 'Volume' in df.columns else None
        df['Close'] = df[price_col] if price_col else 0
        if marcap_col:
            raw_marcap = pd.to_numeric(df[marcap_col], errors='coerce').fillna(0)
            # FDR ETF/KR의 MarCap 컬럼은 억원 단위로 제공됨 — 최대값 기준 단위 추론
            median_val = raw_marcap[raw_marcap > 0].median() if (raw_marcap > 0).any() else 0
            df['Marcap'] = raw_marcap * 100_000_000 if median_val < 1_000_000_000 else raw_marcap
        else:
            df['Marcap'] = 0
        df['Volume'] = df[volume_col] if volume_col else 0
        return df[['Name', 'Market', 'Close', 'Volume', 'Marcap']]
    except Exception:
        logger.exception("[cache] KR ETF 목록 로드 실패")
        return pd.DataFrame(columns=['Name', 'Market', 'Close', 'Volume', 'Marcap'])


def get_current_price(ticker: str, market: str) -> float:
    if market == "KR":
        global _kr_listing_cache
        if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
            row = _kr_listing_cache.loc[ticker]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            return float(row['Close'] or 0)
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
        name_mask = _kr_listing_cache['Name'].str.contains(query, na=False, regex=False, case=False)
        code_mask = _kr_listing_cache.index.str.contains(query_upper, na=False, regex=False)
        matched = _kr_listing_cache[name_mask | code_mask].head(20)
        results = []
        for code, row in matched.iterrows():
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            results.append({"ticker": str(code), "name": str(row['Name']), "market": "KR"})
        return results
    else:
        try:
            import yfinance as yf
            search = yf.Search(query, max_results=10)
            results = []
            for q in search.quotes:
                symbol = q.get('symbol', '')
                quote_type = (q.get('quoteType') or '').upper()
                name = q.get('longname') or q.get('shortname') or symbol
                if (symbol
                        and quote_type in ('EQUITY', 'ETF')
                        and not symbol.endswith(('.KS', '.KQ', '.KN'))):
                    results.append({"ticker": symbol, "name": name, "market": "US"})
            return results[:10]
        except Exception:
            logger.exception("US 검색 실패: %s", query)
            return []


def get_stock_name(ticker: str, market: str) -> str:
    if market == "KR":
        global _kr_listing_cache
        if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
            row = _kr_listing_cache.loc[ticker]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            return str(row["Name"])
    return ticker


def get_stock_data(ticker: str, market: str) -> dict:
    if market == "KR":
        return _get_kr_stock_data(ticker)
    else:
        return _get_us_stock_data(ticker)


def _is_etf(info: dict) -> bool:
    return (info.get("quoteType") or "").upper() == "ETF"


def _get_kr_stock_data(ticker: str) -> dict:
    import FinanceDataReader as fdr

    global _kr_listing_cache, _kr_etf_codes
    name = ticker
    current_price = 0.0
    market_cap = 0.0
    volume = 0
    kr_market = ""

    if not _kr_listing_cache.empty and ticker in _kr_listing_cache.index:
        row = _kr_listing_cache.loc[ticker]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        name = str(row['Name'])
        current_price = float(row['Close'] or 0)
        market_cap = float(row['Marcap'] or 0)
        volume = int(row['Volume'] or 0)
        kr_market = str(row.get('Market', ''))

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

    is_etf_ticker = ticker in _kr_etf_codes or kr_market == 'ETF'
    if is_etf_ticker:
        return _build_kr_etf_data(ticker, name, history_df, current_price, market_cap, volume, kr_market)

    from services.naver_scraper import fetch_kr_fundamentals
    fundamentals = fetch_kr_fundamentals(ticker)

    return {
        "ticker": ticker,
        "name": name,
        "market": "KR",
        "quote_type": "EQUITY",
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


def _build_kr_etf_data(ticker: str, name: str, history_df, current_price: float, market_cap: float, volume: int, kr_market: str) -> dict:
    from services.naver_etf_scraper import fetch_kr_etf_info
    etf_info = fetch_kr_etf_info(ticker)

    return {
        "ticker": ticker,
        "name": name,
        "market": "KR",
        "quote_type": "ETF",
        "sector": kr_market,
        "industry": "",
        "current_price": current_price,
        "market_cap": market_cap,
        "volume": volume,
        "expense_ratio": etf_info.get("expense_ratio"),
        "dividend_yield": etf_info.get("dividend_yield"),
        "three_year_return": etf_info.get("three_year_return"),
        "per": None,
        "pbr": None,
        "roe": None,
        "eps": None,
        "debt_ratio": None,
        "revenue_growth": None,
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

    current_price = float(info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice') or 0.0)
    market_cap = float(info.get('marketCap') or info.get('totalAssets') or 0.0)
    volume = int(info.get('volume') or 0)

    if _is_etf(info):
        return _build_etf_data(ticker, info, history_df, current_price, market_cap, volume)

    per = info.get('trailingPE') or info.get('forwardPE')
    pbr = info.get('priceToBook')

    roe_raw = info.get('returnOnEquity')
    roe = roe_raw * 100 if roe_raw is not None else None

    eps = info.get('trailingEps')

    rev_raw = info.get('revenueGrowth')
    revenue_growth = rev_raw * 100 if rev_raw is not None else None

    total_debt = info.get('totalDebt') or 0
    total_equity_raw = info.get('totalStockholdersEquity')
    if total_equity_raw is None:
        debt_ratio = None
    elif total_equity_raw <= 0:
        debt_ratio = 9999.0  # 자본잠식 — 최악 패널티
    else:
        debt_ratio = total_debt / total_equity_raw * 100

    return {
        "ticker": ticker.upper(),
        "name": info.get('longName') or info.get('shortName', ticker.upper()),
        "market": "US",
        "quote_type": "EQUITY",
        "sector": info.get('sector') or "",
        "industry": info.get('industry') or "",
        "current_price": current_price,
        "market_cap": market_cap,
        "volume": volume,
        "per": float(per) if per else None,
        "pbr": float(pbr) if pbr else None,
        "roe": float(roe) if roe is not None else None,
        "eps": float(eps) if eps else None,
        "debt_ratio": float(debt_ratio) if debt_ratio is not None else None,
        "revenue_growth": float(revenue_growth) if revenue_growth is not None else None,
        "history": history_df,
    }


def _build_etf_data(ticker: str, info: dict, history_df, current_price: float, market_cap: float, volume: int) -> dict:
    expense_raw = info.get('annualReportExpenseRatio') or info.get('expenseRatio')
    expense_ratio = float(expense_raw) * 100 if expense_raw is not None else None

    div_raw = info.get('trailingAnnualDividendYield') or info.get('dividendYield')
    dividend_yield = float(div_raw) * 100 if div_raw is not None else None
    if dividend_yield is not None and dividend_yield > 30:
        dividend_yield /= 100

    three_yr_raw = info.get('threeYearAverageReturn')
    three_year_return = float(three_yr_raw) * 100 if three_yr_raw is not None else None

    return {
        "ticker": ticker.upper(),
        "name": info.get('longName') or info.get('shortName', ticker.upper()),
        "market": "US",
        "quote_type": "ETF",
        "sector": info.get('category') or "",
        "industry": "",
        "current_price": current_price,
        "market_cap": market_cap,
        "volume": volume,
        "expense_ratio": expense_ratio,
        "dividend_yield": dividend_yield,
        "three_year_return": three_year_return,
        # ETF는 개별 재무지표 없음
        "per": None,
        "pbr": None,
        "roe": None,
        "eps": None,
        "debt_ratio": None,
        "revenue_growth": None,
        "history": history_df,
    }
