from chiasma.data.view_tree import ViewTree, LayoutNode, PaneNode

from myo.ui.data.view import Layout, Pane


MyoViewTree = ViewTree[Layout, Pane]
MyoLayoutNode = LayoutNode[Layout, Pane]
MyoPaneNode = PaneNode[Layout, Pane]

__all__ = ('MyoViewTree', 'MyoLayoutNode', 'MyoPaneNode',)
