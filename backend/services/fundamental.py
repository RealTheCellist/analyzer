_TECH_SECTORS = {
    "Technology", "Communication Services", "Semiconductors",
    "Software", "Internet", "AI",
}
_BIO_SECTORS = {
    "Healthcare", "Biotechnology", "Pharmaceuticals",
    "Medical Devices",
}
_FINANCE_SECTORS = {
    "Financial Services", "Banking", "Insurance",
    "Real Estate", "REITs",
}


def _classify(stock_data: dict) -> str:
    """업종 분류: tech / bio / finance / kosdaq / default"""
    market = stock_data.get("market", "")
    sector = stock_data.get("sector", "") or ""
    industry = stock_data.get("industry", "") or ""
    combined = (sector + " " + industry).lower()

    if market == "KR":
        return "kosdaq" if "KOSDAQ" in sector.upper() else "default"

    for s in _TECH_SECTORS:
        if s.lower() in combined:
            return "tech"
    for s in _BIO_SECTORS:
        if s.lower() in combined:
            return "bio"
    for s in _FINANCE_SECTORS:
        if s.lower() in combined:
            return "finance"
    return "default"


def _score_per(per, kind: str):
    if per is None:
        return 0.0, False, "데이터 없음"
    if per <= 0:
        return 0.0, False, "음수 (적자)"

    if kind == "tech":
        # 테크: 고PER 허용 (AI·반도체 평균 40~60)
        if per <= 20:   return 5.0, True,  "저평가 (0~20)"
        if per <= 40:   return 4.0, True,  "적정 (20~40)"
        if per <= 70:   return 3.0, True,  "성장 프리미엄 (40~70)"
        if per <= 120:  return 2.0, True,  "고성장 프리미엄 (70~120)"
        return           1.0, False, "과열 (120+)"

    if kind == "bio":
        # 바이오: 파이프라인 가치로 PER 무의미할 수 있음 → 관대하게
        if per <= 30:   return 5.0, True,  "저평가 (0~30)"
        if per <= 60:   return 4.0, True,  "적정 (30~60)"
        if per <= 100:  return 3.0, True,  "성장 기대 (60~100)"
        if per <= 200:  return 2.0, True,  "파이프라인 프리미엄 (100~200)"
        return           1.0, False, "과열 (200+)"

    if kind == "kosdaq":
        # KOSDAQ: 성장주 특성, tech보다 살짝 관대
        if per <= 20:   return 5.0, True,  "저평가 (0~20)"
        if per <= 40:   return 4.0, True,  "적정 (20~40)"
        if per <= 70:   return 3.0, True,  "성장주 수준 (40~70)"
        if per <= 120:  return 2.0, True,  "고성장 프리미엄 (70~120)"
        return           1.0, False, "고평가 (120+)"

    # default / finance
    if per <= 15:   return 5.0, True,  "저평가 (0~15)"
    if per <= 25:   return 4.0, True,  "적정 (15~25)"
    if per <= 40:   return 3.0, True,  "성장주 수준 (25~40)"
    if per <= 60:   return 2.0, True,  "고성장 프리미엄 (40~60)"
    return           1.0, False, "고평가 (60+)"


def _score_pbr(pbr, kind: str):
    if pbr is None:
        return 0.0, False, "데이터 없음"
    if pbr <= 0:
        return 0.0, False, "음수"

    if kind == "tech":
        # 테크: 무형자산·IP 가치 크므로 PBR 높음이 정상 (NVDA ~35, MSFT ~15)
        if pbr <= 3:    return 5.0, True,  "저평가 (0~3)"
        if pbr <= 10:   return 4.0, True,  "적정 (3~10)"
        if pbr <= 20:   return 3.0, True,  "프리미엄 (10~20)"
        if pbr <= 40:   return 2.0, True,  "고프리미엄 (20~40)"
        return           1.0, False, "과열 (40+)"

    if kind == "bio":
        if pbr <= 3:    return 5.0, True,  "저평가 (0~3)"
        if pbr <= 8:    return 4.0, True,  "적정 (3~8)"
        if pbr <= 15:   return 3.0, True,  "파이프라인 프리미엄 (8~15)"
        if pbr <= 30:   return 2.0, True,  "고프리미엄 (15~30)"
        return           1.0, False, "과열 (30+)"

    if kind == "finance":
        # 금융: 장부가 기반 사업, PBR 1~1.5가 정상
        if pbr <= 1:    return 5.0, True,  "저평가 (0~1)"
        if pbr <= 1.5:  return 4.0, True,  "적정 (1~1.5)"
        if pbr <= 2.5:  return 3.0, True,  "보통 (1.5~2.5)"
        if pbr <= 4:    return 2.0, True,  "고평가 (2.5~4)"
        return           1.0, False, "과열 (4+)"

    if kind == "kosdaq":
        if pbr <= 2:    return 5.0, True,  "저평가 (0~2)"
        if pbr <= 5:    return 4.0, True,  "적정 (2~5)"
        if pbr <= 10:   return 3.0, True,  "성장 프리미엄 (5~10)"
        if pbr <= 20:   return 2.0, True,  "고프리미엄 (10~20)"
        return           1.0, False, "과열 (20+)"

    # default (KOSPI 제조·에너지 등)
    if pbr <= 1:    return 5.0, True,  "저평가 (0~1)"
    if pbr <= 3:    return 4.0, True,  "적정 (1~3)"
    if pbr <= 6:    return 3.0, True,  "브랜드 프리미엄 (3~6)"
    if pbr <= 10:   return 2.0, True,  "고프리미엄 (6~10)"
    return           1.0, False, "과열 (10+)"


