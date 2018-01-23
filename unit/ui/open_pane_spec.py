from typing import Tuple, Callable, TypeVar

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, do, Do, __, Dat, Just, _, Either, Right, Boolean, Left, L, ADT
from amino.state import State, EitherState
from amino.lenses.lens import lens
from amino.dispatch import PatMat
from amino.boolean import true, false

from ribosome.test.spec import MockNvimFacade
from ribosome import ribo_log

from myo.ui.data.ui import UiData
from myo.ui.data.tree import ViewTree, LayoutNode, PaneNode, pane_by_ident, layout_panes
from myo.ui.data.view import Layout, Pane, ViewGeometry
from myo.ui.data.window import Window, find_principal
from myo.ui.data.space import Space
from myo.ui.data.view_path import pane_path
from myo.components.tmux.tmux import Tmux
from myo.components.tmux.io import TS, TmuxIO
from myo.tmux.data.tmux import TmuxData
from myo.tmux.data.session import Session
from myo.tmux.data.window import Window as TWindow
# from myo.tmux.data.layout import Layout as TLayout, View as TView
from myo.tmux.data.pane import Pane as TPane
from myo.tmux.native.window import NativeWindow
from myo.tmux.native.pane import NativePane
from myo.tmux.window.measure import measure_window, MeasuredLayout, MeasuredPane, MeasuredLayoutNode, MeasuredPaneNode

from unit.tmux.io_spec import start_tmux

D = TypeVar('D')


@do(State[TmuxData, Session])
def add_space(space: Space) -> Do:
    session = Session.cons(space.ident)
    yield State.pure(session)


@do(State[TmuxData, Session])
def find_or_create_session(space: Space) -> Do:
    existing = yield State.inspect(__.session_for_space(space))
    session = existing.cata(lambda err: add_space(space), State.pure)
    yield session


@do(State[TmuxData, TWindow])
def add_window(window: Window) -> Do:
    twindow = TWindow.cons(window.ident)
    yield State.pure(twindow)


@do(State[TmuxData, TWindow])
def find_or_create_window(window: Window) -> Do:
    existing = yield State.inspect(__.window_for_window(window))
    twindow = existing.cata(lambda err: add_window(window), State.pure)
    yield twindow


@do(State[TmuxData, TPane])
def add_pane(pane: Pane) -> Do:
    tpane = TPane.cons(pane.ident)
    yield State.modify(__.add_pane(tpane))
    yield State.pure(tpane)


@do(State[TmuxData, TPane])
def find_or_create_pane(pane: Pane) -> Do:
    existing = yield State.inspect(__.pane_for_pane(pane))
    tpane = existing.cata(lambda err: add_pane(pane), State.pure)
    yield tpane


@do(TS[TmuxData, None])
def create_session(session: Session) -> Do:
    yield TS.lift(TmuxIO.delay(__.create_session(session.name)))


@do(TS[TmuxData, None])
def ensure_session(session: Session) -> Do:
    exists = yield TS.lift(TmuxIO.delay(__.sessions.exists(lambda s: session.id.contains(s.id))))
    yield TS.pure(None) if exists else create_session(session)


@do(TS[TmuxData, NativeWindow])
def create_window(session: Session, window: TWindow) -> Do:
    principal = yield TS.inspect_f(__.principal(window))
    window = yield TS.lift(TmuxIO.delay(__.create_window(session, window)))
    yield TS.modify(__.set_principal_id(window, principal))
    yield TS.from_either(window)


@do(TS)
def add_principal_pane(pane: Pane) -> Do:
    tpane = TPane.cons(pane.ident)
    yield TS.modify(__.append1.panes(tpane))
    yield TS.pure(tpane)


@do(TS[TmuxData, TPane])
def principal_native(session: Session, window: Window, pane: Pane) -> Do:
    twin = yield TS.inspect_f(__.window_for_window(window))
    session_id = yield TS.from_either(session.id.to_either('no session id'))
    window_id = yield TS.from_either(twin.id.to_either('no window id'))
    native_e = yield TS.delay(__.session_window(session_id, window_id))
    native = yield TS.from_either(native_e)
    yield TS.from_either(native.panes.head.to_either(lambda: f'no panes in {native}'))


