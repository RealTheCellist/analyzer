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


def collect_news_and_score(ticker: str, name: str, market: str) -> dict:
    news_list = []

    if market == "KR":
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
                feed2 = feedparser.parse(f"https://news.google.com/rss/search?q={encoded}+주식&hl=ko&gl=KR&ceid=KR:ko")
                for entry in feed2.entries[:10]:
                    title = entry.get("title", "")
                    news_list.append({
                        "title": title,
                        "link": entry.get("link", ""),
                        "published": _parse_published(entry),
                        "source": "Google뉴스",
                    })
            except Exception:
                logger.exception("Google 뉴스 RSS 수집 실패: %s", name)

    else:
        try:
            feed = feedparser.parse(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US")
            for entry in feed.entries[:15]:
                news_list.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": _parse_published(entry),
                    "source": (entry.get("source") or {}).get("title", "Yahoo Finance"),
                })
        except Exception:
            logger.exception("Yahoo Finance RSS 수집 실패: %s", ticker)

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
