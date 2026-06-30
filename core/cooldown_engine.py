from database.repository import is_symbol_in_cooldown


class CooldownEngine:
    def can_trade(self, symbol):
        return not is_symbol_in_cooldown(symbol)