import os
import json
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


async def get_ai_judgment(
    stock_data: dict, fundamental: dict, technical: dict, news: dict
) -> dict:
    indicators_summary = ", ".join(
        f"{i['name']}={i['value']} ({i['benchmark']})"
        for i in fundamental['indicators'] if i['value'] is not None
    )
    tech_summary = ", ".join(
        f"{i['name']}={i['signal']}"
        for i in technical['indicators']
    )

    is_etf = stock_data.get("quote_type") == "ETF"

    if is_etf:
        prompt = f"""You are a professional ETF investment analyst. Analyze the following ETF data and respond ONLY in JSON.

ETF: {stock_data['name']} ({stock_data['ticker']}, {stock_data['market']})
Current Price: {stock_data['current_price']}
ETF Score: {fundamental['score']}/30 (based on expense ratio, AUM, dividend yield, 3-year return)
Technical Score: {technical['score']}/20
Sentiment Score: {news['sentiment_score']}/10
News Score: {news['news_score']}/10

ETF Metrics: {indicators_summary}
Technical Signals: {tech_summary}
News Summary: {news['summary']}

Based on this data, rate the ETF investment suitability from 0 to 30.
Consider: low expense ratio, large AUM, and consistent returns are key for ETF quality.
Be balanced — 10 is average, 18+ means above average, 24+ means excellent.

Respond ONLY in this exact JSON format (reasoning and strengths/weaknesses must be in Korean):
{{"score": <number 0-30>, "reasoning": "<2-3 sentences in Korean>", "strengths": ["<Korean>", "<Korean>"], "weaknesses": ["<Korean>", "<Korean>"]}}"""
    else:
        prompt = f"""You are a professional stock investment analyst. Analyze the following data and respond ONLY in JSON.

Stock: {stock_data['name']} ({stock_data['ticker']}, {stock_data['market']})
Current Price: {stock_data['current_price']}
Fundamental Score: {fundamental['score']}/30
Technical Score: {technical['score']}/20
Sentiment Score: {news['sentiment_score']}/10
News Score: {news['news_score']}/10

Key Fundamentals: {indicators_summary}
Technical Signals: {tech_summary}
News Summary: {news['summary']}

Based on this data, rate the investment suitability from 0 to 30.
Be balanced — 10 is average, 18+ means above average, 24+ means excellent.

Respond ONLY in this exact JSON format (reasoning and strengths/weaknesses must be in Korean):
{{"score": <number 0-30>, "reasoning": "<2-3 sentences in Korean>", "strengths": ["<Korean>", "<Korean>"], "weaknesses": ["<Korean>", "<Korean>"]}}"""

    try:
        import asyncio
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        parsed = json.loads(response.text)
        score = float(parsed.get("score", 15))
        score = max(0.0, min(30.0, score))
        return {
            "score": score,
            "reasoning": parsed.get("reasoning", ""),
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
        }
    except Exception:
        logger.exception("Gemini AI 판정 실패 (Ollama 폴백)")
        return await _ollama_fallback(prompt)


async def _ollama_fallback(prompt: str) -> dict:
    try:
        import httpx
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma4:latest")
        timeout = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{ollama_host}/api/generate",
                json={"model": ollama_model, "prompt": prompt, "stream": False, "format": "json"},
            )
            response.raise_for_status()
            parsed = json.loads(response.json()["response"])
            score = float(parsed.get("score", 15))
            score = max(0.0, min(30.0, score))
            return {
                "score": score,
                "reasoning": parsed.get("reasoning", ""),
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
            }
    except Exception:
        logger.exception("Ollama 폴백도 실패")
        return {
            "score": 15.0,
            "reasoning": "AI 분석 서버에 연결할 수 없습니다.",
            "strengths": [],
            "weaknesses": [],
        }
