import logging
import math
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    """float 변환 후 NaN/Inf를 None으로 정규화."""
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def calculate_technical_score(history_df: pd.DataFrame) -> dict:
    indicators = []
    total = 0.0

    if history_df is None or len(history_df) < 20:
        return {
            "score": 0.0,
            "indicators": [
                {"name": "RSI(14)", "value": None, "signal": "NEUTRAL", "score": 0},
                {"name": "MACD", "value": None, "signal": "NEUTRAL", "score": 0},
                {"name": "이동평균(20/60)", "value": None, "signal": "NEUTRAL", "score": 0},
                {"name": "볼린저밴드", "value": None, "signal": "NEUTRAL", "score": 0},
            ],
        }

    try:
        import pandas_ta as ta
    except ImportError:
        return {"score": 0.0, "indicators": []}

    df = history_df.copy()

    # RSI(14) - 최대 5점
    try:
        rsi_series = ta.rsi(df["Close"], length=14)
        rsi_val = _safe_float(rsi_series.iloc[-1]) if rsi_series is not None and not rsi_series.empty else None
        if rsi_val is None:
            rsi_score, rsi_signal = 0.0, "NEUTRAL"
        elif rsi_val < 30:
            rsi_score, rsi_signal = 5.0, "BUY"   # 과매도 — 강한 매수
        elif rsi_val < 50:
            rsi_score, rsi_signal = 4.0, "BUY"   # 중립 이하 — 매수 우위
        elif rsi_val <= 65:
            rsi_score, rsi_signal = 3.0, "NEUTRAL"  # 정상 상승 구간
        elif rsi_val <= 75:
            rsi_score, rsi_signal = 2.0, "NEUTRAL"  # 다소 과열이나 추세 유효
        else:
            rsi_score, rsi_signal = 1.0, "SELL"  # 과매수 — 감점만, 0점 제거
        indicators.append({"name": "RSI(14)", "value": round(rsi_val, 2) if rsi_val is not None else None, "signal": rsi_signal, "score": rsi_score})
        total += rsi_score
    except Exception:
        logger.exception("RSI 계산 실패")
        indicators.append({"name": "RSI(14)", "value": None, "signal": "NEUTRAL", "score": 0.0})

    # MACD - 최대 7점 (기본 5 + 교차 보너스 2)
    try:
        macd_df = ta.macd(df["Close"])
        if macd_df is not None and not macd_df.empty:
            macd_col = [c for c in macd_df.columns if "MACD_" in c and "MACDs" not in c and "MACDh" not in c]
            signal_col = [c for c in macd_df.columns if "MACDs" in c]
            if macd_col and signal_col:
                macd_val = _safe_float(macd_df[macd_col[0]].iloc[-1])
                sig_val = _safe_float(macd_df[signal_col[0]].iloc[-1])
                if macd_val is None or sig_val is None:
                    indicators.append({"name": "MACD", "value": None, "signal": "NEUTRAL", "score": 0.0})
                else:
                    # 5일 이내 골든크로스 여부: prev=[-2]봉, curr=최신봉(iloc[-1])
                    recent = macd_df[[macd_col[0], signal_col[0]]].iloc[-6:-1]
                    crossed_recently = False
                    if len(recent) >= 2:
                        prev_diff = _safe_float(recent[macd_col[0]].iloc[-2]) or 0
                        curr_diff = macd_val - sig_val
                        prev_sig = _safe_float(recent[signal_col[0]].iloc[-2]) or 0
                        crossed_recently = (prev_diff - prev_sig < 0 and curr_diff > 0)

                    if macd_val > sig_val:
                        macd_score = 5.0 + (2.0 if crossed_recently else 0.0)
                        macd_signal = "BUY"
                    else:
                        macd_score = 2.0  # SELL이어도 최소 2점 (추세 하나로 전체 박살 방지)
                        macd_signal = "SELL"

                    macd_score = min(macd_score, 7.0)
                    indicators.append({"name": "MACD", "value": round(macd_val, 4), "signal": macd_signal, "score": macd_score})
                    total += macd_score
            else:
                indicators.append({"name": "MACD", "value": None, "signal": "NEUTRAL", "score": 0.0})
        else:
            indicators.append({"name": "MACD", "value": None, "signal": "NEUTRAL", "score": 0.0})
    except Exception:
        logger.exception("MACD 계산 실패")
        indicators.append({"name": "MACD", "value": None, "signal": "NEUTRAL", "score": 0.0})

    # 이동평균 (20/60) - 최대 5점 (데이터 부족 시 MA20만)
    try:
        close = df["Close"]
        current_price = _safe_float(close.iloc[-1])
        ma20 = _safe_float(close.rolling(20).mean().iloc[-1])
        has_60 = len(close) >= 60
        ma60 = _safe_float(close.rolling(60).mean().iloc[-1]) if has_60 else None

        if current_price is None or ma20 is None:
            indicators.append({"name": "이동평균(20/60)", "value": None, "signal": "NEUTRAL", "score": 0.0})
        else:
            if ma60 is not None:
                if current_price > ma20 > ma60:
                    ma_score, ma_signal = 5.0, "BUY"    # 정배열
                elif current_price > ma20:
                    ma_score, ma_signal = 3.5, "BUY"    # MA20 위 (단기 상승)
                elif current_price > ma60:
                    ma_score, ma_signal = 2.0, "NEUTRAL" # MA60 위 (중기 지지)
                else:
                    ma_score, ma_signal = 1.0, "SELL"   # 하락 추세도 최소 1점
            else:
                if current_price > ma20:
                    ma_score, ma_signal = 3.0, "BUY"
                else:
                    ma_score, ma_signal = 1.0, "SELL"

            indicators.append({"name": "이동평균(20/60)", "value": round(ma20, 2), "signal": ma_signal, "score": ma_score})
            total += ma_score
    except Exception:
        logger.exception("이동평균 계산 실패")
        indicators.append({"name": "이동평균(20/60)", "value": None, "signal": "NEUTRAL", "score": 0.0})

    # 볼린저밴드 - 최대 5점
    try:
        bb_df = ta.bbands(df["Close"], length=20)
        if bb_df is not None and not bb_df.empty:
            lower_col = [c for c in bb_df.columns if "BBL" in c]
            upper_col = [c for c in bb_df.columns if "BBU" in c]
            if lower_col and upper_col:
                lower = _safe_float(bb_df[lower_col[0]].iloc[-1])
                upper = _safe_float(bb_df[upper_col[0]].iloc[-1])
                cur = _safe_float(df["Close"].iloc[-1])
                if lower is None or upper is None or cur is None:
                    indicators.append({"name": "볼린저밴드", "value": None, "signal": "NEUTRAL", "score": 0.0})
                else:
                    band_width = upper - lower
                    position = (cur - lower) / band_width if band_width > 0 else 0.5
                    if cur < lower:
                        bb_score, bb_signal = 5.0, "BUY"    # 하단 이탈 — 강한 매수
                    elif position < 0.3:
                        bb_score, bb_signal = 4.0, "BUY"    # 하단 30% — 매수 우위
                    elif position <= 0.7:
                        bb_score, bb_signal = 3.0, "NEUTRAL" # 중간 구간 — 정상
                    elif position <= 1.0:
                        bb_score, bb_signal = 2.0, "NEUTRAL" # 상단 30% — 과열 주의
                    else:
                        bb_score, bb_signal = 1.0, "SELL"   # 상단 이탈 — 감점만
                    indicators.append({"name": "볼린저밴드", "value": round(cur, 2), "signal": bb_signal, "score": bb_score})
                    total += bb_score
            else:
                indicators.append({"name": "볼린저밴드", "value": None, "signal": "NEUTRAL", "score": 0.0})
        else:
            indicators.append({"name": "볼린저밴드", "value": None, "signal": "NEUTRAL", "score": 0.0})
    except Exception:
        logger.exception("볼린저밴드 계산 실패")
        indicators.append({"name": "볼린저밴드", "value": None, "signal": "NEUTRAL", "score": 0.0})

    return {"score": round(min(total, 20.0), 2), "indicators": indicators}
