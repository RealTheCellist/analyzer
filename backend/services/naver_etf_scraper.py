"""
네이버 금융 ETF 페이지에서 KR ETF 지표 스크래핑.
운용보수, 분배율(배당), 3년 수익률 제공.
"""

import re
import logging
import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.naver.com/",
}


def fetch_kr_etf_info(ticker: str) -> dict:
    result = {
        "expense_ratio": None,
        "dividend_yield": None,
        "three_year_return": None,
    }

    try:
        resp = requests.get(
            f"https://finance.naver.com/fund/etfItemDetail.naver?etfNo={ticker}",
            headers=_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        html = resp.content.decode("cp949", errors="ignore")
    except Exception as e:
        logger.warning("네이버 ETF 페이지 요청 실패 %s: %s", ticker, e)
        return result

    # 운용보수 (총보수) — "총보수" 레이블 근방 숫자%
    expense_m = re.search(r'총\s*보\s*수[^0-9]*?([\d.]+)\s*%', html)
    if expense_m:
        result["expense_ratio"] = _parse_float(expense_m.group(1))

    # 분배율 — "분배금수익률" 또는 "배당수익률" 근방
    div_m = re.search(r'분배금수익률[^0-9\-]*?([\d.\-]+)\s*%', html)
    if not div_m:
        div_m = re.search(r'배당수익률[^0-9\-]*?([\d.\-]+)\s*%', html)
    if div_m:
        result["dividend_yield"] = _parse_float(div_m.group(1))

    # 3년 수익률 — "3년" 수익률 근방
    ret3_m = re.search(r'3\s*년[^0-9\-]*?([\d.\-]+)\s*%', html)
    if ret3_m:
        result["three_year_return"] = _parse_float(ret3_m.group(1))

    # 스크래핑 실패 시 네이버 금융 종목 메인 페이지 보조 시도
    if all(v is None for v in result.values()):
        result = _fallback_naver_main(ticker, result)

    return result


def _fallback_naver_main(ticker: str, result: dict) -> dict:
    """네이버 금융 종목 메인 페이지에서 ETF 보조 정보 조회"""
    try:
        resp = requests.get(
            f"https://finance.naver.com/item/main.naver?code={ticker}",
            headers=_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        html = resp.content.decode("cp949", errors="ignore")

        # 총보수 재시도
        if result["expense_ratio"] is None:
            m = re.search(r'총보수[^0-9]*([\d.]+)\s*%', html)
            if m:
                result["expense_ratio"] = _parse_float(m.group(1))

        # 3년 수익률 재시도
        if result["three_year_return"] is None:
            m = re.search(r'3년[^0-9\-]*([\d.\-]+)', html)
            if m:
                result["three_year_return"] = _parse_float(m.group(1))
    except Exception as e:
        logger.warning("네이버 메인 보조 조회 실패 %s: %s", ticker, e)

    return result


def _parse_float(s: str) -> float | None:
    try:
        return float(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None
