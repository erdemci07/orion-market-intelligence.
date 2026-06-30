from services.storage import get_open_positions


class PositionEngine:

    def run(self):

        positions = get_open_positions()

        print(

            "Açık pozisyon:",

            len(positions)

        )

        return positions