@do(TS[TmuxData, Tuple[Pane, Pane]])
def principal(window: Window) -> Do:
    pane = yield TS.from_either(find_principal(window))
    existing = yield TS.inspect(__.pane_for_pane(pane))
    tpane = yield existing / TS.pure | (lambda: add_principal_pane(pane))
    yield TS.pure((pane, tpane))


@do(TS[TmuxData, None])
def sync_principal(session: Session, window: Window, nwindow: NativeWindow) -> Do:
    (pane, tpane) = yield principal(window)
    native = yield principal_native(session, window, tpane)
    yield TS.modify(__.update_pane(tpane.copy(id=Just(native.id))))


@do(TS[TmuxData, None])
def ensure_window(session: Session, window: TWindow, ui_window: Window) -> Do:
    @do(Either[str, TmuxIO[Either[str, NativeWindow]]])
    def existing() -> Do:
        sid = yield session.id.to_either('session has no id')
        wid = yield window.id.to_either('window has no id')
        yield Right(TmuxIO.delay(__.session_window(sid, wid)))
    @do(TS[TmuxData, Either[str, NativeWindow]])
    def sync(win_io: TmuxIO[Either[str, NativeWindow]]) -> Do:
        win = yield TS.lift(win_io)
        yield (
            win /
            L(sync_principal)(session, ui_window, _) /
            __.map(Right) |
            (lambda: TS.pure(Left('window not open')))
        )
    win = yield (existing() / sync).value
    yield win / TS.pure | (lambda: create_window(session, window))
    yield TS.unit


@do(TS[TmuxData, NativePane])
def create_pane(session: Session, window: TWindow, pane: TPane) -> Do:
    tpane_e = yield TS.delay(__.create_pane(session, window, pane))
    tpane = yield TS.from_either(tpane_e)
    yield TS.modify(__.set_pane_id(pane, tpane.id))


@do(TS[TmuxData, NativePane])
def ensure_pane_open(session: Session, window: Window, pane: Pane, npane: Either[str, NativePane]) -> Do:
    yield npane / TS.pure | (lambda: create_pane(session, window, pane))


@do(TmuxIO[Either[str, NativePane]])
def native_pane(session: Session, window: TWindow, pane: TPane) -> Do:
    yield TmuxIO.delay(__.pane(session, window, pane))


class EnsureView(PatMat, alg=ViewTree):
    '''synchronize a TmuxData window to tmux.
    After this step, all missing tmux entities are considered fatal.
    '''

    def __init__(self, session: Session, window: TWindow) -> None:
        self.session = session
        self.window = window

    @do(TS[TmuxData, None])
    def layout_node(self, layout: LayoutNode) -> Do:
        yield layout.sub.traverse(self, TS)

    @do(TS[TmuxData, None])
    def pane_node(self, node: PaneNode) -> Do:
        pane = node.data
        tpane = yield find_or_create_pane(node.data).tmux
        pane1 = yield TS.lift(native_pane(self.session, self.window, tpane))
        yield ensure_pane_open(self.session, self.window, tpane, pane1) if pane.open else TS.pure(None)


def pane_for_pane(pane: Pane) -> TS[D, TPane]:
    return TS.inspect_either(__.pane_for_pane(pane))


def pane_id_fatal(pane: Pane) -> TS[D, str]:
    return TS.from_either(pane.id.to_either(lambda: f'pane has no id: {pane}'))


@do(TS[TmuxData, Boolean])
def tmux_pane_open(pane: Pane) -> Do:
    tpane = yield pane_for_pane(pane)
    yield TS.lift(tpane.id.cata(lambda id: TmuxIO.delay(__.pane_open(id)), lambda: TmuxIO.pure(false)))


