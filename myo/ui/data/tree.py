import abc
from typing import Generic, TypeVar, Union

from amino import ADT, List, Nil, Either, Right, Left, Boolean, __
from amino.dispatch import PatMat

from myo.ui.data.view import View, Layout, Pane


# class ViewTree(ADT['ViewTree']):

#     @staticmethod
#     def layout(
#             data: Layout,
#             sub: List['ViewTree']=Nil,
#     ) -> 'ViewTree':
#         return LayoutNode(data, sub)

#     @staticmethod
#     def pane(data: Pane) -> 'ViewTree':
#         return PaneNode(data)

#     @abc.abstractproperty
#     def view(self) -> View:
#         ...

#     @abc.abstractmethod
#     def pane_by_ident(self, ident: str) -> Either[str, Pane]:
#         ...


# class PaneNode(ViewTree):

#     def __init__(self, data: Pane) -> None:
#         self.data = data

#     @property
#     def view(self) -> View:
#         return self.data

#     def pane_by_ident(self, ident: str) -> Either[str, Pane]:
#         return Right(self.data) if self.data.ident == ident else Left(f'pane ident does not match')


# class LayoutNode(ViewTree):

#     def __init__(self, data: Layout, sub: List[ViewTree]) -> None:
#         self.data = data
#         self.sub = sub

#     @property
#     def view(self) -> View:
#         return self.data

#     @property
#     def reference(self) -> Either[str, Pane]:
#         def pred(node: ViewTree) -> Either[str, Pane]:
#             return (
#                 (
#                     Right(node.data)
#                     if node.data.open else
#                     Left('pane closed')
#                 )
#                 if isinstance(node, PaneNode) else
#                 node.reference
#             )
#         return self.sub.find_map_e(pred).lmap(lambda a: 'no open pane in layout')

#     @property
#     def panes(self) -> List[PaneNode]:
#         return self.sub.filter(Boolean.is_a(PaneNode))

#     def pane_by_ident(self, ident: str) -> Either[str, Pane]:
#         return self.sub.find_map_e(__.pane_by_ident(ident)).to_either(lambda: f'no pane `{ident}` in {self}')


A = TypeVar('A')
B = TypeVar('B')


class ViewTree(Generic[A, B], ADT['ViewTree[A, B]']):

    @staticmethod
    def layout(
            data: A,
            sub: List['ViewTree[A, B]']=Nil,
    ) -> 'ViewTree[A, B]':
        return LayoutNode(data, sub)

    @staticmethod
    def pane(data: B) -> 'ViewTree[A, B]':
        return PaneNode(data)


class PaneNode(Generic[A, B], ViewTree[A, B]):

    def __init__(self, data: B) -> None:
        self.data = data


class LayoutNode(Generic[A, B], ViewTree[A, B]):

    def __init__(self, data: A, sub: List[ViewTree[A, B]]) -> None:
        self.data = data
        self.sub = sub


class reference_node(PatMat, alg=ViewTree):

    def pane_node(self, node: PaneNode[Layout, Pane]) -> Either[str, Pane]:
        return Right(node.data) if node.data.open else Left('pane closed')

    def layout_node(self, node: LayoutNode[Layout, Layout]) -> Either[str, Layout]:
        return node.sub.find_map_e(self).lmap(lambda a: 'no open pane in layout')


class pane_by_ident(PatMat, alg=ViewTree):

    def __init__(self, ident: str) -> None:
        self.ident = ident

    def pane_node(self, node: PaneNode[A, Pane]) -> Either[str, Pane]:
        return Right(node.data) if node.data.ident == self.ident else Left(f'pane ident does not match')

    def layout_node(self, node: LayoutNode[A, Pane]) -> Either[str, Pane]:
        return node.sub.find_map_e(self).to_either(lambda: f'no pane `{self.ident}` in {node}')


def layout_panes(node: LayoutNode) -> List[PaneNode]:
    return node.sub.filter(Boolean.is_a(PaneNode))


__all__ = ('ViewTree', 'PaneNode', 'LayoutNode', 'reference_node', 'pane_by_ident', 'layout_panes')
