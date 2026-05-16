import feedparser
import logging
from datetime import datetime, timezone, timedelta
from collections import Counter
import re

logger = logging.getLogger(__name__)

POSITIVE_KR = [
    "상승", "급등", "호실적", "매수", "성장", "흑자", "최고", "돌파", "기대", "호재",
    "상향", "개선", "회복", "강세", "수익", "증가", "반등", "신고가", "확대", "수주",
    "호황", "개발", "출시", "협력", "계약", "투자", "긍정", "전망", "낙관", "견조",
]
NEGATIVE_KR = [
    "하락", "급락", "적자", "매도", "위기", "손실", "최저", "우려", "악재", "하향",
    "부진", "약세", "폭락", "매각", "감소", "손해", "리콜", "제재", "소송", "파산",
    "침체", "둔화", "충격", "불안", "혼란", "경고", "취소", "중단", "포기",
]
POSITIVE_EN = [
    "rise", "surge", "beat", "growth", "profit", "upgrade", "strong", "bull",
    "rally", "gain", "record", "soar", "jump", "boost", "outperform", "exceed",
    "expand", "launch", "partnership", "deal", "invest", "optimistic", "recover",
    "positive", "high", "up", "buy", "reward", "dividend", "innovation",
]
NEGATIVE_EN = [
    "fall", "drop", "miss", "loss", "concern", "downgrade", "weak", "bear",
    "decline", "risk", "crash", "cut", "recall", "sanction", "lawsuit", "bankrupt",
    "slowdown", "shock", "anxiety", "chaos", "warning", "cancel", "halt", "layoff",
    "negative", "low", "sell", "penalty", "fine", "investigation",
]


def _classify_sentiment(title: str) -> str:
    title_lower = title.lower()
    pos = sum(1 for w in POSITIVE_KR + POSITIVE_EN if w in title_lower)
    neg = sum(1 for w in NEGATIVE_KR + NEGATIVE_EN if w in title_lower)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def _parse_published(entry) -> str:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def _extract_keywords(news_list: list[dict]) -> list[dict]:
    all_text = " ".join(n["title"] for n in news_list)
    # 한글 단어 (2글자 이상) + 영문 단어 (3글자 이상)
    words = re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", all_text)
    stop_words = {"있는", "없는", "하는", "위한", "통해", "따른", "및", "이후", "관련", "대한", "the", "and", "for", "that", "with"}
    words = [w for w in words if w not in stop_words]

    counter = Counter(words)
    keywords = []
    for word, count in counter.most_common(20):
        # 감성 판단
        word_lower = word.lower()
        if any(p in word_lower for p in POSITIVE_KR + POSITIVE_EN):
            sentiment = "positive"
        elif any(n in word_lower for n in NEGATIVE_KR + NEGATIVE_EN):
            sentiment = "negative"
        else:
            sentiment = "neutral"
        keywords.append({"text": word, "value": count, "sentiment": sentiment})

    return keywords


_DEDUP_STOP = {
    "있는", "없는", "하는", "위한", "통해", "따른", "및", "이후", "관련", "대한",
    "the", "and", "for", "that", "with", "this", "from", "are", "was", "its",
    "에서", "으로", "에도", "한다", "된다", "이다", "에게", "까지", "부터",
    "속보", "단독", "종합", "업데이트", "breaking", "exclusive", "update",
}


def _title_tokens(title: str) -> frozenset[str]:
    """제목에서 불용어를 제거한 전체 단어 집합."""
    words = re.findall(r"[가-힣]{2,}|[a-zA-Z0-9]{2,}", title)
    return frozenset(w.lower() for w in words if w.lower() not in _DEDUP_STOP)


def _entity_tokens(title: str) -> frozenset[str]:
    """고유명사·숫자 중심 핵심 토큰 (대소문자 유지, 숫자 포함)."""
    # 영문 대문자 시작 단어, 한글 고유명사(2자 이상), 숫자+단위
    entities = re.findall(r"[A-Z][A-Za-z0-9]+|[가-힣]{2,}|[0-9]+[%·조억만원$]?", title)
    stop_en = {"The", "For", "With", "From", "This", "That", "After", "As"}
    return frozenset(e for e in entities if e not in stop_en and len(e) >= 2)


