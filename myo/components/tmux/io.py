import abc
import inspect
from traceback import FrameSummary
from typing import TypeVar, Callable, Any, Generic, Generator, Union, Tuple
from threading import Thread

from amino.tc.base import ImplicitInstances, F, TypeClass, tc_prop
from amino.lazy import lazy
from amino.tc.monad import Monad
from amino import Either, __, IO, Maybe, Left, Eval, List, Right, Lists, options, Nil, Try, Path
from amino.state import tcs, StateT, State, EitherState
from amino.func import CallByName, tailrec
from amino.do import do
from amino.util.exception import format_exception
from amino.dat import ADT

from ribosome.nvim.io import ToNvimIOState, NS
from ribosome.nvim import NvimIO, NvimFacade

from myo.components.tmux.tmux import Tmux

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
S = TypeVar('S')


def cframe() -> FrameSummary:
    return inspect.currentframe()


def callsite(frame) -> Any:
    def loop(f) -> None:
        pkg = f.f_globals.get('__package__', '')
        mod = f.f_globals.get('__module__', '')
        return loop(f.f_back) if mod == 'myo.components.tmux.io' or pkg.startswith('amino') else f
    return loop(frame)


def callsite_info(frame: FrameSummary) -> List[str]:
    cs = callsite(frame)
    source = inspect.getsourcefile(cs.f_code)
    line = cs.f_lineno
    code = Try(Path, source) // (lambda a: Try(a.read_text)) / Lists.lines // __.lift(line - 1) | '<no source>'
    fun = cs.f_code.co_name
    clean = code.strip()
    return List(f'  File "{source}", line {line}, in {fun}', f'    {clean}')


def callsite_source(frame) -> Tuple[List[str], int]:
    cs = callsite(frame)
    source = inspect.getsourcefile(cs.f_code)
    return Try(Path, source) // (lambda a: Try(a.read_text)) / Lists.lines // __.lift(cs.f_lineno - 1) | '<no source>'


class TmuxIOException(Exception):

    def __init__(self, f, stack, cause, frame=None) -> None:
        self.f = f
        self.stack = List.wrap(stack)
        self.cause = cause
        self.frame = frame

    @property
    def lines(self) -> List[str]:
        cause = format_exception(self.cause)
        cs = callsite_info(self.frame)
        return List(f'TmuxIO exception') + cs + cause[-3:]

    def __str__(self):
        return self.lines.join_lines

    @property
    def callsite(self) -> Any:
        return callsite(self.frame)

    @property
    def callsite_source(self) -> List[str]:
        return callsite_source(self.frame)


class TmuxIOInstances(ImplicitInstances):

    @lazy
    def _instances(self) -> 'amino.map.Map':
        from amino.map import Map
        return Map({Monad: TmuxIOMonad()})


class TResult(Generic[A], ADT['TmuxIOResult[A]']):

    @abc.abstractproperty
    def to_either(self) -> Either[Exception, A]:
        ...


class TSuccess(Generic[A], TResult[A]):

    def __init__(self, value: A) -> None:
        self.value = value

    @property
    def to_either(self) -> Either[Exception, A]:
        return Right(self.value)


class TError(Generic[A], TResult[A]):

    def __init__(self, error: str) -> None:
        self.error = error

    @property
    def to_either(self) -> Either[Exception, A]:
        return Left(Exception(self.error))


class TFatal(Generic[A], TResult[A]):

    def __init__(self, exception: Exception) -> None:
        self.exception = exception

    @property
    def to_either(self) -> Either[Exception, A]:
        return Left(self.exception)


