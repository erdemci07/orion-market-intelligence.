from strategy.scoring import score_symbol
from config import MIN_FINAL_SCORE


MIN_VOLUME_24H = 100_000
MIN_ADX = 0


def get_candidate_symbols():
    return [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "AVAXUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "LINKUSDT",
        "XAUUSDT",
        "SUIUSDT",
    ]


def pre_filter(symbol_data):
    if symbol_data["price"] <= 0:
        return False

    if symbol_data["volume_24h"] < MIN_VOLUME_24H:
        return False

    if symbol_data["adx"] < MIN_ADX:
        return False

    return True


def scan_market(market_data):
    approved = []

    for symbol, data in market_data.items():
        if not pre_filter(data):
            continue

        score_result = score_symbol(data)
        final_score = score_result["final_score"]

        print(symbol, final_score, score_result["scores"])

        if final_score >= MIN_FINAL_SCORE:
            approved.append({
                "symbol": symbol,
                "score": final_score,
                "details": score_result
            })

    return sorted(approved, key=lambda x: x["score"], reverse=True)