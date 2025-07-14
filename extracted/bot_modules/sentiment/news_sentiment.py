import aiohttp
import os
import logging

logger = logging.getLogger(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_URL = "https://newsapi.org/v2/everything"

async def get_news_sentiment(symbol):
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set in environment.")
        return 0

    query = symbol.replace("USDT", "") + " crypto"

    params = {
        "q": query,
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(NEWS_API_URL, params=params, timeout=10) as resp:
                data = await resp.json()
                articles = data.get("articles", [])

                if not articles:
                    return 0  # Netral

                score = 0
                for article in articles:
                    title = article.get("title", "").lower()
                    if any(word in title for word in ["rally", "bull", "buy", "soar"]):
                        score += 1
                    elif any(word in title for word in ["dump", "sell", "crash", "fear"]):
                        score -= 1

                normalized_score = score / len(articles)
                logger.info(f"[News] {symbol} sentiment score: {normalized_score}")
                return normalized_score

    except Exception as e:
        logger.warning(f"News sentiment error for {symbol}: {e}")
        return 0