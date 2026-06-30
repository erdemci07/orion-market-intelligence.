from config import AUTO_TRADE
from services.exchange_client import ExchangeClient


class OrderEngine:
    def __init__(self):
        self.exchange = ExchangeClient()

    def buy(self, symbol, usdt_amount):
        if not AUTO_TRADE:
            print(f"[SIMULATION BUY] {symbol} - {usdt_amount} USDT")
            return {
                "mode": "SIMULATION",
                "side": "BUY",
                "symbol": symbol,
                "usdt_amount": usdt_amount,
                "executed_price": None,
                "executed_quantity": None,
                "order_id": None,
                "status": "SUCCESS"
            }

        print(f"[TESTNET/LIVE BUY] {symbol} - {usdt_amount} USDT")

        order = self.exchange.buy_market(
            symbol=symbol,
            usdt_amount=usdt_amount
        )

        return self._parse_order(order, "BUY")

    def sell(self, symbol, quantity):
        if not AUTO_TRADE:
            print(f"[SIMULATION SELL] {symbol} - {quantity}")
            return {
                "mode": "SIMULATION",
                "side": "SELL",
                "symbol": symbol,
                "quantity": quantity,
                "executed_price": None,
                "executed_quantity": quantity,
                "order_id": None,
                "status": "SUCCESS"
            }

        print(f"[TESTNET/LIVE SELL] {symbol} - {quantity}")

        order = self.exchange.sell_market(
            symbol=symbol,
            quantity=quantity
        )

        return self._parse_order(order, "SELL")

    def _parse_order(self, order, side):
        fills = order.get("fills", [])

        executed_quantity = float(order.get("executedQty", 0))
        total_quote = 0

        for fill in fills:
            price = float(fill["price"])
            qty = float(fill["qty"])
            total_quote += price * qty

        executed_price = None

        if executed_quantity > 0:
            executed_price = total_quote / executed_quantity

        return {
            "mode": "TESTNET_OR_LIVE",
            "side": side,
            "symbol": order.get("symbol"),
            "order_id": order.get("orderId"),
            "status": order.get("status"),
            "executed_price": executed_price,
            "executed_quantity": executed_quantity,
            "raw": order
        }