"""
Sentiment & News Intelligence Module (Lightweight)
==================================================
Provides:
    • get_market_sentiment() – pulls Fear & Greed Index (Alternative.me)
    • score_text_sentiment(text) – local VADER polarity scoring

Designed to be extremely light-weight for VPS 1 GB.
"""
from __future__ import annotations

import aiohttp
import asyncio
import logging
from typing import Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Instantiate once (cheap)
_analyzer = SentimentIntensityAnalyzer()

FNG_API = "https://api.alternative.me/fng/?limit=1&format=json"

async def get_market_sentiment(session: aiohttp.ClientSession | None = None) -> Tuple[int, str]:
    """Fetch Crypto Fear & Greed Index.

    Returns
    -------
    score : int
        0-100 (0 = Extreme Fear, 100 = Extreme Greed).
    classification : str
        Human readable classification from the API.
    """
    owns_session = False
    if session is None:
        session = aiohttp.ClientSession()
        owns_session = True
    try:
        async with session.get(FNG_API, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()
            value = int(data["data"][0]["value"])
            classification = data["data"][0]["value_classification"].lower()
            return value, classification
    except Exception as e:
        logger.warning(f"Sentiment fetch failed: {e}")
        return -1, "unknown"
    finally:
        if owns_session:
            await session.close()

def score_text_sentiment(text: str) -> float:
    """Return compound sentiment score (-1 .. 1) using VADER."""
    vs = _analyzer.polarity_scores(text)
    return vs["compound"]

# Quick manual test
if __name__ == "__main__":
    async def _test():
        print(await get_market_sentiment())
        print(score_text_sentiment("Bitcoin to the moon! 🚀"))
    asyncio.run(_test())