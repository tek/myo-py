from tryp import List


class View(object):
    pass


class Views(object):

    def __init__(self, views: List[View]=List()) -> None:
        self.views = views

__all__ = ['Views', 'View']
