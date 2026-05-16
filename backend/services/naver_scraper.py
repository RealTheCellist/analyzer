"""
네이버 금융 스크래핑으로 KR 주식 재무지표 수집.
PER, PBR, EPS, ROE 제공 (무료, 인증 불필요).
"""

import re
import logging
import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.naver.com/",
}

def fetch_kr_fundamentals(ticker: str) -> dict:
    """
    네이버 금융 종목 메인 페이지에서 재무지표 스크래핑.
    반환: {per, pbr, eps, roe, debt_ratio, revenue_growth} — 없으면 None
    """
    result: dict = {
        "per": None,
        "pbr": None,
        "eps": None,
        "roe": None,
        "debt_ratio": None,
        "revenue_growth": None,
    }

    try:
        resp = requests.get(
            f"https://finance.naver.com/item/main.naver?code={ticker}",
            headers=_HEADERS,
            timeout=8,
            verify=True,
        )
        resp.raise_for_status()
        # 네이버 금융은 EUC-KR 또는 CP949
        html = resp.content.decode("cp949", errors="ignore")
    except requests.exceptions.SSLError as e:
        logger.warning("네이버 금융 SSL 오류 %s: %s", ticker, e)
        return result
    except requests.exceptions.HTTPError as e:
        logger.warning("네이버 금융 HTTP 오류 %s: %s", ticker, e)
        return result
    except Exception as e:
        logger.warning("네이버 금융 요청 실패 %s: %s", ticker, e)
        return result

    # PER, PBR, EPS — id 속성으로 정확히 추출
    for field, id_name in [("per", "_per"), ("pbr", "_pbr"), ("eps", "_eps")]:
        m = re.search(rf'id="{id_name}"[^>]*>([\d.,]+)', html)
        if m:
            result[field] = _parse_float(m.group(1))

    # ROE — cop_anal13 섹션만 먼저 잘라낸 뒤 첫 번째 td 탐색
    section_m = re.search(r'cop_anal13[^>]*>(.*?)</tr>', html, re.DOTALL)
    if section_m:
        roe_m = re.search(r'<td[^>]*>\s*([\d.\-]+)', section_m.group(1))
        if roe_m:
            result["roe"] = _parse_float(roe_m.group(1))

    # 부채비율 — cop_anal15 섹션만 먼저 잘라낸 뒤 첫 번째 td 탐색
    section_m = re.search(r'cop_anal15[^>]*>(.*?)</tr>', html, re.DOTALL)
    if section_m:
        debt_m = re.search(r'<td[^>]*>\s*([\d.\-]+)', section_m.group(1))
        if debt_m:
            result["debt_ratio"] = _parse_float(debt_m.group(1))

    # 매출성장률 — cop_anal9 또는 cop_anal10 섹션만 먼저 잘라낸 뒤 첫 번째 td 탐색
    section_m = re.search(r'cop_anal(?:9|10)[^>]*>(.*?)</tr>', html, re.DOTALL)
    if section_m:
        rev_m = re.search(r'<td[^>]*>\s*([\d.\-]+)', section_m.group(1))
        if rev_m:
            result["revenue_growth"] = _parse_float(rev_m.group(1))

    return result


def _parse_float(s: str) -> float | None:
    try:
        return float(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None
