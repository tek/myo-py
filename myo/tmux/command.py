from typing import TypeVar, Callable

from amino import List, Either, Map, Lists, do, Do, _, L, Try

from myo.tmux.io.compute import TmuxIO


def tmux_fmt_attr(attr: str) -> str:
    return f'#{{{attr}}}'


def tmux_fmt_attrs(attrs: List[str]) -> str:
    raw = (attrs / tmux_fmt_attr).join_tokens
    return f"'{raw}'"


def tmux_attr_map(attrs: List[str], output: str) -> Map[str, str]:
    tokens = Lists.split(output, ' ')
    return Map(attrs.zip(tokens))


@do(TmuxIO[List[Map[str, str]]])
def simple_tmux_cmd_attrs(cmd: str, args: List[str], attrs: List[str]) -> Do:
    output = yield TmuxIO.read(cmd, '-F', tmux_fmt_attrs(attrs), *args)
    yield TmuxIO.pure(output / L(tmux_attr_map)(attrs, _))


A = TypeVar('A')


def cons_tmux_data(data: List[Map[str, str]], cons: Callable[[Map[str, str]], Either[str, A]]) -> Either[str, A]:
    return data.traverse(lambda kw: Try(cons, **kw).join, Either)


@do(TmuxIO[A])
def tmux_data_cmd(cmd: str, args: List[str], attrs: List[str], cons: Callable[[Map[str, str]], Either[str, A]]) -> Do:
    data = yield simple_tmux_cmd_attrs(cmd, args, attrs)
    yield TmuxIO.from_either(cons_tmux_data(data, cons))


__all__ = ('tmux_data_cmd',)