@do(TS[TmuxData, Either[str, Pane]])
def reference_pane(node: MeasuredLayoutNode) -> Do:
    open = yield layout_panes(node).map(_.data.pane).traverse(lambda p: tmux_pane_open(p).map(__.m(p)), TS)
    yield TS.pure(open.join.head.to_either(f'no open pane in layout'))


@do(TS[TmuxData, None])
def move_pane(pane: Pane, reference: Pane, vertical: Boolean) -> Do:
    tpane = yield pane_for_pane(pane)
    ref_tpane = yield pane_for_pane(reference)
    id = yield pane_id_fatal(tpane)
    ref_id = yield pane_id_fatal(ref_tpane)
    is_open = yield TS.delay(__.pane_open(id))
    direction = '-v' if vertical else '-h'
    yield TS.delay(__.cmd('move-pane', '-s', id, '-t', ref_id, direction)) if is_open else TS.pure(None)


@do(TS[TmuxData, None])
def pack_pane(pane: Pane, reference: Pane, vertical: Boolean) -> Do:
    if pane.open and pane != reference:
        yield move_pane(pane, reference, vertical)
    yield TS.unit


class position_view(PatMat, alg=ViewTree):

    def __init__(self, vertical: Boolean, reference: Pane) -> None:
        self.vertical = vertical
        self.reference = reference

    @do(TS[TmuxData, None])
    def layout_node(self, node: MeasuredLayoutNode) -> Do:
        pane = layout_panes(node).head
        yield pane / _.data.pane / L(pack_pane)(_, self.reference, self.vertical) | TS.unit

    @do(TS[TmuxData, None])
    def pane_node(self, node: MeasuredPaneNode) -> Do:
        yield pack_pane(node.data.pane, self.reference, self.vertical)
        yield TS.unit


class resize_view(PatMat, alg=ViewTree):

    def __init__(self, vertical: Boolean, reference: Pane) -> None:
        self.vertical = vertical
        self.reference = reference

    @do(TS[TmuxData, None])
    def layout_node(self, node: MeasuredLayoutNode) -> Do:
        yield TS.unit

    @do(TS[TmuxData, None])
    def pane_node(self, node: MeasuredPaneNode) -> Do:
        mp = node.data
        size = mp.measures.size
        tpane = yield pane_for_pane(mp.pane)
        id = yield pane_id_fatal(tpane)
        direction = '-x' if self.vertical else '-y'
        ribo_log.debug(f'resize {mp.pane} to {size} ({self.vertical})')
        yield TS.delay(__.cmd('resize-pane', '-t', id, direction, size))


# TODO sort views by `position` attr before positioning
class pack_tree(PatMat, alg=ViewTree):

    def __init__(self, session: Session, window: TWindow, principal: Pane) -> None:
        self.session = session
        self.window = window
        self.principal = principal

    @do(TS[TmuxData, None])
    def layout_node(self, node: MeasuredLayoutNode, vertical: Boolean, reference: Pane) -> Do:
        layout_reference = yield reference_pane(node)
        new_reference = layout_reference | reference
        yield node.sub.traverse(position_view(vertical, reference), TS)
        yield node.sub.traverse(L(self)(_, node.data.layout.vertical, new_reference), TS)
        yield node.sub.traverse(resize_view(vertical, reference), TS)
        yield TS.unit

    @do(TS[TmuxData, None])
    def pane_node(self, node: PaneNode[MeasuredLayout, MeasuredPane], vertical: Boolean, reference: Pane) -> Do:
        yield TS.unit


class WindowState(ADT['WindowState']):
    pass


class PristineWindow(WindowState):

    def __init__(self, native_window: NativeWindow, ui_window: Window, pane: NativePane) -> None:
        self.native_window = native_window
        self.ui_window = ui_window
        self.pane = pane


class TrackedWindow(WindowState):

    def __init__(self, native_window: NativeWindow, ui_window: Window, native: NativePane, pane: TPane) -> None:
        self.native_window = native_window
        self.ui_window = ui_window
        self.native = native
        self.pane = pane


