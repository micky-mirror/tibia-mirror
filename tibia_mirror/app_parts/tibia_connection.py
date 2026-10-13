"""The connection to Tibia."""

from tibia_mirror.services.game import Game


class TibiaConnection:
    """Knows if Tibia is running and if its window can be seen."""

    def __init__(self) -> None:
        self._game = Game()
        self._look_for_tibia()

    @property
    def state(self) -> str:
        """The state of the connection: WAITING, MINIMIZED or CONNECTED."""
        return self._game.state

    def _look_for_tibia(self) -> None:
        """Find Tibia's window and read where its client area is."""
        self._game.find()
        self._game.current_client()
