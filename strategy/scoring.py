def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(value, max_value))


def score_ema(data):
    score = 0

    if data["ema21"] > data["ema50"]:
        score += 35

    if data["ema50"] > data["ema200"]:
        score += 35

    if data["price"] > data["ema21"]:
        score += 30

    return clamp(score)


def score_rsi(data):
    rsi = data["rsi"]

    if 50 <= rsi <= 62:
        return clamp(100 - abs(56 - rsi) * 3)

    if 62 < rsi <= 70:
        return clamp(85 - (rsi - 62) * 4)

    if 45 <= rsi < 50:
        return clamp(45 + (rsi - 45) * 8)

    if 70 < rsi <= 80:
        return clamp(45 - (rsi - 70) * 3)

    return 0


def score_macd(data):
    if data["macd_hist"] <= 0:
        return 0

    return clamp(data["macd_hist"] * 70)


def score_adx(data):
    adx = data["adx"]

    if adx < 18:
        return 0

    return clamp((adx - 18) * 6)

def score_volume(data):
    if data["avg_volume"] <= 0:
        return 0

    ratio = data["volume"] / data["avg_volume"]

    if ratio >= 2:
        return 100

    if ratio >= 1.5:
        return 80

    if ratio >= 1.1:
        return 60

    if ratio >= 0.9:
        return 40

    if ratio >= 0.7:
        return 20

    return 0


def score_structure(data):
    if data["higher_high"] and data["higher_low"]:
        return 100

    if data["higher_low"]:
        return 60

    if data["higher_high"]:
        return 40

    return 0


def score_fibonacci(data):
    price = data["price"]

    if price >= data["fib_382"]:
        return 85

    if price >= data["fib_500"]:
        return 65

    if price >= data["fib_618"]:
        return 40

    return 10


def score_symbol(data):
    scores = {
        "ema": score_ema(data),
        "rsi": score_rsi(data),
        "macd": score_macd(data),
        "adx": score_adx(data),
        "volume": score_volume(data),
        "structure": score_structure(data),
        "fibonacci": score_fibonacci(data),
    }

    final_score = (
        scores["structure"] * 0.30 +
        scores["ema"] * 0.20 +
        scores["adx"] * 0.15 +
        scores["volume"] * 0.15 +
        scores["rsi"] * 0.08 +
        scores["macd"] * 0.07 +
        scores["fibonacci"] * 0.05
    )

    return {
        "final_score": round(final_score, 2),
        "scores": scores
    }