def pane_by_id(id: str) -> TS[TmuxData, Either[str, TPane]]:
    return TS.inspect(__.panes.find(__.id.contains(id)).to_either(lambda: f'no tmux pane for `{id}`'))


@do(TS[TmuxData, WindowState])
def window_state(ui_window: Window, twindow: TWindow) -> Do:
    window_id = yield TS.from_maybe(twindow.id, 'window_state: `{twindow}` has no id')
    native_window_e = yield TS.delay(__.window(window_id))
    native_window = yield TS.from_either(native_window_e)
    panes = yield TS.delay(lambda a: native_window.panes)
    native_pane, tail = yield TS.from_maybe(panes.detach_head, 'no panes in window')
    reference_pane = yield pane_by_id(native_pane.id)
    state = (
        reference_pane
        .map(L(TrackedWindow)(native_window, ui_window, native_pane, _)) |
        L(PristineWindow)(native_window, ui_window, native_pane)
    )
    yield TS.pure(state)


class PackWindow(PatMat, alg=WindowState):

    def __init__(self, session: Session, window: TWindow, principal: Pane) -> None:
        self.session = session
        self.window = window
        self.principal = principal

    @do(TS[TmuxData, None])
    def pristine_window(self, win: PristineWindow) -> Do:
        yield TS.unit
        # yield pack_tree(session, window, ui_princ)(ui_window.layout, false, Left('initial'))

    @do(TS[TmuxData, None])
    def tracked_window(self, win: TrackedWindow) -> Do:
        ref = yield TS.from_either(pane_by_ident(win.pane.pane)(win.ui_window.layout))
        width, height = int(win.native_window.width), int(win.native_window.height)
        measure_tree = measure_window(win.ui_window, width, height)
        yield pack_tree(self.session, self.window, self.principal)(measure_tree, false, ref)


@do(TS[TmuxData, None])
def tmux_open_pane(space: Space, ui_window: Window) -> Do:
    session = yield find_or_create_session(space).tmux
    yield ensure_session(session)
    window = yield find_or_create_window(ui_window).tmux
    yield ensure_window(session, window, ui_window)
    yield EnsureView(session, window)(ui_window.layout)
    ui_princ, t_princ = yield principal(ui_window)
    ws = yield window_state(ui_window, window)
    yield PackWindow(session, window, ui_princ)(ws)


class MapNodes(PatMat, alg=ViewTree):

    def __init__(self, pred: Callable, update: Callable) -> None:
        self.pred = pred
        self.update = update

    def layout_node(self, node: LayoutNode) -> Either[str, ViewTree]:
        def update(new: ViewTree) -> ViewTree:
            return lens.sub.Each().Filter(_.data.ident == new.data.ident).set(new)(node)
        return node.sub.find_map(self) / update

    def pane_node(self, node: PaneNode) -> Either[str, ViewTree]:
        return self.pred(node).e(lambda: 'no match', lambda: self.update(node))


@do(EitherState[UiData, Window])
def ui_open_pane(name: str) -> Do:
    @do(Either[str, Window])
    def find_pane(window: Window) -> Do:
        new = yield MapNodes(lambda a: Boolean(a.data.ident == name), lens.data.open.set(true))(window.layout)
        yield Right(window.copy(layout=new))
    @do(Either[str, Tuple[Space, Window]])
    def find_window(space: Space) -> Do:
        win = yield space.windows.find_map_e(find_pane)
        yield Right((space.replace_window(win), win))
    @do(Either[str, Tuple[UiData, Window]])
    def find_space(ui: UiData) -> Do:
        new, window = yield ui.spaces.find_map_e(find_window).lmap(lambda err: f'pane not found: {name}')
        yield Right((ui.replace_space(new), window))
    data, window = yield EitherState.inspect_f(find_space)
    yield EitherState.set(data)
    yield EitherState.pure(window)