class TmuxIO(Generic[A], F[A], ADT['TmuxIO'], implicits=True, imp_mod='myo.components.tmux.io',
             imp_cls='TmuxIOInstances'):
    debug = options.io_debug.exists

    @staticmethod
    def wrap_either(f: Callable[[Tmux], Either[B, A]], frame: FrameSummary=None) -> 'TmuxIO[A]':
        return TmuxIO.suspend(lambda a: f(a).cata(TmuxIO.error, TmuxIO.pure), _frame=frame)

    @staticmethod
    def from_either(e: Either[str, A], frame: FrameSummary=None) -> 'TmuxIO[A]':
        return TmuxIO.wrap_either(lambda v: e, frame)

    @staticmethod
    def from_maybe(e: Maybe[A], error: CallByName) -> 'TmuxIO[A]':
        return TmuxIO.from_either(e.to_either(error))

    @staticmethod
    def cmd_sync(cmdline: str, verbose=False) -> 'TmuxIO[str]':
        return TmuxIO.wrap_either(__.cmd_sync(cmdline, verbose=verbose))

    @staticmethod
    def cmd(cmdline: str, verbose=False) -> 'TmuxIO[str]':
        return TmuxIO.wrap_either(__.cmd(cmdline, verbose=verbose))

    @staticmethod
    def call(name: str, *args: Any, **kw: Any) -> 'TmuxIO[A]':
        return TmuxIO.wrap_either(__.call(name, *args, **kw))

    @staticmethod
    def call_once_defined(name: str, *args: Any, **kw: Any) -> 'TmuxIO[A]':
        return TmuxIO.wrap_either(__.call_once_defined(name, *args, **kw))

    @staticmethod
    def exception(exc: Exception) -> 'TmuxIO[A]':
        return TmuxIOFatal(exc)

    @staticmethod
    def failed(msg: str) -> 'TmuxIO[A]':
        return TmuxIO.exception(Exception(msg))

    @staticmethod
    def error(msg: str) -> 'TmuxIO[A]':
        return TmuxIOError(msg)

    @staticmethod
    def from_io(io: IO[A]) -> 'TmuxIO[A]':
        return TmuxIO.delay(lambda a: io.attempt.get_or_raise())

    @staticmethod
    def fork(f: Callable[[Tmux], None]) -> 'TmuxIO[None]':
        return TmuxIO.delay(lambda v: Thread(target=f, args=(v,)).start())

    @staticmethod
    def delay(f: Callable[..., A], *a: Any, **kw: Any) -> 'TmuxIO[A]':
        def g(tmux: Tmux) -> A:
            return Pure(f(tmux, *a, **kw))
        return Suspend(g)

    @staticmethod
    def simple(f: Callable[..., A], *a, **kw) -> 'TmuxIO[A]':
        return TmuxIO.delay(lambda v: f(*a, **kw))

    @staticmethod
    def suspend(f: Callable[..., 'TmuxIO[A]'], *a: Any, _frame: FrameSummary=None, **kw: Any) -> 'TmuxIO[A]':
        def g(tmux: Tmux) -> TmuxIO[A]:
            return f(tmux, *a, **kw)
        return Suspend(g, _frame)

    @staticmethod
    def pure(a: A) -> 'TmuxIO[A]':
        return Pure(a)

    @staticmethod
    def unit() -> 'TmuxIO[A]':
        return TmuxIO.pure(None)

    @abc.abstractmethod
    def _flat_map(self, f: Callable[[A], 'TmuxIO[B]'], ts: Eval[str], fs: Eval[str]) -> 'TmuxIO[B]':
        ...

    @abc.abstractmethod
    def step(self, tmux: Tmux) -> 'TmuxIO[A]':
        ...

    def __init__(self, frame=None) -> None:
        self.frame = frame or inspect.currentframe()

    def flat_map(self, f: Callable[[A], 'TmuxIO[B]']) -> 'TmuxIO[B]':
        return self._flat_map(f)

    def run(self, tmux: Tmux) -> A:
        @tailrec
        def run(t: 'TmuxIO[A]') -> Union[Tuple[bool, A], Tuple[bool, Tuple[Union[A, 'TmuxIO[A]']]]]:
            if isinstance(t, Pure):
                return True, (t.value,)
            elif isinstance(t, (Suspend, BindSuspend)):
                return True, (t.step(tmux),)
            elif isinstance(t, TmuxIOError):
                return False, TError(t.error)
            elif isinstance(t, TmuxIOFatal):
                return False, TFatal(t.exception)
            else:
                return False, TSuccess(t)
        return run(self)

    def result(self, tmux: Tmux) -> TResult[A]:
        try:
            return self.run(tmux)
        except TmuxIOException as e:
            return TFatal(e)

    def either(self, tmux: Tmux) -> Either[TmuxIOException, A]:
        try:
            return self.run(tmux).to_either
        except TmuxIOException as e:
            return Left(e)

    def attempt(self, tmux: Tmux) -> Either[TmuxIOException, A]:
        return self.either(tmux)

    def unsafe(self, tmux: Tmux) -> A:
        return self.either(tmux).get_or_raise()

    def recover(self, f: Callable[[Exception], B]) -> 'TmuxIO[B]':
        return TmuxIO.delay(self.attempt).map(__.value_or(f))

    # FIXME use TResult
    @do('TmuxIO[A]')
    def ensure(self, f: Callable[[Either[Exception, A]], 'TmuxIO[None]']) -> Generator:
        result = yield TmuxIO.delay(self.attempt)
        yield f(result)
        yield TmuxIO.from_either(result)

    def effect(self, f: Callable[[A], Any]) -> 'TmuxIO[A]':
        def wrap(v: Tmux) -> A:
            ret = self.run(v)
            f(ret)
            return ret
        return TmuxIO.delay(wrap)

    __mod__ = effect

    def error_effect(self, f: Callable[[Exception], None]) -> 'TmuxIO[A]':
        return self.ensure(lambda a: TmuxIO.delay(lambda v: a.leffect(f)))

    def error_effect_f(self, f: Callable[[Exception], 'TmuxIO[None]']) -> 'TmuxIO[A]':
        return self.ensure(lambda a: TmuxIO.suspend(lambda v: a.cata(f, TmuxIO.pure)))

    @property
    def callsite_l1(self) -> str:
        return callsite_source(self.frame)[0][0]


