import logging

logger = logging.getLogger(__name__)


def calculate_etf_score(stock_data: dict) -> dict:
    """ETF 전용 재무 스코어 (30점 만점)"""
    indicators = []
    total = 0.0
    market = stock_data.get("market", "US")

    # 운용보수 (expense ratio) - 최대 10점
    expense = stock_data.get("expense_ratio")
    if expense is None:
        exp_score, exp_pass, exp_bench = 0.0, False, "데이터 없음"
    elif expense <= 0.10:
        exp_score, exp_pass, exp_bench = 10.0, True, "초저비용 (≤0.10%)"
    elif expense <= 0.20:
        exp_score, exp_pass, exp_bench = 8.0, True, "저비용 (0.10~0.20%)"
    elif expense <= 0.50:
        exp_score, exp_pass, exp_bench = 6.0, True, "보통 (0.20~0.50%)"
    elif expense <= 1.00:
        exp_score, exp_pass, exp_bench = 3.0, False, "고비용 (0.50~1.00%)"
    else:
        exp_score, exp_pass, exp_bench = 1.0, False, "매우 고비용 (1.00%+)"
    indicators.append({"name": "운용보수", "value": expense, "benchmark": exp_bench, "pass": exp_pass, "weight": 10.0})
    total += exp_score

    # AUM (운용자산) - 최대 8점: 규모가 클수록 유동성·안정성 높음
    # KR: 원화(Marcap = 원), US: 달러(marketCap = 달러)
    aum = stock_data.get("market_cap")
    if aum is None or aum == 0:
        aum_score, aum_pass, aum_bench = 4.0, True, "데이터 없음 (중립)"
    elif market == "KR":
        # 원화 기준 (1조 = 1_000_000_000_000)
        if aum >= 5_000_000_000_000:       # 5조원+
            aum_score, aum_pass, aum_bench = 8.0, True, "대형 ETF (5조원+)"
        elif aum >= 1_000_000_000_000:     # 1조원+
            aum_score, aum_pass, aum_bench = 6.0, True, "중형 ETF (1~5조원)"
        elif aum >= 100_000_000_000:       # 1000억원+
            aum_score, aum_pass, aum_bench = 4.0, True, "소형 ETF (1000억~1조)"
        elif aum >= 10_000_000_000:        # 100억원+
            aum_score, aum_pass, aum_bench = 2.0, False, "초소형 ETF (100억~1000억)"
        else:
            aum_score, aum_pass, aum_bench = 1.0, False, "유동성 위험 (<100억원)"
    else:
        # 달러 기준
        if aum >= 10_000_000_000:          # 100억달러+
            aum_score, aum_pass, aum_bench = 8.0, True, "대형 ETF (100억$+)"
        elif aum >= 1_000_000_000:
            aum_score, aum_pass, aum_bench = 6.0, True, "중형 ETF (10~100억$)"
        elif aum >= 100_000_000:
            aum_score, aum_pass, aum_bench = 4.0, True, "소형 ETF (1~10억$)"
        elif aum >= 10_000_000:
            aum_score, aum_pass, aum_bench = 2.0, False, "초소형 ETF (1000만$+)"
        else:
            aum_score, aum_pass, aum_bench = 1.0, False, "유동성 위험 (<1000만$)"
    indicators.append({"name": "AUM(운용규모)", "value": aum, "benchmark": aum_bench, "pass": aum_pass, "weight": 8.0})
    total += aum_score

    # 분배율 (dividend yield) - 최대 6점
    div_yield = stock_data.get("dividend_yield")
    if div_yield is None:
        div_score, div_pass, div_bench = 0.0, False, "데이터 없음"
    elif div_yield >= 4.0:
        div_score, div_pass, div_bench = 6.0, True, "고배당 (4%+)"
    elif div_yield >= 2.0:
        div_score, div_pass, div_bench = 5.0, True, "양호 (2~4%)"
    elif div_yield >= 0.5:
        div_score, div_pass, div_bench = 3.0, True, "소배당 (0.5~2%)"
    else:
        div_score, div_pass, div_bench = 2.0, True, "무배당/성장형"
    indicators.append({"name": "분배율(배당)", "value": div_yield, "benchmark": div_bench, "pass": div_pass, "weight": 6.0})
    total += div_score

    # 추적오차 (3년 연환산 수익률로 대체 — yfinance에서 직접 tracking error 제공 안 함)
    # three_year_return을 통해 장기 성과를 간접 평가
    three_yr = stock_data.get("three_year_return")
    if three_yr is None:
        perf_score, perf_pass, perf_bench = 0.0, False, "데이터 없음"
    elif three_yr >= 15:
        perf_score, perf_pass, perf_bench = 6.0, True, "우수 (연 15%+)"
    elif three_yr >= 8:
        perf_score, perf_pass, perf_bench = 5.0, True, "양호 (연 8~15%)"
    elif three_yr >= 3:
        perf_score, perf_pass, perf_bench = 3.0, True, "보통 (연 3~8%)"
    elif three_yr >= 0:
        perf_score, perf_pass, perf_bench = 2.0, False, "저조 (0~3%)"
    else:
        perf_score, perf_pass, perf_bench = 1.0, False, "손실 (음수)"
    indicators.append({"name": "3년수익률", "value": three_yr, "benchmark": perf_bench, "pass": perf_pass, "weight": 6.0})
    total += perf_score

    scaled = round(min(total, 30.0), 2)
    return {"score": scaled, "indicators": indicators}
