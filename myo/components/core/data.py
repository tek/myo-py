from amino import Dat


class CoreData(Dat['CoreData']):

    @staticmethod
    def cons() -> 'CoreData':
        return CoreData()

    def __init__(self) -> None:
        pass


__all__ = ('CoreData',)