class Suspend(Generic[A], TmuxIO[A]):

    def __init__(self, thunk: Callable[[Tmux], TmuxIO[A]], frame: FrameSummary=None) -> None:
        super().__init__(frame)
        self.thunk = thunk

    def step(self, tmux: Tmux) -> TmuxIO[A]:
        try:
            return self.thunk(tmux)
        except TmuxIOException as e:
            raise e
        except Exception as e:
            raise TmuxIOException('', Nil, e, self.frame)

    def _flat_map(self, f: Callable[[A], TmuxIO[B]]) -> TmuxIO[B]:
        return BindSuspend(self.thunk, f, self.frame)


class BindSuspend(Generic[A, B], TmuxIO[B]):

    def __init__(self, thunk: Callable[[Tmux], TmuxIO[A]], f: Callable[[A], TmuxIO[B]], frame: FrameSummary
                 ) -> None:
        super().__init__(frame)
        self.thunk = thunk
        self.f = f

    def step(self, tmux: Tmux) -> TmuxIO[B]:
        try:
            step = self.thunk(tmux)
        except TmuxIOException as e:
            raise e
        except Exception as e:
            raise TmuxIOException('', Nil, e, self.frame)
        try:
            return step.flat_map(self.f)
        except TmuxIOException as e:
            raise e
        except Exception as e:
            raise TmuxIOException('', Nil, e, step.frame)

    def _flat_map(self, f: Callable[[B], TmuxIO[C]]) -> TmuxIO[C]:
        def bs(tmux: Tmux) -> TmuxIO[C]:
            return BindSuspend(self.thunk, lambda a: self.f(a).flat_map(f), self.frame)
        return Suspend(bs)


class Pure(Generic[A], TmuxIO[A]):

    def __init__(self, value: A) -> None:
        super().__init__()
        self.value = value

    def _arg_desc(self) -> List[str]:
        return List(str(self.value))

    def step(self, tmux: Tmux) -> TmuxIO[A]:
        return self

    def _flat_map(self, f: Callable[[A], TmuxIO[B]]) -> TmuxIO[B]:
        def g(tmux: Tmux) -> TmuxIO[B]:
            return f(self.value)
        return Suspend(g)