def _is_duplicate(a: str, b: str) -> bool:
    """두 제목이 내용상 중복인지 판별한다."""
    ta, tb = _title_tokens(a), _title_tokens(b)
    ea, eb = _entity_tokens(a), _entity_tokens(b)

    # 1) 전체 단어 Jaccard 0.4 이상
    union_all = len(ta | tb)
    if union_all > 0 and len(ta & tb) / union_all >= 0.4:
        return True

    # 2) 핵심 엔티티 2개 이상 공유 (단, 각 제목에 엔티티가 2개 이상 있을 때만)
    if len(ea) >= 2 and len(eb) >= 2 and len(ea & eb) >= 2:
        return True

    return False


def _dedup_news(news_list: list[dict]) -> list[dict]:
    """내용상 중복 기사를 제거한다."""
    kept: list[dict] = []
    for item in news_list:
        title = item["title"]
        if not any(_is_duplicate(title, k["title"]) for k in kept):
            kept.append(item)
    return kept


_ETF_SECTOR_QUERY_KR: dict[str, str] = {
    "반도체": "반도체 시장",
    "2차전지": "2차전지 배터리",
    "전기차": "전기차 EV",
    "바이오": "바이오 헬스케어",
    "IT": "IT 기술주",
    "금융": "금융 은행",
    "에너지": "에너지 원자재",
    "부동산": "부동산 리츠",
    "미국": "미국 증시",
    "중국": "중국 증시",
    "인도": "인도 증시",
    "채권": "채권 금리",
}

_ETF_SECTOR_QUERY_US: dict[str, str] = {
    "Technology": "technology sector stocks",
    "Healthcare": "healthcare sector stocks",
    "Financials": "financial sector stocks",
    "Energy": "energy sector stocks",
    "Consumer": "consumer sector stocks",
    "Real Estate": "real estate REIT",
    "Industrials": "industrials sector",
    "Materials": "materials commodities",
    "Utilities": "utilities sector",
    "Communication": "communication services",
    "Bond": "bond market interest rate",
    "Dividend": "dividend stocks",
}


def _etf_search_query(name: str, sector: str, market: str) -> str:
    """ETF 이름/섹터에서 검색용 키워드를 추론한다."""
    if market == "KR":
        for keyword, query in _ETF_SECTOR_QUERY_KR.items():
            if keyword in name or keyword in sector:
                return query
        # 이름에서 브랜드(TIGER/KODEX 등) 제거 후 핵심 단어 추출
        core = re.sub(r'(TIGER|KODEX|KINDEX|ARIRANG|HANARO|ACE)\s*', '', name, flags=re.IGNORECASE).strip()
        return f"{core} 시장" if core else "국내 증시"
    else:
        for keyword, query in _ETF_SECTOR_QUERY_US.items():
            if keyword.lower() in sector.lower() or keyword.lower() in name.lower():
                return query
        # sector 값이 있으면 그대로 사용
        if sector:
            return f"{sector} sector market"
        return "stock market ETF"


