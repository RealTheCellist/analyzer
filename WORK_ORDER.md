# 주식 투자 적합도 분석 앱 — 작업지시서

> 대상 모델: Qwen3-coder-next  
> 작성일: 2026-05-14  
> 목적: 비용 0원으로 국내/미국 주식의 투자 적합도를 0~100점으로 분석·시각화하는 웹 앱 제작

---

## 1. 프로젝트 개요

### 핵심 목표
- 종목 검색 → 다차원 분석 → **0~100점 투자 적합도 점수** + **적격/부적격 판정** 표시
- 최신 뉴스 종합 제공 (감성 분석 포함)
- 레이더 차트, 게이지, 버블 차트로 **입체적 시각화**

### 판정 기준
- **80점 이상** → 투자 적격 (녹색)
- **80점 미만** → 투자 부적격 (빨간색)

### 점수 가중치
| 영역 | 비중 | 최대 점수 |
|------|------|----------|
| 재무제표 분석 | 20% | 20점 |
| 기술적 분석 | 20% | 20점 |
| 뉴스/감성 분석 | 10% | 10점 |
| Gemini AI 종합 판단 | 50% | 50점 |

---

## 2. 기술 스택

### Backend
- **Python 3.11+**
- **FastAPI** — REST API 서버
- **yfinance** — 미국 주식 시세/재무 데이터
- **pykrx** — 국내 주식 시세 데이터 (무료, KRX 공식)
- **pandas** — 데이터 처리
- **pandas-ta** — 기술적 지표 계산 (ta-lib 대체, 설치 불필요)
- **feedparser** — RSS 뉴스 파싱
- **httpx** — 비동기 HTTP 클라이언트
- **google-generativeai** — Gemini API SDK
- **python-dotenv** — 환경변수 관리

### Frontend
- **React 18 + TypeScript**
- **Vite** — 빌드 도구
- **Recharts** — 레이더 차트, 막대 차트, 라인 차트
- **react-circular-progressbar** — 반원 게이지
- **@visx/wordcloud** — 감성 버블/워드클라우드
- **Tailwind CSS** — 스타일링
- **axios** — API 호출
- **react-query (@tanstack/react-query)** — 서버 상태 관리

---

## 3. 프로젝트 디렉토리 구조

```
stock-analyzer/
├── backend/
│   ├── main.py
│   ├── .env                        # GEMINI_API_KEY=xxx
│   ├── requirements.txt
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── stocks.py               # 종목 검색, 시세
│   │   ├── analysis.py             # 분석 실행
│   │   └── news.py                 # 뉴스 수집
│   └── services/
│       ├── __init__.py
│       ├── data_fetcher.py         # yfinance + pykrx 통합 래퍼
│       ├── fundamental.py          # 재무 지표 계산
│       ├── technical.py            # 기술적 지표 계산
│       ├── news_service.py         # 뉴스 수집 + 감성 점수
│       └── ai_judge.py             # Gemini API 종합 판정
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── stockApi.ts         # axios 인스턴스 + API 함수
        ├── types/
        │   └── index.ts            # TypeScript 타입 정의
        ├── components/
        │   ├── SearchBar.tsx
        │   ├── ScoreGauge.tsx      # 반원 게이지
        │   ├── RadarChart.tsx      # 레이더 차트 (5축)
        │   ├── ScoreBreakdown.tsx  # 영역별 점수 막대
        │   ├── NewsPanel.tsx       # 뉴스 목록 + 요약
        │   ├── SentimentBubble.tsx # 감성 버블 차트
        │   ├── VerdictBadge.tsx    # 적격/부적격 뱃지
        │   └── LoadingSpinner.tsx
        └── pages/
            ├── Home.tsx            # 검색 메인 화면
            └── StockDetail.tsx     # 종목 분석 결과 화면
```

---

## 4. 환경 설정

### 4-1. Backend 환경 설정

