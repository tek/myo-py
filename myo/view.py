from amino import List


class View():
    pass


class Views():

    def __init__(self, views: List[View]=List()) -> None:
        self.views = views

    def __add__(self, view: View):
        return Views(self.views + [view])

__all__ = ('Views', 'View')
