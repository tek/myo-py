from amino import Dat, List


class InfoWidget(Dat['InfoWidget']):

    @staticmethod
    def cons(
            lines: List[str],
    ) -> 'InfoWidget':
        return InfoWidget(
            lines,
        )

    def __init__(self, lines: List[str]) -> None:
        self.lines = lines


__all__ = ('InfoWidget',)