class TmuxIOError(Generic[A], TmuxIO[A]):

    def __init__(self, error: str) -> None:
        self.error = error

    def _flat_map(self, f: Callable[[A], TmuxIO[B]]) -> TmuxIO[B]:
        return self

    def step(self, tmux: Tmux) -> TmuxIO[A]:
        return self


class TmuxIOFatal(Generic[A], TmuxIO[A]):

    def __init__(self, exception: Exception) -> None:
        self.exception = exception

    def _flat_map(self, f: Callable[[A], TmuxIO[B]]) -> TmuxIO[B]:
        return self

    def step(self, tmux: Tmux) -> TmuxIO[A]:
        return self


class TmuxIOMonad(Monad[TmuxIO]):

    def pure(self, a: A) -> TmuxIO[A]:
        return TmuxIO.pure(a)

    def flat_map(self, fa: TmuxIO[A], f: Callable[[A], TmuxIO[B]]) -> TmuxIO[B]:
        return fa.flat_map(f)


class TmuxIOState(Generic[S, A], StateT[TmuxIO, S, A], tpe=TmuxIO):

    @staticmethod
    def io(f: Callable[[Tmux], A]) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.delay(f))

    @staticmethod
    def delay(f: Callable[[Tmux], A]) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.delay(f))

    @staticmethod
    def suspend(f: Callable[[Tmux], TmuxIO[A]]) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.suspend(f))

    @staticmethod
    def from_io(io: IO[A]) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.wrap_either(lambda v: io.attempt))

    @staticmethod
    def from_id(st: State[S, A]) -> 'TmuxIOState[S, A]':
        return st.transform_f(TmuxIOState, lambda s: TmuxIO.pure(s.value))

    @staticmethod
    def from_either_state(st: EitherState[S, A]) -> 'TmuxIOState[S, A]':
        return st.transform_f(TmuxIOState, lambda s: TmuxIO.from_either(s))

    @staticmethod
    def from_either(e: Either[str, A]) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.from_either(e))

    @staticmethod
    def failed(e: str) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.failed(e))

    @staticmethod
    def error(e: str) -> 'TmuxIOState[S, A]':
        return TmuxIOState.lift(TmuxIO.error(e))

    @staticmethod
    def inspect_either(f: Callable[[S], Either[str, A]]) -> 'TmuxIOState[S, A]':
        frame = cframe()
        return TmuxIOState.inspect_f(lambda s: TmuxIO.from_either(f(s), frame))


tcs(TmuxIO, TmuxIOState)
TS = TmuxIOState


class ToTmuxIOState(TypeClass):

    @abc.abstractproperty
    def tmux(self) -> TS:
        ...


class IdStateToTmuxIOState(ToTmuxIOState, tpe=State):

    @tc_prop
    def tmux(self, fa: State[S, A]) -> TS:
        return TmuxIOState.from_id(fa)


class EitherStateToTmuxIOState(ToTmuxIOState, tpe=EitherState):

    @tc_prop
    def tmux(self, fa: EitherState[S, A]) -> TS:
        return TmuxIOState.from_either_state(fa)


def tmux_from_vim(vim: NvimFacade) -> Tmux:
    socket = vim.vars.p('tmux_socket') | None
    return Tmux.cons(socket=socket)


class TmuxStateToNvimIOState(ToNvimIOState, tpe=TmuxIOState):

    @tc_prop
    def nvim(self, fa: TmuxIOState[S, A]) -> NS:
        def tmux_to_nvim(tm: TmuxIO[A]) -> NvimIO[A]:
            return NvimIO.suspend(lambda v: NvimIO.from_either(tm.either(tmux_from_vim(v))))
        return fa.transform_f(NS, tmux_to_nvim)


__all__ = ('TmuxIO', 'TmuxIOState', 'TS')
