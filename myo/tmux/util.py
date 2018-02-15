from amino import List


def format_pane(pane):
    return List(pane.desc)


def format_layout(lay):
    return (List(lay.desc) + indent(lay.layouts // format_layout) +
            indent(lay.panes // format_pane))


def indent(lines):
    return lines / '  {}'.format


def format_window(win):
    return List(win.desc) + indent(format_layout(win.root))


def format_state(state) -> List[str]:
    return state.all_windows // format_window


__all__ = ('format_state', 'format_window', 'indent', 'format_layout', 'format_pane')
