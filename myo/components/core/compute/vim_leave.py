from amino import do, Do, _, Nil

from ribosome.compute.prog import Prog
from ribosome.compute.api import prog
from ribosome.compute.program import bind_programs

from myo.config.handler import find_handlers


@prog.do(None)
def vim_leave() -> Do:
    programs = yield find_handlers(_.quit)
    yield bind_programs(programs, Nil)


__all__ = ('vim_leave',)
