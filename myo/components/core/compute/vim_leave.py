from amino import do, Do, _, Nil

from ribosome.compute.prog import Prog, bind_programs
from ribosome.compute.api import prog

from myo.config.handler import find_handlers


@prog.do
@do(Prog[None])
def vim_leave() -> Do:
    programs = yield find_handlers(_.quit)
    yield bind_programs(programs, Nil)


__all__ = ('vim_leave',)
