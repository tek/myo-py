from amino import do, Do, List, _, Nil, Just

from ribosome.nvim.scratch import show_in_scratch_buffer_default
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.prog import Prog
from ribosome.compute.ribosome_api import Ribo
from ribosome.compute.program import bind_programs

from myo.config.handler import find_handlers
from myo.data.info import InfoWidget
from myo.env import Env


@do(NS[Env, None])
def display_info(widgets: List[InfoWidget]) -> Do:
    yield NS.lift(show_in_scratch_buffer_default(widgets // _.lines, Just(.5)))


@prog.do(None)
def collect_info() -> Do:
    programs = yield find_handlers(_.info)
    yield bind_programs(programs, Nil)


@prog.do(None)
def info() -> Do:
    widgets = yield collect_info()
    yield Ribo.trivial(display_info(widgets))


__all__ = ('info',)