**`backend/requirements.txt`**
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
yfinance==0.2.40
pykrx==1.0.45
pandas==2.2.2
pandas-ta==0.3.14b
feedparser==6.0.11
httpx==0.27.0
google-generativeai==0.7.2
python-dotenv==1.0.1
```

**`backend/.env`**
```
GEMINI_API_KEY=여기에_발급받은_API_키_입력
```

**실행 명령어**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4-2. Frontend 환경 설정

**`frontend/package.json` 핵심 의존성**
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "axios": "^1.7.0",
    "@tanstack/react-query": "^5.40.0",
    "recharts": "^2.12.0",
    "react-circular-progressbar": "^2.1.0",
    "@visx/wordcloud": "^3.10.0",
    "@visx/scale": "^3.10.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

**`frontend/vite.config.ts`**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

---

## 5. Backend 상세 구현

### 5-1. `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stocks, analysis, news
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Stock Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api/stocks")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(news.router, prefix="/api/news")
```

---

### 5-2. `backend/services/data_fetcher.py`

**역할:** yfinance(미국)와 pykrx(국내) 데이터를 통일된 형태로 반환

```python
"""
반환 형식 (공통):
{
    "ticker": str,
    "name": str,
    "market": "KR" | "US",
    "current_price": float,
    "market_cap": float,
    "volume": int,
    "per": float | None,
    "pbr": float | None,
    "roe": float | None,
    "eps": float | None,
    "debt_ratio": float | None,
    "revenue_growth": float | None,   # 전년비 매출 성장률 (%)
    "history": pd.DataFrame           # 최근 180일 OHLCV
}
"""

def get_stock_data(ticker: str, market: str) -> dict:
    """
    market == "KR": pykrx로 종목 데이터 조회
    market == "US": yfinance로 종목 데이터 조회
    """
    ...

def search_stocks(query: str, market: str) -> list[dict]:
    """
    종목명 또는 티커로 검색
    KR: pykrx의 stock.get_market_ticker_list() 활용
    US: yfinance.Ticker(query).info 활용
    반환: [{"ticker": ..., "name": ..., "market": ...}]
    """
    ...
```

---

### 5-3. `backend/services/fundamental.py`

**역할:** 재무제표 지표로 0~20점 산출

**구현 로직 (반드시 이 기준으로 구현):**

```python
def calculate_fundamental_score(stock_data: dict) -> dict:
    """
    반환:
    {
        "score": float,          # 0~20점
        "indicators": [
            {
                "name": str,     # 지표명
                "value": float,  # 실제 값
                "benchmark": str,# 기준값 설명
                "pass": bool,    # 합격 여부
                "weight": float  # 이 지표의 배점
            }
        ]
    }
    """

    # 지표별 배점 기준 (합계 20점)
    # PER:          0~15 → 5점, 15~25 → 3점, 25~ → 1점, 없음 → 0점
    # PBR:          0~1  → 5점, 1~3   → 3점, 3~  → 1점, 없음 → 0점
    # ROE:          20%+ → 5점, 10~20% → 3점, 0~10% → 1점, 없음 → 0점
    # 부채비율:     ~100% → 3점, 100~200% → 2점, 200%~ → 0점, 없음 → 0점
    # 매출성장률:   10%+  → 2점, 0~10% → 1점, 0%미만 → 0점, 없음 → 0점
```

---

### 5-4. `backend/services/technical.py`

**역할:** 기술적 지표로 0~20점 산출  
**사용 라이브러리:** `pandas-ta` (import pandas_ta as ta)

```python
def calculate_technical_score(history_df) -> dict:
    """
    history_df: OHLCV DataFrame (최소 60일치 필요)
    반환:
    {
        "score": float,   # 0~20점
        "indicators": [
            {
                "name": str,
                "value": float,
                "signal": "BUY" | "SELL" | "NEUTRAL",
                "score": float
            }
        ]
    }
    """

    # 지표별 배점 기준 (합계 20점)
    # RSI(14):
    #   30 미만 → 과매도 BUY   → 5점
    #   30~50   → 상승권 BUY   → 4점
    #   50~70   → 중립 NEUTRAL → 2점
    #   70 초과 → 과매수 SELL  → 0점
    #
    # MACD:
    #   MACD > Signal → BUY  → 5점
    #   MACD < Signal → SELL → 0점
    #   교차 직후(5일 이내) → 추가 2점
    #
    # 이동평균(20/60):
    #   현재가 > MA20 > MA60 → 정배열 BUY  → 5점
    #   현재가 > MA20, MA20 < MA60 → 2점
    #   현재가 < MA20              → SELL   → 0점
    #
    # 볼린저밴드:
    #   하단 밴드 근처 (±2%) → BUY  → 5점
    #   중간 밴드 근처       → NEUTRAL → 3점
    #   상단 밴드 근처 (±2%) → SELL → 0점
```

---

### 5-5. `backend/services/news_service.py`

**역할:** 뉴스 수집, 감성 점수(0~10점), 키워드 추출

```python
# 수집 소스
# 국내 종목: 네이버 금융 RSS
#   URL 패턴: https://finance.naver.com/item/news_news.naver?code={종목코드}
#   RSS: https://finance.naver.com/rss/news.nhn?productCode={종목코드}
#
# 미국 종목: Yahoo Finance 뉴스
#   yfinance Ticker.news 속성 사용

