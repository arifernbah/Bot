
def backtest(config: dict, data: list[dict]) -> dict:
    pnl = 0
    trades = 0
    win = 0
    balance = config.get("equity", 100)

    for i in range(1, len(data)):
        ohlcv = data[i]

        # Placeholder logic: beli kalau naik, jual kalau turun
        entry_cond = data[i]["close"] > data[i - 1]["close"]
        exit_cond = data[i]["close"] < data[i - 1]["close"]

        if entry_cond:
            entry_price = data[i]["close"]
            trades += 1
            if exit_cond:
                pnl += data[i]["close"] - entry_price
                if data[i]["close"] > entry_price:
                    win += 1

    winrate = (win / trades) * 100 if trades else 0

    return {
        "pnl": round(pnl, 2),
        "winrate": round(winrate, 2),
        "max_drawdown": -5.0,  # dummy dulu
        "trades": trades
    }
