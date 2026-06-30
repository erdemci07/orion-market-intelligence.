import requests


class SentimentClient:
    def get_fear_greed_index(self):
        url = "https://api.alternative.me/fng/"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()["data"][0]

            return {
                "value": int(data["value"]),
                "classification": data["value_classification"],
                "timestamp": data["timestamp"]
            }

        except Exception as e:
            print("Fear & Greed verisi alınamadı:", e)

            return {
                "value": 50,
                "classification": "Neutral",
                "timestamp": None
            }