def fetch_news(ticker: str, market: str, limit: int = 20) -> list[dict]:
    """
    반환: [{"title": str, "link": str, "published": str, "source": str}]
    """
    ...

def analyze_sentiment(news_list: list[dict], ticker: str, market: str) -> dict:
    """
    Gemini API를 사용해 뉴스 목록의 감성 분석
    
    반환:
    {
        "score": float,        # 0~10점
        "positive_ratio": float,  # 0.0~1.0
        "neutral_ratio": float,
        "negative_ratio": float,
        "summary": str,        # 3줄 핵심 요약
        "bull_signals": list[str],  # 상승 재료 키워드
        "bear_signals": list[str],  # 하락 재료 키워드
        "keywords": list[{"text": str, "value": int, "sentiment": "positive"|"negative"|"neutral"}]
    }
    
    감성 점수 산출 기준:
    - 긍정 비율 70%+ → 10점
    - 긍정 비율 50~70% → 7점
    - 긍정 비율 30~50% → 5점
    - 긍정 비율 30% 미만 → 2점
    """
    ...
```

---

### 5-6. `backend/services/ai_judge.py`

**역할:** Gemini API로 전체 분석 결과를 종합하여 0~50점 판정

**Gemini 모델:** `gemini-1.5-flash` (무료 티어)

```python
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

def ai_comprehensive_judge(
    stock_data: dict,
    fundamental_result: dict,
    technical_result: dict,
    sentiment_result: dict,
    news_list: list[dict]
) -> dict:
    """
    Gemini에게 전달할 프롬프트 구조:
    
    당신은 전문 주식 투자 분석가입니다.
    아래 데이터를 바탕으로 {종목명}({티커})의 투자 적합성을 0~50점으로 평가하세요.
    
    [종목 기본 정보]
    - 현재가: {current_price}
    - 시가총액: {market_cap}
    - 시장: {market}
    
    [재무 분석 결과] (20점 만점 중 {score}점)
    - PER: {per}
    - PBR: {pbr}
    - ROE: {roe}
    - 부채비율: {debt_ratio}
    
    [기술적 분석 결과] (20점 만점 중 {score}점)
    - RSI: {rsi} ({signal})
    - MACD: {signal}
    - 이동평균: {signal}
    
    [뉴스/감성 분석] (10점 만점 중 {score}점)
    - 긍정: {positive}% / 중립: {neutral}% / 부정: {negative}%
    - 핵심 뉴스 요약: {summary}
    - 상승 재료: {bull_signals}
    - 하락 재료: {bear_signals}
    
    위 정보를 종합적으로 분석하여 다음 JSON 형식으로만 응답하세요:
    {
        "score": <0~50 사이 정수>,
        "verdict": "<QUALIFIED|DISQUALIFIED>",
        "reasoning": "<150자 이내 한국어 판정 근거>",
        "strengths": ["<강점1>", "<강점2>", "<강점3>"],
        "weaknesses": ["<약점1>", "<약점2>"],
        "recommendation": "<매수|관망|매도>"
    }
    
    반환:
    {
        "score": int,          # 0~50점
        "verdict": str,        # "QUALIFIED" | "DISQUALIFIED"
        "reasoning": str,      # 판정 근거 (한국어)
        "strengths": list[str],
        "weaknesses": list[str],
        "recommendation": str  # "매수" | "관망" | "매도"
    }
    """
    ...
```

---

### 5-7. `backend/routers/analysis.py`

**엔드포인트:** `POST /api/analysis/run`

```python
# Request Body
{
    "ticker": "005930",
    "market": "KR"   # "KR" | "US"
}