def _filter_recent(news_list: list[dict], days: int = 7) -> list[dict]:
    """days일 이내 뉴스만 반환한다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for n in news_list:
        try:
            pub = datetime.fromisoformat(n["published"].replace("Z", "+00:00"))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff:
                result.append(n)
        except Exception:
            result.append(n)
    return result


def collect_news_and_score(ticker: str, name: str, market: str,
                           quote_type: str = "EQUITY", sector: str = "") -> dict:
    news_list = []
    is_etf = quote_type == "ETF"

    if market == "KR":
        if is_etf:
            # ETF는 종목 RSS 대신 관련 분야 구글 뉴스 검색
            try:
                import urllib.parse
                query = _etf_search_query(name, sector, "KR")
                encoded = urllib.parse.quote(query)
                feed = feedparser.parse(
                    f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
                )
                for entry in feed.entries[:15]:
                    news_list.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": _parse_published(entry),
                        "source": "Google뉴스",
                    })
            except Exception:
                logger.exception("KR ETF Google 뉴스 수집 실패: %s", name)
        else:
            try:
                feed = feedparser.parse(f"https://finance.naver.com/item/rss.naver?code={ticker}")
                for entry in feed.entries[:15]:
                    news_list.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": _parse_published(entry),
                        "source": (entry.get("source") or {}).get("title", "네이버금융"),
                    })
            except Exception:
                logger.exception("네이버금융 RSS 수집 실패: %s", ticker)

            # 보조: 구글 뉴스 RSS (종목명 검색)
            if not news_list:
                try:
                    import urllib.parse
                    encoded = urllib.parse.quote(name)
                    feed2 = feedparser.parse(
                        f"https://news.google.com/rss/search?q={encoded}+주식&hl=ko&gl=KR&ceid=KR:ko"
                    )
                    for entry in feed2.entries[:10]:
                        news_list.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "published": _parse_published(entry),
                            "source": "Google뉴스",
                        })
                except Exception:
                    logger.exception("Google 뉴스 RSS 수집 실패: %s", name)

    else:
        if is_etf:
            # ETF는 섹터/카테고리 키워드로 구글 뉴스 검색
            try:
                import urllib.parse
                query = _etf_search_query(name, sector, "US")
                encoded = urllib.parse.quote(query)
                feed = feedparser.parse(
                    f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"
                )
                for entry in feed.entries[:15]:
                    news_list.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": _parse_published(entry),
                        "source": "Google News",
                    })
            except Exception:
                logger.exception("US ETF Google 뉴스 수집 실패: %s", name)
        else:
            try:
                feed = feedparser.parse(
                    f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
                )
                for entry in feed.entries[:15]:
                    news_list.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": _parse_published(entry),
                        "source": (entry.get("source") or {}).get("title", "Yahoo Finance"),
                    })
            except Exception:
                logger.exception("Yahoo Finance RSS 수집 실패: %s", ticker)

    # 7일 이내 뉴스만 유지 후 내용 중복 제거
    news_list = _filter_recent(news_list, days=7)
    news_list = _dedup_news(news_list)

    # 감성 분류
    sentiments = [_classify_sentiment(n["title"]) for n in news_list]
    total = len(sentiments)

    if total == 0:
        pos_ratio, neu_ratio, neg_ratio = 0.0, 1.0, 0.0
        sentiment_score = 0.0
        news_score = 2.0
        summary = "수집된 뉴스가 없습니다."
        bull_signals = []
        bear_signals = []
    else:
        pos_count = sentiments.count("positive")
        neg_count = sentiments.count("negative")
        neu_count = sentiments.count("neutral")
        pos_ratio = pos_count / total
        neg_ratio = neg_count / total
        neu_ratio = neu_count / total

        # 감성 점수 (최대 10점) — 긍정 비율 + 부정 비율 동시 고려
        if pos_ratio >= 0.5:
            sentiment_score = 10.0
        elif pos_ratio >= 0.3:
            sentiment_score = 8.0
        elif neg_ratio <= 0.1:
            sentiment_score = 6.0   # 긍정은 적지만 부정도 거의 없음
        elif neg_ratio <= 0.2:
            sentiment_score = 4.0
        else:
            sentiment_score = 1.0

        # 뉴스 건수 점수 (최대 10점) — 24시간 이내 기사 수 기준
        now = datetime.now(timezone.utc)
        recent_count = 0
        for n in news_list:
            try:
                pub = datetime.fromisoformat(n["published"].replace("Z", "+00:00"))
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                if (now - pub).total_seconds() < 86400:
                    recent_count += 1
            except Exception:
                pass

        if recent_count >= 5:
            news_score = 10.0
        elif recent_count >= 3:
            news_score = 7.0
        elif recent_count >= 1:
            news_score = 4.0
        else:
            news_score = 1.0

        # 요약 생성
        pos_pct = round(pos_ratio * 100)
        neg_pct = round(neg_ratio * 100)
        neu_pct = round(neu_ratio * 100)
        summary = f"수집된 뉴스 {total}건 중 긍정 {pos_pct}%, 중립 {neu_pct}%, 부정 {neg_pct}%입니다."

        bull_signals = [n["title"][:30] for n, s in zip(news_list, sentiments) if s == "positive"][:3]
        bear_signals = [n["title"][:30] for n, s in zip(news_list, sentiments) if s == "negative"][:3]

    keywords = _extract_keywords(news_list)

    return {
        "sentiment_score": sentiment_score,
        "news_score": news_score,
        "positive_ratio": round(pos_ratio, 3),
        "neutral_ratio": round(neu_ratio, 3),
        "negative_ratio": round(neg_ratio, 3),
        "summary": summary,
        "bull_signals": bull_signals,
        "bear_signals": bear_signals,
        "keywords": keywords,
        "news_list": news_list[:20],
    }
