from typing import Tuple, Callable

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, do, Do, __, Dat, Just, Nil, _, Either, Right, Boolean, Left, L
from amino.state import State, EitherState
from amino.lenses.lens import lens
from amino.dispatch import PatMat
from amino.boolean import true

from ribosome.nvim.io import NS
from ribosome.test.spec import MockNvimFacade

from myo.ui.data.ui import UiData
from myo.ui.data.tree import ViewTree, LayoutNode, PaneNode
from myo.ui.data.view import Layout, Pane, View
from myo.ui.data.window import Window, find_principal
from myo.ui.data.space import Space
from myo.ui.data.view_path import pane_path
from myo.components.tmux.tmux import Tmux
from myo.components.tmux.io import TS, TmuxIO
from myo.tmux.data.tmux import TmuxData
from myo.tmux.data.session import Session
from myo.tmux.data.window import Window as TWindow
from myo.tmux.data.layout import Layout as TLayout, View as TView
from myo.tmux.data.pane import Pane as TPane
from myo.tmux.window import NativeWindow
from myo.tmux.pane import NativePane

from unit.tmux.io_spec import start_tmux


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
    yield State.pure(tpane)


@do(State[TmuxData, TPane])
def find_or_create_pane(pane: Pane) -> Do:
    existing = yield State.inspect(__.pane_for_pane(pane))
    tpane = existing.cata(lambda err: add_pane(pane), State.pure)
    yield tpane


@do(TS[TmuxData, Tuple[TView, List[TLayout]]])
def find_or_create_views(view: View, layouts: List[Layout]) -> Do:
    layouts = yield TS.inspect(_.layouts)
    def step(h: Layout, tail: List[Layout]) -> None:
        tl = layouts.find(_.layout)
        return
    l = layouts.detach_head.map2(step)
    yield TS.pure((view, Nil))


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
    native_e = yield TS.delay(__.window(session_id, window_id))
    native = yield TS.from_either(native_e)
    yield TS.from_either(native.panes.head.to_either(lambda: f'no panes in {native}'))


@do(TS[TmuxData, TPane])
def principal(window: Window) -> Do:
    ui_pr = yield TS.from_either(find_principal(window))
    existing = yield TS.inspect(__.pane_for_pane(ui_pr))
    yield existing / TS.pure | (lambda: add_principal_pane(ui_pr))


@do(TS[TmuxData, None])
def sync_principal(session: Session, window: Window, nwindow: NativeWindow) -> Do:
    princ = yield principal(window)
    native = yield principal_native(session, window, princ)
    yield TS.modify(__.update_pane(princ.copy(id=Just(native.id))))


@do(TS[TmuxData, None])
def ensure_window(session: Session, window: TWindow, ui_window: Window) -> Do:
    @do(Either[str, TmuxIO[Either[str, NativeWindow]]])
    def existing() -> Do:
        sid = yield session.id.to_either('session has no id')
        wid = yield window.id.to_either('window has no id')
        yield Right(TmuxIO.delay(__.window(sid, wid)))
    @do(TS[TmuxData, Either[str, NativeWindow]])
    def sync(win_io: TmuxIO[Either[str, NativeWindow]]) -> Do:
        win = yield TS.lift(win_io)
        yield win / L(sync_principal)(session, ui_window, _) / __.map(Right) | (lambda: TS.pure(Left('window not open')))
    win = yield (existing() / sync).value
    yield win / TS.pure | (lambda: create_window(session, window))
    yield TS.unit


@do(TS[TmuxData, NativePane])
def create_pane(session: Session, window: TWindow, pane: TPane) -> Do:
    pane = yield TS.lift(TmuxIO.delay(__.create_pane(session, window, pane)))
    yield TS.from_either(pane)


@do(TS[TmuxData, NativePane])
def ensure_pane_open(session: Session, window: Window, pane: Pane, npane: Either[str, NativePane]) -> Do:
    yield npane / TS.pure | (lambda: create_pane(session, window, pane))


@do(TmuxIO[Either[str, NativePane]])
def native_pane(session: Session, window: TWindow, pane: TPane) -> Do:
    yield TmuxIO.delay(__.pane(session, window, pane))


class EnsureView(PatMat, alg=ViewTree):

    def __init__(self, session: Session, window: TWindow) -> None:
        self.session = session
        self.window = window

    @do(TS[TmuxData, None])
    def layout_node(self, layout: LayoutNode, stack: List[LayoutNode]) -> Do:
        yield layout.sub.zip_const(stack.cons(layout)).traverse2(self, TS)

    @do(TS[TmuxData, None])
    def pane_node(self, node: PaneNode, stack: List[LayoutNode]) -> Do:
        pane = node.data
        tpane = yield find_or_create_pane(node.data).tmux
        pane1 = yield TS.lift(native_pane(self.session, self.window, tpane))
        yield ensure_pane_open(self.session, self.window, tpane, pane1) if pane.open else TS.pure(None)


@do(TS[TmuxData, None])
def tmux_open_pane(space: Space, ui_window: Window) -> Do:
    session = yield find_or_create_session(space).tmux
    yield ensure_session(session)
    window = yield find_or_create_window(ui_window).tmux
    yield ensure_window(session, window, ui_window)
    yield EnsureView(session, window)(ui_window.layout, Nil)


class TraverseViewTree(PatMat, alg=ViewTree):

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
        new = yield TraverseViewTree(lambda a: Boolean(a.data.ident == name), lens.data.open.set(true))(window.layout)
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


@do(NS)
def open_pane(name: str) -> Do:
    yield ui_open_pane(name).transform_s_lens(lens.ui).nvim
    a = yield pane_path(name).transform_s_lens(lens.ui).nvim
    yield tmux_open_pane(a.space, a.window).transform_s_lens(lens.tmux).nvim


class OPData(Dat['OPData']):

    def __init__(self, ui: UiData, tmux: TmuxData) -> None:
        self.ui = ui
        self.tmux = tmux


# TODO
# first, update UiData to match the desired state, i.e. the pane is open
# then invalidate the window state and redraw its contents, passing over to tmux
# no view path needed in tmux
# this was only necessary before because the update and the redraw were done in one step
class OpenPaneSpec(SpecBase):
    '''
    test $test
    '''

    def setup(self) -> None:
        self.socket = 'op'
        self.proc = start_tmux(self.socket, True)
        self.tmux = Tmux.cons(self.socket)

    def teardown(self) -> None:
        self.proc.kill()
        self.proc.wait()
        self.tmux.kill_server()

    def test(self) -> Expectation:
        self._wait(1)
        layout = ViewTree.layout(
            Layout.cons('root'),
            List(
                ViewTree.layout(Layout.cons('main'), List(ViewTree.pane(Pane.cons('one')))),
                ViewTree.pane(Pane.cons('two'))
            )
        )
        windows = List(Window.cons('main', layout=layout))
        spaces = List(Space.cons('main', windows))
        ui = UiData(spaces)
        tm = TmuxData.cons(sessions=List(Session.cons('main', id='$0')), windows=List(TWindow.cons('main', id='@0')))
        data = OPData(ui, tm)
        vars = dict(op_tmux_socket='op')
        vim = MockNvimFacade(prefix='op', vars=vars)
        (open_pane('one') // (lambda a: open_pane('two'))).run(data).unsafe(vim)
        self._wait(1)
        return k(1) == 1


__all__ = ('OpenPaneSpec',)