# Response 200
{
    "ticker": "005930",
    "name": "삼성전자",
    "market": "KR",
    "current_price": 75000,
    "market_cap": 448000000000000,
    "analyzed_at": "2026-05-14T09:00:00Z",
    
    "total_score": 82,
    "verdict": "QUALIFIED",          # "QUALIFIED" | "DISQUALIFIED"
    "recommendation": "매수",
    
    "breakdown": {
        "fundamental": {
            "score": 14,             # 0~20점
            "indicators": [
                {"name": "PER", "value": 12.3, "benchmark": "15 이하", "pass": true, "weight": 5},
                {"name": "PBR", "value": 1.2, "benchmark": "3 이하", "pass": true, "weight": 5},
                {"name": "ROE", "value": 14.5, "benchmark": "10% 이상", "pass": true, "weight": 5},
                {"name": "부채비율", "value": 35.0, "benchmark": "100% 이하", "pass": true, "weight": 3},
                {"name": "매출성장률", "value": -2.1, "benchmark": "0% 이상", "pass": false, "weight": 2}
            ]
        },
        "technical": {
            "score": 13,             # 0~20점
            "indicators": [
                {"name": "RSI", "value": 42.3, "signal": "BUY", "score": 4},
                {"name": "MACD", "value": 125.0, "signal": "BUY", "score": 5},
                {"name": "이동평균", "value": null, "signal": "NEUTRAL", "score": 2},
                {"name": "볼린저밴드", "value": null, "signal": "NEUTRAL", "score": 2}
            ]
        },
        "sentiment": {
            "score": 7,              # 0~10점
            "positive_ratio": 0.62,
            "neutral_ratio": 0.25,
            "negative_ratio": 0.13,
            "summary": "실적 개선 기대감 상승. 반도체 업황 회복 신호. 외국인 순매수 지속.",
            "bull_signals": ["실적 개선", "반도체 회복", "외국인 매수"],
            "bear_signals": ["환율 리스크"],
            "keywords": [
                {"text": "실적", "value": 15, "sentiment": "positive"},
                {"text": "반도체", "value": 12, "sentiment": "positive"},
                {"text": "환율", "value": 8, "sentiment": "negative"}
            ]
        },
        "ai": {
            "score": 48,             # 0~50점
            "reasoning": "재무 건전성과 기술적 지표가 양호하며 뉴스 센티먼트도 긍정적. 단기 매출 감소는 우려되나 중장기 전망은 밝음.",
            "strengths": ["탄탄한 재무구조", "기술적 반등 신호", "긍정적 뉴스 흐름"],
            "weaknesses": ["단기 매출 역성장", "환율 불확실성"]
        }
    },
    
    "news": [
        {
            "title": "삼성전자, 2분기 실적 기대 이상...",
            "link": "https://...",
            "published": "2026-05-14T08:30:00Z",
            "source": "네이버금융"
        }
    ]
}
```

---

### 5-8. `backend/routers/stocks.py`

```
GET /api/stocks/search?q={keyword}&market={KR|US}

Response 200:
{
    "results": [
        {"ticker": "005930", "name": "삼성전자", "market": "KR", "current_price": 75000},
        ...
    ]
}
```

---

## 6. Frontend 상세 구현

### 6-1. TypeScript 타입 정의 (`src/types/index.ts`)

```typescript
export type Market = 'KR' | 'US';
export type Verdict = 'QUALIFIED' | 'DISQUALIFIED';
export type Signal = 'BUY' | 'SELL' | 'NEUTRAL';
export type Recommendation = '매수' | '관망' | '매도';
export type Sentiment = 'positive' | 'negative' | 'neutral';

export interface SearchResult {
  ticker: string;
  name: string;
  market: Market;
  current_price: number;
}

export interface FundamentalIndicator {
  name: string;
  value: number | null;
  benchmark: string;
  pass: boolean;
  weight: number;
}

export interface TechnicalIndicator {
  name: string;
  value: number | null;
  signal: Signal;
  score: number;
}

export interface NewsKeyword {
  text: string;
  value: number;
  sentiment: Sentiment;
}

export interface NewsItem {
  title: string;
  link: string;
  published: string;
  source: string;
}