def _score_roe(roe, kind: str):
    if roe is None:
        return 0.0, False, "데이터 없음"

    if kind == "finance":
        # 금융: ROE 8~12%가 업계 평균
        if roe >= 15:   return 5.0, True,  "우수 (15%+)"
        if roe >= 8:    return 4.0, True,  "양호 (8~15%)"
        if roe >= 4:    return 3.0, True,  "보통 (4~8%)"
        if roe >= 0:    return 1.0, False, "미흡 (0~4%)"
        return           0.0, False, "손실 (음수)"

    # tech / bio / kosdaq / default 공통
    if roe >= 20:   return 5.0, True,  "우수 (20%+)"
    if roe >= 10:   return 4.0, True,  "양호 (10~20%)"
    if roe >= 5:    return 3.0, True,  "보통 (5~10%)"
    if roe >= 0:    return 1.0, False, "미흡 (0~5%)"
    return           0.0, False, "손실 (음수)"


def _score_debt(debt, kind: str):
    if debt is None:
        return 0.0, False, "데이터 없음"

    if kind == "finance":
        # 금융: 레버리지 사업 특성상 부채비율 수백~수천% 정상
        # 총자산 대비 부채로 계산되므로 다른 기준 적용
        if debt <= 800:     return 3.0, True,  "안전 (~800%)"
        if debt <= 1500:    return 2.0, True,  "보통 (800~1500%)"
        if debt <= 2500:    return 1.0, True,  "주의 (1500~2500%)"
        return               0.0, False, "위험 (2500%+)"

    if kind in ("tech", "kosdaq"):
        # 테크·KOSDAQ 성장기업: 투자 단계에서 부채 높을 수 있음
        if debt <= 80:      return 3.0, True,  "안전 (~80%)"
        if debt <= 150:     return 2.0, True,  "보통 (80~150%)"
        if debt <= 300:     return 1.0, True,  "주의 (150~300%)"
        return               0.0, False, "위험 (300%+)"

    # default / bio
    if debt <= 100:     return 3.0, True,  "안전 (~100%)"
    if debt <= 200:     return 2.0, True,  "보통 (100~200%)"
    if debt <= 350:     return 1.0, True,  "주의 (200~350%)"
    return               0.0, False, "위험 (350%+)"


def _score_revenue_growth(rev, kind: str):
    if rev is None:
        return 0.0, False, "데이터 없음"

    if kind in ("tech", "kosdaq"):
        # 테크: 20%+ 성장이 기대치
        if rev >= 20:   return 2.0, True,  "고성장 (20%+)"
        if rev >= 10:   return 1.5, True,  "성장 (10~20%)"
        if rev >= 0:    return 1.0, True,  "안정 (0~10%)"
        if rev >= -10:  return 0.5, False, "소폭 역성장 (-10~0%)"
        return           0.0, False, "역성장 (-10%+)"

    if kind == "bio":
        # 바이오: 임상 단계 기업은 매출 없을 수 있음 → 매우 관대
        if rev >= 10:   return 2.0, True,  "성장 (10%+)"
        if rev >= 0:    return 1.5, True,  "안정 (0~10%)"
        if rev >= -30:  return 1.0, False, "임상 단계 (-30~0%)"
        return           0.0, False, "매출 감소 (-30%+)"

    # default / finance
    if rev >= 10:   return 2.0, True,  "고성장 (10%+)"
    if rev >= 3:    return 1.5, True,  "성장 (3~10%)"
    if rev >= 0:    return 1.0, True,  "안정 (0~3%)"
    if rev >= -10:  return 0.5, False, "소폭 역성장 (-10~0%)"
    return           0.0, False, "역성장 (-10%+)"


def calculate_fundamental_score(stock_data: dict) -> dict:
    kind = _classify(stock_data)
    indicators = []
    total = 0.0

    per = stock_data.get("per")
    s, p, b = _score_per(per, kind)
    indicators.append({"name": "PER", "value": per, "benchmark": b, "pass": p, "weight": 5.0})
    total += s

    pbr = stock_data.get("pbr")
    s, p, b = _score_pbr(pbr, kind)
    indicators.append({"name": "PBR", "value": pbr, "benchmark": b, "pass": p, "weight": 5.0})
    total += s

    roe = stock_data.get("roe")
    s, p, b = _score_roe(roe, kind)
    indicators.append({"name": "ROE", "value": roe, "benchmark": b, "pass": p, "weight": 5.0})
    total += s

    debt = stock_data.get("debt_ratio")
    s, p, b = _score_debt(debt, kind)
    indicators.append({"name": "부채비율", "value": debt, "benchmark": b, "pass": p, "weight": 3.0})
    total += s

    rev = stock_data.get("revenue_growth")
    s, p, b = _score_revenue_growth(rev, kind)
    indicators.append({"name": "매출성장률", "value": rev, "benchmark": b, "pass": p, "weight": 2.0})
    total += s

    # 기존 최대 20점 → 30점으로 스케일업
    scaled = round(min(total * 1.5, 30.0), 2)
    return {"score": scaled, "indicators": indicators, "sector_kind": kind}