class OPData(Dat['OPData']):

    @staticmethod
    def cons(layout: ViewTree) -> 'OPData':
        windows = List(Window.cons('main', layout=layout))
        spaces = List(Space.cons('main', windows))
        ui = UiData(spaces)
        tm = TmuxData.cons(sessions=List(Session.cons('main', id='$0')), windows=List(TWindow.cons('main', id='@0')))
        return OPData(ui, tm)

    def __init__(self, ui: UiData, tmux: TmuxData) -> None:
        self.ui = ui
        self.tmux = tmux


@do(TS[OPData, None])
def open_pane(name: str) -> Do:
    yield ui_open_pane(name).transform_s_lens(lens.ui).tmux
    a = yield pane_path(name).transform_s_lens(lens.ui).tmux
    yield tmux_open_pane(a.space, a.window).transform_s_lens(lens.tmux)
    yield TS.delay(__.cmd('display-panes'))


class OpenPaneSpec(SpecBase):
    '''
    one pane $one
    two panes in one layout $two_in_one
    four nested layouts $four
    '''

    def setup(self) -> None:
        self.socket = 'op'
        self.proc = start_tmux(self.socket, True)
        self.tmux = Tmux.cons(self.socket)
        vars = dict(op_tmux_socket='op')
        self.vim = MockNvimFacade(prefix='op', vars=vars)
        self._wait(1)

    def teardown(self) -> None:
        self.proc.kill()
        self.proc.wait()
        self.tmux.kill_server()

    def one(self) -> Expectation:
        self._wait(1)
        layout = ViewTree.layout(
            Layout.cons('root'),
            List(ViewTree.pane(Pane.cons('one')))
        )
        data = OPData.cons(layout)
        @do(TS[OPData, None])
        def go() -> Do:
            yield open_pane('one')
        go().nvim.run(data).unsafe(self.vim)
        self._wait(1)
        return k(1) == 1

    def two_in_one(self) -> Expectation:
        layout = ViewTree.layout(
            Layout.cons('root'),
            List(
                ViewTree.layout(
                    Layout.cons('main', false),
                    List(
                        ViewTree.pane(Pane.cons('one')),
                        ViewTree.pane(Pane.cons('two')),
                    )
                ),
                ViewTree.layout(
                    Layout.cons('bottom', false),
                    List(
                        ViewTree.pane(Pane.cons('three')),
                        ViewTree.pane(Pane.cons('four')),
                    )
                )
            )
        )
        data = OPData.cons(layout)
        @do(TS[OPData, None])
        def go() -> Do:
            yield open_pane('one')
            yield open_pane('two')
            self._wait(1)
            yield open_pane('three')
            self._wait(1)
            yield open_pane('four')
        go().nvim.run(data).unsafe(self.vim)
        self._wait(1)
        return k(1) == 1

    def four(self) -> Expectation:
        self._wait(1)
        layout = ViewTree.layout(
            Layout.cons('root'),
            List(
                ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(min_size=40))),
                ViewTree.layout(
                    Layout.cons('main', vertical=false),
                    List(
                        ViewTree.pane(Pane.cons('two')),
                        ViewTree.layout(
                            Layout.cons('sub1'),
                            List(
                                ViewTree.pane(Pane.cons('three')),
                                ViewTree.layout(
                                    Layout.cons('sub2', vertical=false),
                                    List(
                                        ViewTree.pane(Pane.cons('four')),
                                        ViewTree.pane(Pane.cons('five')),
                                    )
                                )
                            )
                        )
                    )
                ),
            )
        )
        data = OPData.cons(layout)
        @do(TS[OPData, None])
        def go() -> Do:
            yield open_pane('one')
            yield open_pane('two')
            yield open_pane('three')
            yield open_pane('four')
            # yield open_pane('five')
        go().nvim.run(data).unsafe(self.vim)
        self._wait(1)
        return k(1) == 1


__all__ = ('OpenPaneSpec',)