export interface AnalysisResult {
  ticker: string;
  name: string;
  market: Market;
  current_price: number;
  market_cap: number;
  analyzed_at: string;
  total_score: number;
  verdict: Verdict;
  recommendation: Recommendation;
  breakdown: {
    fundamental: {
      score: number;
      indicators: FundamentalIndicator[];
    };
    technical: {
      score: number;
      indicators: TechnicalIndicator[];
    };
    sentiment: {
      score: number;
      positive_ratio: number;
      neutral_ratio: number;
      negative_ratio: number;
      summary: string;
      bull_signals: string[];
      bear_signals: string[];
      keywords: NewsKeyword[];
    };
    ai: {
      score: number;
      reasoning: string;
      strengths: string[];
      weaknesses: string[];
    };
  };
  news: NewsItem[];
}
```

---

### 6-2. 화면 레이아웃 (StockDetail.tsx)

**전체 레이아웃 구조:**

```
┌─────────────────────────────────────────────────────────┐
│  [검색창]                               [국내 | 미국]    │
├─────────────────────────────────────────────────────────┤
│                    종목명 (티커) · 시장                   │
│                    현재가 / 시가총액                      │
├───────────────────────────┬─────────────────────────────┤
│                           │  ┌─────────────────────┐   │
│     레이더 차트            │  │   반원 게이지         │   │
│   (재무/기술/감성/AI/뉴스) │  │     82 / 100         │   │
│      5축 입체 표현         │  │   ✅ 투자 적격        │   │
│                           │  └─────────────────────┘   │
│                           │  추천: 매수                  │
│                           │  AI 판정 근거 텍스트          │
├───────────────────────────┴─────────────────────────────┤
│                영역별 점수 분석                            │
│  재무 ████████░░ 14/20  기술 █████████░ 13/20            │
│  감성 ███████░░░  7/10  AI  ████████████████████ 48/50  │
├───────────────────────────────────────────────────────── │
│  강점                      │  약점                       │
│  ✅ 탄탄한 재무구조          │  ⚠️ 단기 매출 역성장        │
│  ✅ 기술적 반등 신호         │  ⚠️ 환율 불확실성           │
├─────────────────────────────────────────────────────────┤
│                재무 지표 상세                              │
│  PER 12.3 ✅  PBR 1.2 ✅  ROE 14.5% ✅                  │
│  부채비율 35% ✅  매출성장률 -2.1% ❌                     │
├───────────────────────────┬─────────────────────────────┤
│   기술적 지표              │  감성 버블 차트               │
│   RSI: 42.3 📈 BUY        │  [실적] [반도체] [환율]      │
│   MACD: BUY               │  키워드 크기 = 빈도           │
│   이동평균: NEUTRAL        │  색상 = 긍/부정              │
│   볼린저: NEUTRAL          │                             │
├───────────────────────────┴─────────────────────────────┤
│                최신 뉴스 종합                              │
│  [긍정 62%] [중립 25%] [부정 13%]                        │
│  핵심: 실적 개선 기대감 상승. 반도체 업황 회복 신호.        │
│  상승재료: 실적 개선, 반도체 회복  하락재료: 환율 리스크    │
│  ─────────────────────────────────────────              │
│  📰 삼성전자, 2분기 실적 기대 이상... (네이버금융)          │
│  📰 외국인 3일 연속 순매수... (한국경제)                   │
└─────────────────────────────────────────────────────────┘
```

---

### 6-3. 핵심 컴포넌트 명세

#### `ScoreGauge.tsx` — 반원 게이지
- `react-circular-progressbar` 사용
- 0~100 값 표시
- 80 기준으로 색상 전환 (미만: `#ef4444` 빨강, 이상: `#22c55e` 초록)
- 중앙에 점수 숫자 + 큰 폰트로 표시
- 하단에 "투자 적격" / "투자 부적격" 텍스트

Props:
```typescript
interface ScoreGaugeProps {
  score: number;     // 0~100
  verdict: Verdict;
}
```

#### `RadarChart.tsx` — 레이더 차트 (5축)
- `recharts` RadarChart 사용
- 5개 축: 재무(20점 만점), 기술(20점), 감성(10점), AI(50점), 뉴스(10점)
- 각 축을 비율(%)로 정규화하여 표시 (0~100% 스케일)
- 반투명 녹색 채우기
- 80점 기준선 참고용 점선 표시

Props:
```typescript
interface RadarChartProps {
  fundamental: number;   // 0~20
  technical: number;     // 0~20
  sentiment: number;     // 0~10
  ai: number;            // 0~50
}
```

#### `SentimentBubble.tsx` — 감성 버블/워드클라우드
- `@visx/wordcloud` 사용
- 키워드 크기 = 빈도(value) 비례
- 색상: positive → `#22c55e`, negative → `#ef4444`, neutral → `#94a3b8`

Props:
```typescript
interface SentimentBubbleProps {
  keywords: NewsKeyword[];
}
```

#### `ScoreBreakdown.tsx` — 영역별 점수 막대
- 재무/기술/감성/AI 각 영역 점수를 수평 막대 차트로 표시
- 점수/만점 텍스트 함께 표시
- Recharts BarChart 사용

#### `VerdictBadge.tsx` — 판정 뱃지
- QUALIFIED: 초록 배경 "✅ 투자 적격"
- DISQUALIFIED: 빨강 배경 "❌ 투자 부적격"

---

### 6-4. API 호출 (`src/api/stockApi.ts`)

