import abc

from amino import ADT, List, Nil

from myo.ui.data.view import View, Layout, Pane


class ViewTree(ADT['ViewTree']):

    @staticmethod
    def layout(
            data: Layout,
            sub: List['ViewTree']=Nil,
    ) -> 'ViewTree':
        return LayoutNode(data, sub)

    @staticmethod
    def pane(data: Pane) -> 'ViewTree':
        return PaneNode(data)

    @abc.abstractproperty
    def view(self) -> View:
        ...


class LayoutNode(ViewTree):

    def __init__(self, data: Layout, sub: List[ViewTree]) -> None:
        self.data = data
        self.sub = sub

    @property
    def view(self) -> View:
        return self.data


class PaneNode(ViewTree):

    def __init__(self, data: Pane) -> None:
        self.data = data

    @property
    def view(self) -> View:
        return self.data


__all__ = ('ViewTree',)