```typescript
import axios from 'axios';
import { SearchResult, AnalysisResult } from '../types';

const api = axios.create({ baseURL: '/api' });

export const searchStocks = async (query: string, market: string): Promise<SearchResult[]> => {
  const { data } = await api.get('/stocks/search', { params: { q: query, market } });
  return data.results;
};

export const runAnalysis = async (ticker: string, market: string): Promise<AnalysisResult> => {
  const { data } = await api.post('/analysis/run', { ticker, market });
  return data;
};
```

---

## 7. 구현 순서 (Phase별)

### Phase 1 — Backend 기반 (1일차)
1. `backend/` 폴더 생성 및 `requirements.txt` 설치
2. `.env` 파일 생성 (Gemini API 키 입력)
3. `main.py` 작성 (FastAPI 앱 + CORS)
4. `data_fetcher.py` 구현 (yfinance + pykrx)
5. `stocks.py` 라우터 구현 (종목 검색 API)
6. **테스트:** `GET /api/stocks/search?q=삼성전자&market=KR` 동작 확인

### Phase 2 — 분석 엔진 (2일차)
1. `fundamental.py` 구현 (재무 지표 점수화)
2. `technical.py` 구현 (pandas-ta 기술 지표)
3. `news_service.py` 구현 (RSS 수집 + Gemini 감성 분석)
4. `ai_judge.py` 구현 (Gemini 종합 판정)
5. `analysis.py` 라우터 구현 (위 서비스 조합)
6. **테스트:** `POST /api/analysis/run` 전체 응답 확인

### Phase 3 — Frontend (3~4일차)
1. Vite + React + TypeScript 프로젝트 생성
2. Tailwind CSS 설정
3. 타입 정의 (`types/index.ts`)
4. API 함수 (`api/stockApi.ts`)
5. `SearchBar.tsx` → `VerdictBadge.tsx` → `ScoreGauge.tsx` 순서로 컴포넌트 구현
6. `RadarChart.tsx` → `ScoreBreakdown.tsx` → `SentimentBubble.tsx` → `NewsPanel.tsx`
7. `StockDetail.tsx` 페이지 조립
8. `Home.tsx` 검색 메인 화면 구현

---

## 8. 주의사항 및 예외 처리

### 데이터 없음 처리
- 재무 지표가 없는 경우 (일부 종목): 해당 항목 0점 처리, UI에 "데이터 없음" 표시
- 뉴스가 없는 경우: 감성 점수 5점(중립) 처리

### pykrx 주의사항
- `pykrx`는 KRX 공식 데이터를 스크래핑 — 장 마감 후(오후 4시 이후) 당일 데이터 사용 가능
- 티커는 6자리 숫자 문자열 (예: "005930")
- 종목 검색은 `stock.get_market_ticker_list(date, market='KOSPI')` 또는 `'KOSDAQ'` 사용

### yfinance 주의사항
- 미국 종목 티커는 심볼 그대로 (예: "AAPL", "TSLA")
- `.info` 딕셔너리에서 재무 데이터 추출 시 키 존재 여부 반드시 확인 (`.get()` 사용)

### Gemini API 에러 처리
- Rate Limit 초과 시 (429 에러): 30초 대기 후 1회 재시도
- 응답이 JSON 파싱 실패 시: 기본값 반환 (score: 25, verdict: "DISQUALIFIED")

### CORS
- 개발 환경: Vite proxy 설정으로 해결 (`/api` → `localhost:8000`)
- 프로덕션 배포 시: FastAPI CORS allow_origins 수정 필요

---

## 9. 완성 기준 (Definition of Done)

- [ ] 국내 종목 티커 입력 시 전체 분석 결과 반환
- [ ] 미국 종목 티커 입력 시 전체 분석 결과 반환
- [ ] 0~100점 게이지 UI 표시
- [ ] 80점 기준 적격/부적격 판정 표시
- [ ] 레이더 차트 5축 표시
- [ ] 영역별 점수 막대 표시
- [ ] 재무 지표 상세 (PER/PBR/ROE/부채비율/매출성장률)
- [ ] 기술적 지표 상세 (RSI/MACD/이동평균/볼린저밴드)
- [ ] 최신 뉴스 목록 표시 (최소 5건)
- [ ] 뉴스 감성 비율 표시 (긍정/중립/부정 %)
- [ ] 감성 버블 차트 표시
- [ ] Gemini AI 판정 근거 텍스트 표시
- [ ] 강점/약점 항목 표시
- [ ] 반응형 레이아웃 (모바일 최소 지원)
